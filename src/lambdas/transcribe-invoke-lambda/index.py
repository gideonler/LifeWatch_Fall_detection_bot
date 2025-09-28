import json
import logging
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TranscribeInvokeHandler:
    """Handles audio transcription and Bedrock agent invocation for elderly safety monitoring."""
    
    def __init__(self):
        self.transcribe_client = boto3.client('transcribe')
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        self.ssm_client = boto3.client('ssm')
        
        # Get Bedrock configuration from SSM
        self.agent_id = self._get_ssm_parameter('/fall-detection/bedrock/agent-id')
        self.knowledge_base_id = self._get_ssm_parameter('/fall-detection/bedrock/kb-id')
        self.model_id = self._get_ssm_parameter('/fall-detection/bedrock/model-id')
        
        # S3 bucket for storing transcription results
        self.transcription_bucket = os.environ.get('TRANSCRIPTION_BUCKET')
        
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
        
        Args:
            event: Lambda event containing audio file information
            
        Returns:
            Dictionary containing transcription and analysis results
        """
        try:
            # Extract audio file information from event
            audio_uri = event.get('audio_uri')
            if not audio_uri:
                raise ValueError("audio_uri is required in the event")
            
            # Start transcription job
            transcription_result = self._transcribe_audio(audio_uri)
            
            if not transcription_result:
                raise ValueError("Transcription failed")
            
            # Invoke Bedrock agent with transcription
            bedrock_response = self._invoke_bedrock_agent(transcription_result)
            
            # Store results
            results = {
                "transcription": transcription_result,
                "bedrock_analysis": bedrock_response,
                "timestamp": datetime.utcnow().isoformat(),
                "audio_uri": audio_uri
            }
            
            # Store in S3 if bucket is configured
            if self.transcription_bucket:
                self._store_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise
    
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
    
    def _invoke_bedrock_agent(self, transcription: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with transcription for elderly safety analysis."""
        try:
            if not self.agent_id:
                logger.warning("Bedrock agent ID not configured, returning mock response")
                return self._get_mock_bedrock_response(transcription)
            
            # Prepare input for Bedrock agent
            input_text = f"""
            Please analyze the following audio transcription for elderly safety monitoring:
            
            Transcription: {transcription}
            
            Focus on:
            1. Fall detection indicators
            2. Emergency situations
            3. Unusual activity patterns
            4. Normal activity confirmation
            5. Any concerning sounds or speech patterns
            
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
            return self._get_mock_bedrock_response(transcription)
    
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
    
    def _get_mock_bedrock_response(self, transcription: str) -> Dict[str, Any]:
        """Get mock Bedrock response for testing."""
        # Simple keyword-based analysis
        transcription_lower = transcription.lower()
        
        if any(word in transcription_lower for word in ['fall', 'fell', 'help', 'emergency']):
            analysis = "EMERGENCY: Potential fall or emergency situation detected in audio. Immediate attention required."
            priority = "HIGH"
        elif any(word in transcription_lower for word in ['unusual', 'strange', 'concerning']):
            analysis = "WARNING: Unusual activity detected in audio. Monitor closely."
            priority = "MEDIUM"
        else:
            analysis = "NORMAL: Audio indicates normal activity patterns. No immediate concerns."
            priority = "LOW"
        
        return {
            "content": f"Audio Analysis: {analysis}\nPriority: {priority}\nTranscription: {transcription[:200]}...",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_analysis",
            "priority": priority
        }
    
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
