import json
import logging
import os
import boto3
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AgentInvokeHandler:
    """Handles combining transcribe and video outputs and invoking Bedrock agent."""
    
    def __init__(self):
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        self.ssm_client = boto3.client('ssm')
        self.s3_client = boto3.client('s3')
        
        # Get Bedrock configuration from SSM
        self.agent_id = self._get_ssm_parameter('/fall-detection/bedrock/agent-id')
        self.model_id = self._get_ssm_parameter('/fall-detection/bedrock/model-id')
        
        # S3 bucket for event storage
        self.events_bucket = os.environ.get('EVENTS_BUCKET')
        if not self.events_bucket:
            raise ValueError("EVENTS_BUCKET environment variable is required")
        
    def _get_ssm_parameter(self, parameter_name: str) -> Optional[str]:
        """Get parameter value from SSM Parameter Store."""
        try:
            response = self.ssm_client.get_parameter(Name=parameter_name)
            return response['Parameter']['Value']
        except Exception as e:
            logger.warning(f"Could not retrieve parameter {parameter_name}: {str(e)}")
            return None
    
    def process_agent_input(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transcribe and/or video inputs for a specific event_id.
        Invokes Bedrock as long as at least one input (video OR transcribe) is available.
        
        Args:
            event: Lambda event containing event_id
            
        Returns:
            Dictionary containing combined analysis and Bedrock results
        """
        try:
            # Extract event_id from event
            event_id = event.get('event_id')
            if not event_id:
                raise ValueError("event_id is required in the event")
            
            # Load transcribe and video results for this event_id
            transcribe_data, video_data = self._load_event_data(event_id)
            
            # Check if we have at least one input
            if not transcribe_data and not video_data:
                logger.warning(f"No transcribe or video data found for event {event_id}")
                return {
                    "event_id": event_id,
                    "transcribe_data": None,
                    "video_data": None,
                    "combined_analysis": {
                        "event_id": event_id,
                        "has_audio": False,
                        "has_video": False,
                        "overall_safety_score": 100,
                        "priority_level": "UNKNOWN",
                        "combined_indicators": [],
                        "note": "No input data available"
                    },
                    "bedrock_analysis": None,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "no_data"
                }
            
            # Combine the data (handles cases where only one input is available)
            combined_data = self._combine_analysis(transcribe_data, video_data, event_id)
            
            # Invoke Bedrock agent with combined data (as long as we have at least one input)
            bedrock_response = self._invoke_bedrock_agent(combined_data)
            
            # Store combined results
            results = {
                "event_id": event_id,
                "transcribe_data": transcribe_data,
                "video_data": video_data,
                "combined_analysis": combined_data,
                "bedrock_analysis": bedrock_response,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
            # Store combined results in S3
            self._store_combined_results(results, event_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing combined input: {str(e)}")
            raise
    
    def _load_event_data(self, event_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Load transcribe and video data for the given event_id."""
        transcribe_data = None
        video_data = None
        
        try:
            # Load transcribe data
            transcribe_key = f"events/transcribe/{event_id}.json"
            try:
                response = self.s3_client.get_object(Bucket=self.events_bucket, Key=transcribe_key)
                transcribe_data = json.loads(response['Body'].read().decode('utf-8'))
                logger.info(f"Loaded transcribe data for event {event_id}")
            except self.s3_client.exceptions.NoSuchKey:
                logger.warning(f"No transcribe data found for event {event_id}")
            except Exception as e:
                logger.error(f"Error loading transcribe data: {str(e)}")
            
            # Load video data
            video_key = f"events/video/{event_id}.json"
            try:
                response = self.s3_client.get_object(Bucket=self.events_bucket, Key=video_key)
                video_data = json.loads(response['Body'].read().decode('utf-8'))
                logger.info(f"Loaded video data for event {event_id}")
            except self.s3_client.exceptions.NoSuchKey:
                logger.warning(f"No video data found for event {event_id}")
            except Exception as e:
                logger.error(f"Error loading video data: {str(e)}")
            
            return transcribe_data, video_data
            
        except Exception as e:
            logger.error(f"Error loading event data: {str(e)}")
            return None, None
    
    def _combine_analysis(self, transcribe_data: Optional[Dict[str, Any]], 
                         video_data: Optional[Dict[str, Any]], 
                         event_id: str) -> Dict[str, Any]:
        """Combine transcribe and/or video analysis into a unified summary.
        Handles cases where only one input (video OR transcribe) is available."""
        
        combined = {
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "has_audio": transcribe_data is not None and transcribe_data.get('audio_present', False),
            "has_video": video_data is not None,
            "audio_analysis": {},
            "video_analysis": {},
            "combined_indicators": [],
            "overall_safety_score": 100,
            "priority_level": "LOW",
            "input_sources": []
        }
        
        # Process audio data
        if transcribe_data:
            combined["input_sources"].append("audio")
            combined["audio_analysis"] = {
                "transcription": transcribe_data.get('transcription', ''),
                "audio_present": transcribe_data.get('audio_present', False),
                "input_mode": transcribe_data.get('input_mode', 'unknown')
            }
            
            # Extract audio-based indicators
            transcription = transcribe_data.get('transcription', '').lower()
            if any(word in transcription for word in ['fall', 'fell', 'help', 'emergency']):
                combined["combined_indicators"].append("audio_emergency")
                combined["priority_level"] = "HIGH"
            elif any(word in transcription for word in ['unusual', 'strange', 'concerning']):
                combined["combined_indicators"].append("audio_unusual")
                if combined["priority_level"] == "LOW":
                    combined["priority_level"] = "MEDIUM"
        
        # Process video data
        if video_data:
            combined["input_sources"].append("video")
            analysis = video_data.get('analysis', {})
            combined["video_analysis"] = {
                "person_count": analysis.get('person_count', 0),
                "safety_score": analysis.get('safety_score', 100),
                "fall_indicators": analysis.get('fall_indicators', []),
                "movement_analysis": analysis.get('movement_analysis', []),
                "input_mode": video_data.get('input_mode', 'unknown')
            }
            
            # Extract video-based indicators
            fall_indicators = analysis.get('fall_indicators', [])
            if fall_indicators:
                combined["combined_indicators"].extend(fall_indicators)
                combined["priority_level"] = "HIGH"
            
            # Update overall safety score based on video
            video_safety = analysis.get('safety_score', 100)
            combined["overall_safety_score"] = min(combined["overall_safety_score"], video_safety)
        
        # Determine final priority level based on available inputs
        if not combined["has_audio"] and not combined["has_video"]:
            combined["priority_level"] = "UNKNOWN"
        elif combined["priority_level"] == "LOW" and combined["overall_safety_score"] < 75:
            combined["priority_level"] = "MEDIUM"
        
        # Add note about input availability
        if len(combined["input_sources"]) == 1:
            combined["note"] = f"Analysis based on {combined['input_sources'][0]} input only"
        elif len(combined["input_sources"]) == 2:
            combined["note"] = "Analysis based on both audio and video inputs"
        
        return combined
    
    def _invoke_bedrock_agent(self, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Bedrock agent with combined analysis."""
        try:
            if not self.agent_id:
                logger.warning("Bedrock agent ID not configured, returning mock response")
                return self._get_mock_bedrock_response(combined_data)
            
            # Prepare comprehensive input for Bedrock agent
            input_sources = combined_data.get('input_sources', [])
            note = combined_data.get('note', '')
            
            input_text = f"""
            Please analyze the following data for elderly safety monitoring:
            
            Event ID: {combined_data['event_id']}
            Input Sources: {', '.join(input_sources) if input_sources else 'None'}
            Note: {note}
            Overall Safety Score: {combined_data['overall_safety_score']}/100
            Priority Level: {combined_data['priority_level']}
            
            Audio Analysis:
            - Available: {combined_data['has_audio']}
            - Transcription: {combined_data['audio_analysis'].get('transcription', 'No audio available')}
            - Audio Present: {combined_data['audio_analysis'].get('audio_present', False)}
            
            Video Analysis:
            - Available: {combined_data['has_video']}
            - Person Count: {combined_data['video_analysis'].get('person_count', 0)}
            - Safety Score: {combined_data['video_analysis'].get('safety_score', 100)}/100
            - Fall Indicators: {combined_data['video_analysis'].get('fall_indicators', [])}
            - Movement Analysis: {json.dumps(combined_data['video_analysis'].get('movement_analysis', []), indent=2)}
            
            Combined Indicators: {combined_data['combined_indicators']}
            
            Focus on:
            1. Fall detection based on available evidence (audio and/or video)
            2. Emergency situations requiring immediate attention
            3. Unusual activity patterns or behaviors
            4. Normal activity confirmation
            5. Safety risk assessment considering available modalities
            
            Note: Analysis is based on {len(input_sources)} input source(s): {', '.join(input_sources) if input_sources else 'none'}.
            
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
            return self._get_mock_bedrock_response(combined_data)
    
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
    
    def _get_mock_bedrock_response(self, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock Bedrock response for testing."""
        priority = combined_data.get('priority_level', 'LOW')
        safety_score = combined_data.get('overall_safety_score', 100)
        indicators = combined_data.get('combined_indicators', [])
        
        if priority == "HIGH" or safety_score < 50 or indicators:
            analysis = "EMERGENCY: High risk situation detected. Immediate attention required."
        elif priority == "MEDIUM" or safety_score < 75:
            analysis = "WARNING: Moderate risk detected. Monitor closely."
        else:
            analysis = "NORMAL: Activity patterns appear normal. No immediate concerns."
        
        return {
            "content": f"Combined Analysis: {analysis}\nPriority: {priority}\nSafety Score: {safety_score}/100\nIndicators: {indicators}",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_analysis",
            "priority": priority
        }
    
    def _store_combined_results(self, results: Dict[str, Any], event_id: str) -> None:
        """Store combined results in S3."""
        try:
            key = f"events/combined/{event_id}.json"
            
            self.s3_client.put_object(
                Bucket=self.events_bucket,
                Key=key,
                Body=json.dumps(results, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Stored combined results: s3://{self.events_bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Error storing combined results: {str(e)}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for agent invoke processing and Bedrock analysis.
    
    Args:
        event: Lambda event containing event_id
        context: Lambda context
        
    Returns:
        Dictionary containing combined analysis and Bedrock results
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Initialize handler
        agent_handler = AgentInvokeHandler()
        
        # Process agent input
        results = agent_handler.process_agent_input(event)
        
        # Return results
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Agent invoke processing completed successfully",
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
