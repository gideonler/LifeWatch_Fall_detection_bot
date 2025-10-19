import boto3
import time
import json
from botocore.exceptions import ClientError
from datetime import datetime, timezone

s3 = boto3.client("s3")
polly = boto3.client("polly", region_name="ap-southeast-1")

EVENTS_BUCKET = "elderly-home-monitoring-events"
VIDEO_INVOKE_BUCKET = "elderly-home-monitoring-images"
DETECTED_PREFIX = "detected-images/"
POLLY_PREFIX = "polly-alerts/"

def get_latest_event(bucket: str = EVENTS_BUCKET, prefix: str = DETECTED_PREFIX):
    """Find the latest folder (datestr=...) and latest JSON in it."""
    try:
        # List all 'datestr=' folders
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
        folders = [p.get('Prefix') for p in response.get('CommonPrefixes', [])]
        if not folders:
            return None

        latest_folder = max(folders)
        # List all JSON files in the latest folder
        response = s3.list_objects_v2(Bucket=bucket, Prefix=latest_folder)
        json_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('_analysis.json')]
        if not json_files:
            return None

        latest_json_key = max(json_files)
        obj = s3.get_object(Bucket=bucket, Key=latest_json_key)
        event_data = json.loads(obj['Body'].read())
        return event_data

    except Exception as e:
        print(f"Error fetching latest event: {e}")
        return None


def generate_message(event_data: dict) -> str:
    """Generate a message depending on alert level."""
    level = event_data.get("alert_level", 0)
    brief = event_data.get("brief_description", "No concerning activity detected.")

    if level == 0:
        return "Hello! Everything seems fine. No immediate issues detected."
    elif level == 1:
        return f"Hi! A minor incident was detected: {brief}. Please respond if you are okay."
    elif level == 2:
        return f"Attention! A serious incident was detected: {brief}. Please stay still. Help has been informed."
    else:
        return "Hello! Unable to determine alert level, please stay safe."



def speak_to_elderly(message: str, bucket: str = EVENTS_BUCKET, output_prefix: str = POLLY_PREFIX) -> str:
    """Generate Polly MP3, save to S3, retry once if AccessDeniedException occurs."""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = polly.synthesize_speech(
                Text=message,
                OutputFormat="mp3",
                VoiceId="Joanna",
            )
            audio_data = response["AudioStream"].read()
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            audio_key = f"{output_prefix}{timestamp}.mp3"

            s3.put_object(
                Bucket=bucket,
                Key=audio_key,
                Body=audio_data,
                ContentType="audio/mpeg"
            )
            print(f"Polly audio saved to s3://{bucket}/{audio_key}")
            return audio_key

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            print(f"Polly attempt {attempt+1} failed: {code}, {e}")
            if code == "AccessDeniedException" and attempt < max_retries - 1:
                print("Waiting 5 seconds and retrying Polly call...")
                time.sleep(5)
                continue
            else:
                raise


# -------------------------
# Lambda entry point
# -------------------------
def lambda_handler(event, context):
    event_data = get_latest_event()
    if not event_data:
        return {
            "statusCode": 404,
            "body": "No recent event found."
        }

    message = generate_message(event_data)

    try:
        audio_key = speak_to_elderly(message)
        return {
            "statusCode": 200,
            "body": f"Message sent to elderly: '{message}'\nPolly audio saved to s3://{EVENTS_BUCKET}/{audio_key}"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error generating Polly audio: {str(e)}"
        }

