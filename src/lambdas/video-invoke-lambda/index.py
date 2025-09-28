import json
import logging
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class VideoInvokeHandler:
    """Handles visual processing and Bedrock agent invocation for elderly safety monitoring.

    Supports two input modes:
    1) video_uri: S3 URI to a video (legacy path using Rekognition Video person tracking)
    2) image_grid_base64 or image_grid_s3_uri: a grid image of 10 frames from Streamlit
       - We run Rekognition DetectLabels on the grid image to detect a human
       - If a human is detected, we store the grid in S3 and invoke the Bedrock agent
    """
    
    def __init__(self):
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        self.ssm_client = boto3.client('ssm')
        self.rekognition_client = boto3.client('rekognition')
        
        # Get Bedrock configuration from SSM
        self.agent_id = self._get_ssm_parameter('/fall-detection/bedrock/agent-id')
        self.model_id = self._get_ssm_parameter('/fall-detection/bedrock/model-id')

        # commenting out knowledge base id for now
        # self.knowledge_base_id = self._get_ssm_parameter('/fall-detection/bedrock/kb-id')
        
        # S3 bucket for storing video analysis results
        self.video_analysis_bucket = os.environ.get('VIDEO_ANALYSIS_BUCKET')
        
    def _get_ssm_parameter(self, parameter_name: str) -> Optional[str]:
        """Get parameter value from SSM Parameter Store."""
        try:
            response = self.ssm_client.get_parameter(Name=parameter_name)
            return response['Parameter']['Value']
        except Exception as e:
            logger.warning(f"Could not retrieve parameter {parameter_name}: {str(e)}")
            return None
    
    def process_video(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route processing based on input: video or frames grid image.

        Event contracts supported:
        - { "video_uri": "s3://bucket/key.mp4", "metadata": {...} }
        - { "image_grid_base64": "<base64>", "metadata": {...} }
        - { "image_grid_s3_uri": "s3://bucket/key.jpg", "metadata": {...} }
        """
        try:
            if event.get('image_grid_base64') or event.get('image_grid_s3_uri'):
                return self._process_frames_grid(event)
            
            # Legacy path: video uri provided
            video_uri = event.get('video_uri')
            if not video_uri:
                raise ValueError("video_uri or image_grid_{base64|s3_uri} is required in the event")

            video_analysis = self._analyze_video(video_uri)
            bedrock_response = self._invoke_bedrock_agent(video_analysis, context_uri=video_uri)

            results = {
                "analysis": video_analysis,
                "bedrock_analysis": bedrock_response,
                "timestamp": datetime.utcnow().isoformat(),
                "context_uri": video_uri,
                "input_mode": "video"
            }

            if self.video_analysis_bucket:
                self._store_results(results)

            return results
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise
    
    def _analyze_video(self, video_uri: str) -> Dict[str, Any]:
        """Analyze video using Amazon Rekognition for elderly safety monitoring."""
        try:
            # Start video analysis job
            job_id = self._start_video_analysis(video_uri)
            
            if not job_id:
                logger.warning("Video analysis job failed to start, using mock analysis")
                return self._get_mock_video_analysis()
            
            # Wait for completion and get results
            analysis_results = self._get_video_analysis_results(job_id)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return self._get_mock_video_analysis()
    
    def _start_video_analysis(self, video_uri: str) -> Optional[str]:
        """Start Amazon Rekognition video analysis job."""
        try:
            # Extract S3 bucket and key from URI
            s3_uri_parts = video_uri.replace('s3://', '').split('/', 1)
            bucket = s3_uri_parts[0]
            key = s3_uri_parts[1]
            
            # Start person tracking job
            response = self.rekognition_client.start_person_tracking(
                Video={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                NotificationChannel={
                    'SNSTopicArn': os.environ.get('REKOGNITION_SNS_TOPIC', ''),
                    'RoleArn': os.environ.get('REKOGNITION_ROLE_ARN', '')
                }
            )
            
            job_id = response['JobId']
            logger.info(f"Started video analysis job: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error starting video analysis: {str(e)}")
            return None
    
    def _get_video_analysis_results(self, job_id: str) -> Dict[str, Any]:
        """Get results from video analysis job."""
        try:
            import time
            
            # Wait for job completion
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                response = self.rekognition_client.get_person_tracking(JobId=job_id)
                
                status = response['JobStatus']
                if status in ['SUCCEEDED', 'FAILED']:
                    break
                    
                time.sleep(10)  # Wait 10 seconds before checking again
            
            if status == 'SUCCEEDED':
                return self._parse_video_analysis_results(response)
            else:
                logger.error(f"Video analysis job failed: {response.get('StatusMessage', 'Unknown error')}")
                return self._get_mock_video_analysis()
                
        except Exception as e:
            logger.error(f"Error getting video analysis results: {str(e)}")
            return self._get_mock_video_analysis()
    
    def _parse_video_analysis_results(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse video analysis results from Rekognition."""
        try:
            persons = response.get('Persons', [])
            
            # Analyze person movements and positions
            analysis = {
                "person_count": len(persons),
                "movement_analysis": [],
                "fall_indicators": [],
                "safety_score": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for person in persons:
                person_data = person.get('Person', {})
                if person_data:
                    # Analyze bounding box and movement
                    bounding_box = person_data.get('BoundingBox', {})
                    movement = self._analyze_person_movement(person)
                    
                    analysis["movement_analysis"].append({
                        "person_id": person_data.get('Index', 0),
                        "bounding_box": bounding_box,
                        "movement": movement,
                        "confidence": person_data.get('Confidence', 0)
                    })
                    
                    # Check for fall indicators
                    fall_indicators = self._check_fall_indicators(bounding_box, movement)
                    if fall_indicators:
                        analysis["fall_indicators"].extend(fall_indicators)
            
            # Calculate safety score
            analysis["safety_score"] = self._calculate_safety_score(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing video analysis results: {str(e)}")
            return self._get_mock_video_analysis()
    
    def _analyze_person_movement(self, person: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze person movement patterns."""
        # This is a simplified implementation
        # In a real scenario, you'd analyze the track over time
        return {
            "movement_type": "walking",  # walking, standing, sitting, lying
            "speed": "normal",
            "direction": "forward",
            "stability": "stable"
        }
    
    def _check_fall_indicators(self, bounding_box: Dict[str, Any], movement: Dict[str, Any]) -> list:
        """Check for fall indicators in person data."""
        indicators = []
        
        # Check bounding box position (person lying down)
        if bounding_box.get('Height', 0) < 0.3:  # Person appears horizontal
            indicators.append("person_horizontal_position")
        
        # Check movement patterns
        if movement.get('movement_type') == 'lying':
            indicators.append("person_lying_down")
        
        if movement.get('stability') == 'unstable':
            indicators.append("unstable_movement")
        
        return indicators
    
    def _calculate_safety_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate safety score based on analysis (0-100, higher is safer)."""
        score = 100
        
        # Deduct points for fall indicators
        score -= len(analysis.get('fall_indicators', [])) * 20
        
        # Deduct points for unusual movement
        for movement in analysis.get('movement_analysis', []):
            if movement.get('movement', {}).get('stability') == 'unstable':
                score -= 10
        
        return max(0, min(100, score))
    
    def _get_mock_video_analysis(self) -> Dict[str, Any]:
        """Get mock video analysis for testing."""
        return {
            "person_count": 1,
            "movement_analysis": [{
                "person_id": 0,
                "bounding_box": {"Width": 0.2, "Height": 0.6, "Left": 0.4, "Top": 0.2},
                "movement": {
                    "movement_type": "walking",
                    "speed": "normal",
                    "direction": "forward",
                    "stability": "stable"
                },
                "confidence": 95.5
            }],
            "fall_indicators": [],
            "safety_score": 85,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_analysis"
        }
    
    def _invoke_bedrock_agent(self, video_analysis: Dict[str, Any], context_uri: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with analysis summary and a context URI (video or image)."""
        try:
            if not self.agent_id:
                logger.warning("Bedrock agent ID not configured, returning mock response")
                return self._get_mock_bedrock_response(video_analysis)
            
            # Prepare input for Bedrock agent
            input_text = f"""
            Please analyze the following visual analysis for elderly safety monitoring:
            
            Analysis Summary:
            - Person Count: {video_analysis.get('person_count', 0)}
            - Safety Score: {video_analysis.get('safety_score', 0)}/100
            - Fall Indicators: {video_analysis.get('fall_indicators', [])}
            - Movement Analysis: {json.dumps(video_analysis.get('movement_analysis', []), indent=2)}
            
            Context URI: {context_uri}
            
            Focus on:
            1. Fall detection based on person positioning and movement
            2. Emergency situations requiring immediate attention
            3. Unusual activity patterns or behaviors
            4. Normal activity confirmation
            5. Safety risk assessment
            
            Provide a detailed analysis with priority level and recommended actions.
            """
            
            # Invoke Bedrock agent
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                sessionId=f"session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                inputText=input_text
            )
            
            # Parse response
            bedrock_response = self._parse_bedrock_response(response)
            return bedrock_response
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock agent: {str(e)}")
            return self._get_mock_bedrock_response(video_analysis)
    
    def _parse_bedrock_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Bedrock agent response."""
        try:
            # Read the response stream
            response_body = response['completion']
            content = ""
            
            for event in response_body:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        content += chunk['bytes'].decode('utf-8')
            
            return {
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "bedrock_agent"
            }
            
        except Exception as e:
            logger.error(f"Error parsing Bedrock response: {str(e)}")
            return {"content": "Error parsing Bedrock response", "error": str(e)}
    
    def _get_mock_bedrock_response(self, video_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock Bedrock response for testing."""
        safety_score = video_analysis.get('safety_score', 0)
        fall_indicators = video_analysis.get('fall_indicators', [])
        
        if safety_score < 50 or fall_indicators:
            analysis = "EMERGENCY: High risk situation detected in video. Immediate attention required."
            priority = "HIGH"
        elif safety_score < 75:
            analysis = "WARNING: Moderate risk detected in video. Monitor closely."
            priority = "MEDIUM"
        else:
            analysis = "NORMAL: Video shows normal activity patterns. No immediate concerns."
            priority = "LOW"
        
        return {
            "content": f"Video Analysis: {analysis}\nPriority: {priority}\nSafety Score: {safety_score}/100",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_analysis",
            "priority": priority
        }
    
    def _store_results(self, results: Dict[str, Any]) -> None:
        """Store results in S3 bucket."""
        try:
            s3_client = boto3.client('s3')
            key = f"video-analysis/{datetime.utcnow().strftime('%Y/%m/%d')}/analysis-{datetime.utcnow().strftime('%H%M%S')}.json"
            
            s3_client.put_object(
                Bucket=self.video_analysis_bucket,
                Key=key,
                Body=json.dumps(results, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Stored video analysis results in S3: s3://{self.video_analysis_bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Error storing results in S3: {str(e)}")

    # --------- New image-grid pipeline ---------
    def _process_frames_grid(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a grid image of frames from Streamlit.

        If a person is detected by Rekognition, persist the grid to S3 and invoke the Bedrock agent.
        """
        image_bytes: Optional[bytes] = None
        grid_s3_uri: Optional[str] = event.get('image_grid_s3_uri')

        if event.get('image_grid_base64'):
            import base64
            image_bytes = base64.b64decode(event['image_grid_base64'])
        elif grid_s3_uri:
            # We will not download; Rekognition can read from S3 directly
            pass
        else:
            raise ValueError("image_grid_base64 or image_grid_s3_uri must be provided")

        # Detect person using Rekognition DetectLabels
        person_detected, labels = self._detect_person_in_image(image_bytes=image_bytes, s3_uri=grid_s3_uri)

        analysis = {
            "person_count": 1 if person_detected else 0,
            "movement_analysis": [],
            "fall_indicators": [],
            "safety_score": 80 if person_detected else 90,
            "labels": labels,
            "timestamp": datetime.utcnow().isoformat()
        }

        if not person_detected:
            return {
                "analysis": analysis,
                "bedrock_analysis": self._get_mock_bedrock_response(analysis),
                "context_uri": grid_s3_uri or "inline-bytes",
                "input_mode": "image_grid",
                "note": "No person detected; skipping Bedrock invocation"
            }

        # Ensure image grid is stored to S3 for traceability
        if not grid_s3_uri:
            grid_s3_uri = self._upload_bytes_to_s3(image_bytes)

        bedrock_response = self._invoke_bedrock_agent(analysis, context_uri=grid_s3_uri)

        results = {
            "analysis": analysis,
            "bedrock_analysis": bedrock_response,
            "timestamp": datetime.utcnow().isoformat(),
            "context_uri": grid_s3_uri,
            "input_mode": "image_grid"
        }

        if self.video_analysis_bucket:
            self._store_results(results)

        return results

    def _detect_person_in_image(self, *, image_bytes: Optional[bytes] = None, s3_uri: Optional[str] = None):
        """Use Rekognition DetectLabels to check for a 'Person' label in an image."""
        try:
            params: Dict[str, Any] = {"MaxLabels": 10, "MinConfidence": 70}
            if image_bytes is not None:
                params["Image"] = {"Bytes": image_bytes}
            elif s3_uri:
                bucket, key = s3_uri.replace('s3://', '').split('/', 1)
                params["Image"] = {"S3Object": {"Bucket": bucket, "Name": key}}
            else:
                raise ValueError("Either image_bytes or s3_uri must be provided")

            resp = self.rekognition_client.detect_labels(**params)
            labels = [{"Name": l["Name"], "Confidence": l["Confidence"]} for l in resp.get("Labels", [])]
            person_detected = any(l["Name"].lower() == "person" and l["Confidence"] >= 70 for l in resp.get("Labels", []))
            return person_detected, labels
        except Exception as e:
            logger.error(f"Error detecting labels: {str(e)}")
            # Fail open but indicate no person to avoid false alarms
            return False, []

    def _upload_bytes_to_s3(self, image_bytes: bytes) -> str:
        """Upload image bytes to the analysis bucket and return the S3 URI."""
        if not self.video_analysis_bucket:
            raise ValueError("VIDEO_ANALYSIS_BUCKET is not configured")
        s3_client = boto3.client('s3')
        key = f"frames-grid/{datetime.utcnow().strftime('%Y/%m/%d')}/grid-{datetime.utcnow().strftime('%H%M%S')}.jpg"
        s3_client.put_object(Bucket=self.video_analysis_bucket, Key=key, Body=image_bytes, ContentType='image/jpeg')
        return f"s3://{self.video_analysis_bucket}/{key}"

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for video processing and Bedrock analysis.
    
    Args:
        event: Lambda event containing video file information
        context: Lambda context
        
    Returns:
        Dictionary containing video analysis and Bedrock results
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Initialize handler
        video_handler = VideoInvokeHandler()
        
        # Process video
        results = video_handler.process_video(event)
        
        # Return results
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Video processing completed successfully",
                "results": results
            })
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }
