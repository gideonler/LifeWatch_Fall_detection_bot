import json
import logging
import os
import boto3
import base64
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class VideoInvokeHandler:
    """Handles single image processing from either inline base64 bytes or S3 URI,
       filters humans first, detects fall, and persists artifacts only when human detected."""

    def __init__(self):
        self.rekognition_client = boto3.client("rekognition")
        self.lambda_client = boto3.client("lambda")
        self.s3_client = boto3.client("s3")

        # Environment configuration
        self.agent_invoke_lambda_name = os.environ.get("AGENT_INVOKE_LAMBDA_NAME")
        self.detection_bucket = os.environ.get("DETECTION_BUCKET")

    def process_image(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process image (from base64 or S3), filter humans, and detect falls."""
        try:
            image_uri = event.get("image_uri")
            base64_image = event.get("image_base64")

            if not image_uri and not base64_image:
                raise ValueError("Must provide either image_uri or image_base64")

            image_bytes: Optional[bytes] = None
            if base64_image:
                image_bytes = base64.b64decode(base64_image)

            # Analyze image for humans
            image_analysis = self._analyze_image_for_human(image_uri, image_bytes)

            if not image_analysis.get("human_detected"):
                logger.info("No humans detected, discarding frame.")
                return {
                    "status": "discarded",
                    "reason": "no_humans",
                    "image_analysis": image_analysis,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Human detected → check fall
            fall_analysis = self._analyze_fall_patterns(image_analysis)

            # Persist logs + image only when human detected
            storage_info = self._save_detection_artifacts(
                image_bytes=image_bytes,
                image_uri=image_uri,
                image_analysis=image_analysis,
                fall_analysis=fall_analysis,
                original_event=event,
            )

            # Optional: invoke Agent Lambda
            agent_response = self._send_to_agent_invoke(
                image_analysis, fall_analysis, event, storage_info
            )

            return {
                "status": "processed" if image_analysis["human_detected"] else "discarded",
                "human_detected": image_analysis["human_detected"],
                "person_count": image_analysis["person_count"],
                "fall_detected": fall_analysis["fall_detected"],
                "safety_score": fall_analysis["safety_score"],
                "stored_logs_uri": storage_info.get("stored_logs_uri"),
                "stored_image_uri": storage_info.get("stored_image_uri"),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _analyze_image_for_human(
        self,
        image_uri: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Detect humans using Rekognition labels and faces."""
        if image_bytes is None and not image_uri:
            raise ValueError("Provide image_bytes or image_uri")

        if image_bytes is not None:
            image_param = {"Bytes": image_bytes}
            resolved_uri = image_uri or "bytes://inline"
        else:
            bucket, key = image_uri.replace("s3://", "").split("/", 1)
            image_param = {"S3Object": {"Bucket": bucket, "Name": key}}
            resolved_uri = image_uri

        labels = self.rekognition_client.detect_labels(
            Image=image_param, MaxLabels=20, MinConfidence=70
        )
        faces = self.rekognition_client.detect_faces(Image=image_param)

        # List humans with bounding boxes and confidence
        humans = []
        for face in faces.get("FaceDetails", []):
            if face.get("Confidence", 0) > 80:
                humans.append({
                    "bounding_box": face["BoundingBox"],
                    "confidence": face["Confidence"]
                })

        human_detected = len(humans) > 0 or any(
            label.get("Name", "").lower() in ["person", "people", "human"]
            and label.get("Confidence", 0) > 80
            for label in labels.get("Labels", [])
        )

        return {
            "image_uri": resolved_uri,
            "labels": labels.get("Labels", []),
            "faces": faces.get("FaceDetails", []),
            "humans": humans,
            "person_count": len(humans),
            "human_detected": human_detected,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _analyze_fall_patterns(self, image_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Detect falls for humans based on bounding box heuristics."""
        humans = image_analysis.get("humans", [])

        fall_detected = False
        for human in humans:
            bbox = human["bounding_box"]
            # Simple heuristic: bounding box height < 0.3 → possibly lying down
            if bbox["Height"] < 0.3:
                fall_detected = True
                break

        return {
            "fall_detected": fall_detected,
            "fall_confidence": 80 if fall_detected else 0,
            "safety_score": 100 if not fall_detected else 70,
            "detected_humans": humans,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _save_detection_artifacts(
        self,
        image_bytes: Optional[bytes],
        image_uri: Optional[str],
        image_analysis: Dict[str, Any],
        fall_analysis: Dict[str, Any],
        original_event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save analysis and images to S3."""
        if not self.detection_bucket:
            return {"error": "DETECTION_BUCKET not set"}

        date_str = datetime.utcnow().strftime("%Y%m%d")
        time_str = datetime.utcnow().strftime("%H%M%S")
        base_folder = f"detected-images/datestr={date_str}"

        # Save JSON log
        logs_key = f"{base_folder}/{time_str}_analysis.json"
        log_data = {
            "image_analysis": image_analysis,
            "fall_analysis": fall_analysis,
            "original_event": original_event,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.s3_client.put_object(
            Bucket=self.detection_bucket,
            Key=logs_key,
            Body=json.dumps(log_data, indent=2),
            ContentType="application/json",
        )

        # Save/copy image
        if image_bytes is not None:
            image_key = f"{base_folder}/{time_str}.jpg"
            self.s3_client.put_object(
                Bucket=self.detection_bucket,
                Key=image_key,
                Body=image_bytes,
                ContentType="image/jpeg",
            )
        else:
            src_bucket, src_key = image_uri.replace("s3://", "").split("/", 1)
            filename = os.path.basename(src_key) or f"{time_str}.jpg"
            image_key = f"{base_folder}/{filename}"
            if not (src_bucket == self.detection_bucket and src_key == image_key):
                self.s3_client.copy_object(
                    Bucket=self.detection_bucket,
                    Key=image_key,
                    CopySource={"Bucket": src_bucket, "Key": src_key},
                    MetadataDirective="REPLACE",
                    ContentType="image/jpeg",
                )

        return {
            "stored_logs_uri": f"s3://{self.detection_bucket}/{logs_key}",
            "stored_image_uri": f"s3://{self.detection_bucket}/{image_key}",
            "detection_bucket": self.detection_bucket,
        }

    def _send_to_agent_invoke(
        self,
        image_analysis: Dict[str, Any],
        fall_analysis: Dict[str, Any],
        event: Dict[str, Any],
        storage_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Invoke Agent Lambda if configured."""
        if not self.agent_invoke_lambda_name:
            return {"message": "Agent lambda not configured"}

        payload = {
            "source": "video-invoke",
            "image_analysis": image_analysis,
            "fall_analysis": fall_analysis,
            "storage_info": storage_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = self.lambda_client.invoke(
            FunctionName=self.agent_invoke_lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )

        return json.loads(response["Payload"].read())


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entrypoint for Function URL or API Gateway v2."""
    try:
        # Normalize API Gateway v2 / Lambda URL input
        if isinstance(event, dict) and "body" in event:
            body = event["body"]
            if event.get("isBase64Encoded"):
                body = base64.b64decode(body).decode("utf-8")
            if isinstance(body, str):
                try:
                    event = json.loads(body)
                except Exception:
                    event = {"raw_body": body}
            elif isinstance(body, dict):
                event = body

        logger.info(f"Received normalized event: {json.dumps(event)[:500]}")
        video_handler = VideoInvokeHandler()
        result = video_handler.process_image(event)
        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
