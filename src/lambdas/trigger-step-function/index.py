import json
import os
import boto3
import base64
from datetime import datetime

stepfunctions = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

def handler(event, context):
    try:
        # Log event
        print("Event keys:", list(event.keys()))
        
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

        image_base64 = event.get("image_base64")
        if image_base64:
            print('got image success')

        print(f"Got image_base64 with {len(image_base64)} characters")
        
        # Create the payload for the Step Function
        step_function_input = {
            "image_base64": image_base64,
            "metadata": event.get("metadata", {}),
            "transcript": event.get("transcript", ""),
            "source": "step-function-trigger"
        }
        
        # Check the size of the input
        input_size = len(json.dumps(step_function_input))
        if input_size > 262144:  # 256 KB limit
            raise ValueError(f"Input size {input_size} exceeds the 256 KB limit.")

        # Start Step Function execution with JSON string
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"run-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}",
            input=json.dumps(step_function_input)  # Must be JSON string!
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Step Function started",
                "executionArn": response["executionArn"]
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}