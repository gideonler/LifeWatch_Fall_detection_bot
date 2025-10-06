import json
import logging
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TranscribeInvokeHandler(Construct):
    """Handles audio transcription and Bedrock agent invocation for elderly safety monitoring."""
    
    def __init__(self):
        self.transcribe_client = boto3.client('transcribe')
        self.ssm_client = boto3.client('ssm')
        
        # Get Bedrock configuration from SSM
        self.agent_id = self._get_ssm_parameter('/fall-detection/bedrock/agent-id')
        self.model_id = self._get_ssm_parameter('/fall-detection/bedrock/model-id')

        # commenting out knowledge base id for now
        # self.knowledge_base_id = self._get_ssm_parameter('/fall-detection/bedrock/kb-id')

        
        # Buckets and pipeline mode
        self.transcription_bucket = os.environ.get('TRANSCRIPTION_BUCKET')
        self.events_bucket = os.environ.get('EVENTS_BUCKET')
        self.combined_pipeline = os.environ.get('COMBINED_PIPELINE', 'false').lower() == 'true'
        
    def _get_ssm_parameter(self, parameter_name: str) -> Optional[str]:
        """Get parameter value from SSM Parameter Store."""
        try:
            response = self.ssm_client.get_parameter(Name=parameter_name)
            return response['Parameter']['Value']
        except Exception as e:
            logger.warning(f"Could not retrieve parameter {parameter_name}: {str(e)}")
            return None
    
    def process_audio(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio file and invoke Bedrock agent for analysis.
        
        Supports two input modes:
        1) audio_uri: S3 URI to audio file (legacy)
        2) audio_base64: base64-encoded audio data directly from Streamlit
        
        Args:
            event: Lambda event containing audio file information
            
        Returns:
            Dictionary containing transcription and analysis results
        """
        try:
            # Check for direct audio input first
            if event.get('audio_base64'):
                return self._process_direct_audio(event)
            
            # Legacy path: S3 URI
            audio_uri = event.get('audio_uri')
            if not audio_uri:
                raise ValueError("audio_uri or audio_base64 is required in the event")
            
            # Start transcription job
            transcription_result = self._transcribe_audio(audio_uri)
            
            if not transcription_result:
                raise ValueError("Transcription failed")
            
            # Determine event_id
            event_id = event.get('event_id') or self._compute_event_id()
            bedrock_response = None  # Bedrock invocation disabled for this function
            
            # Store results
            results = {
                "transcription": transcription_result,
                "bedrock_analysis": bedrock_response,
                "timestamp": datetime.utcnow().isoformat(),
                "audio_uri": audio_uri,
                "input_mode": "s3_uri",
                "event_id": event_id,
                "audio_present": bool(transcription_result)
            }
            
            # Store in events bucket if configured
            if self.events_bucket:
                self._store_event_results(results, key=f"transcribe/{event_id}.json")
            elif self.transcription_bucket:
                self._store_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise

    def _compute_event_id(self) -> str:
        import math
        now = datetime.utcnow()
        epoch = int(now.timestamp())
        window = (epoch // 30) * 30
        return datetime.utcfromtimestamp(window).strftime('%Y%m%dT%H%M%SZ')
    
    def _transcribe_audio(self, audio_uri: str) -> Optional[str]:
        """Transcribe audio file using Amazon Transcribe."""
        try:
            # Extract job name from audio URI
            job_name = f"transcribe-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Start transcription job
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_uri},
                MediaFormat='wav',  # Adjust based on your audio format
                LanguageCode='en-US',
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 2,  # Adjust based on expected speakers
                    'ChannelIdentification': False
                }
            )
            
            job_name = response['TranscriptionJob']['TranscriptionJobName']
            logger.info(f"Started transcription job: {job_name}")
            
            # Wait for completion
            self._wait_for_transcription_completion(job_name)
            
            # Get transcription results
            response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            if response['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                # Download and parse transcription file
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                return self._download_transcript(transcript_uri)
            else:
                logger.error(f"Transcription job failed: {response['TranscriptionJob']['FailureReason']}")
                return None
                
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            return None
    
    def _wait_for_transcription_completion(self, job_name: str, max_wait_time: int = 300) -> None:
        """Wait for transcription job to complete."""
        import time
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            if status in ['COMPLETED', 'FAILED']:
                break
                
            time.sleep(10)  # Wait 10 seconds before checking again
    
    def _download_transcript(self, transcript_uri: str) -> str:
        """Download and parse transcript from S3."""
        import urllib.request
        import json
        
        # Download transcript file
        with urllib.request.urlopen(transcript_uri) as response:
            transcript_data = json.loads(response.read().decode())
        
        # Extract transcript text
        transcript_text = transcript_data['results']['transcripts'][0]['transcript']
        
        # Add speaker information if available
        if 'speaker_labels' in transcript_data['results']:
            speaker_segments = transcript_data['results']['speaker_labels']['segments']
            transcript_text = self._format_with_speakers(transcript_text, speaker_segments)
        
        return transcript_text
    
    def _format_with_speakers(self, transcript: str, speaker_segments: list) -> str:
        """Format transcript with speaker labels."""
        # This is a simplified implementation
        # In a real scenario, you'd want to properly align speaker segments with transcript
        formatted_transcript = f"Audio Transcript:\n{transcript}\n\n"
        formatted_transcript += "Speaker Analysis: Multiple speakers detected in audio stream."
        return formatted_transcript

    def _process_direct_audio(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Accept base64 audio, stage to S3, run Transcribe, and emit event-scoped results."""
        import base64
        s3_client = boto3.client('s3')
        if not self.transcription_bucket and not self.events_bucket:
            raise ValueError("Either TRANSCRIPTION_BUCKET or EVENTS_BUCKET must be configured to stage audio")

        audio_b64 = event['audio_base64']
        audio_bytes = base64.b64decode(audio_b64)
        bucket = self.transcription_bucket or self.events_bucket
        key = f"audio-inline/{datetime.utcnow().strftime('%Y/%m/%d')}/audio-{datetime.utcnow().strftime('%H%M%S')}.wav"
        s3_client.put_object(Bucket=bucket, Key=key, Body=audio_bytes, ContentType='audio/wav')
        audio_uri = f"s3://{bucket}/{key}"

        transcription_result = self._transcribe_audio(audio_uri)
        event_id = event.get('event_id') or self._compute_event_id()

        bedrock_response = None  # Bedrock invocation disabled for this function

        results = {
            "transcription": transcription_result,
            "bedrock_analysis": bedrock_response,
            "timestamp": datetime.utcnow().isoformat(),
            "audio_uri": audio_uri,
            "input_mode": "base64",
            "event_id": event_id,
            "audio_present": bool(transcription_result)
        }

        if self.events_bucket:
            self._store_event_results(results, key=f"transcribe/{event_id}.json")
        else:
            self._store_results(results)

        return results
    
    # Bedrock invocation intentionally omitted in this lambda
    
    def _store_results(self, results: Dict[str, Any]) -> None:
        """Store results in S3 bucket."""
        try:
            s3_client = boto3.client('s3')
            key = f"transcriptions/{datetime.utcnow().strftime('%Y/%m/%d')}/transcription-{datetime.utcnow().strftime('%H%M%S')}.json"
            
            s3_client.put_object(
                Bucket=self.transcription_bucket,
                Key=key,
                Body=json.dumps(results, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Stored transcription results in S3: s3://{self.transcription_bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Error storing results in S3: {str(e)}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for audio transcription and Bedrock analysis.
    
    Args:
        event: Lambda event containing audio file information
        context: Lambda context
        
    Returns:
        Dictionary containing transcription and analysis results
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Initialize handler
        transcribe_handler = TranscribeInvokeHandler()
        
        # Process audio
        results = transcribe_handler.process_audio(event)
        
        # Return results
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Audio processing completed successfully",
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
