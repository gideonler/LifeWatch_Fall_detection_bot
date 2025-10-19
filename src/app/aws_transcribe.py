import boto3
import os 
import uuid
from botocore.config import Config
import time 
import requests

TIMEOUT_SECONDS = 60
AWS_REGION = "ap-southeast-1"
transcribe_client = boto3.client("transcribe", region_name=AWS_REGION, config=Config(connect_timeout=TIMEOUT_SECONDS))

S3_BUCKET = 'elderly-home-monitoring-audio'
# ============== AWS TRANSCRIBE ======================
def transcribe_audio(file_path, bucket_name=S3_BUCKET):
    """Send recorded WAV audio to AWS Transcribe and return transcript text."""
    job_name = f"transcribe_{uuid.uuid4().hex}"
   
    object_name = f"audio/{os.path.basename(file_path)}"
    s3 = boto3.client("s3", region_name=AWS_REGION)

    try:
        print("🧠 Uploading audio for transcription...")
        s3.upload_file(file_path, bucket_name, object_name)
        audio_uri = f"s3://{bucket_name}/{object_name}"
        print(f'Successful upload to {audio_uri}')
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": audio_uri},
            MediaFormat="wav",
            LanguageCode="en-US",
        )

        # Poll for completion
        while True:
            status = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            state = status["TranscriptionJob"]["TranscriptionJobStatus"]
            if state in ["COMPLETED", "FAILED"]:
                break
            print("⏳ Waiting for transcription to finish...")
            time.sleep(5)

        if state == "COMPLETED":
            transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            transcript_data = requests.get(transcript_uri).json()
            text = transcript_data["results"]["transcripts"][0]["transcript"]
            print(f"🗣️ Transcript: {text}")
            return text
        else:
            print("❌ Transcription failed.")
            return ""

    except Exception as e:
        print(f"⚠️ Transcribe error: {e}")
        return ""
# ===================================================
