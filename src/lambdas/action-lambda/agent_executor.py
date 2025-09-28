import json
import logging
import os
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime

from action_handler import Action, ActionType

logger = logging.getLogger(__name__)

class AgentExecutor:
    """Executes actions determined by the ActionHandler using AWS SNS and Amazon Polly."""
    
    def __init__(self):
        self.sns_client = boto3.client('sns')
        self.polly_client = boto3.client('polly')
        self.alerts_topic_arn = os.environ.get('ALERTS_TOPIC_ARN')
        
        if not self.alerts_topic_arn:
            logger.warning("ALERTS_TOPIC_ARN environment variable not set")
    
    def execute_actions(self, actions: List[Action]) -> Dict[str, Any]:
        """
        Execute a list of actions using SNS and Polly.
        
        Args:
            actions: List of actions to execute
            
        Returns:
            Dictionary containing execution results
        """
        results = {
            "executed_actions": [],
            "sns_notifications": [],
            "polly_synthesis": [],
            "errors": []
        }
        
        for action in actions:
            try:
                action_result = self._execute_single_action(action)
                results["executed_actions"].append(action_result)
                
                # Send SNS notification if required
                if self._should_send_sns_notification(action):
                    sns_result = self._send_sns_notification(action)
                    results["sns_notifications"].append(sns_result)
                
                # Synthesize speech if required
                if self._should_synthesize_speech(action):
                    polly_result = self._synthesize_speech(action)
                    results["polly_synthesis"].append(polly_result)
                    
            except Exception as e:
                error_msg = f"Error executing action {action.action_type.value}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append({
                    "action_type": action.action_type.value,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return results
    
    def _execute_single_action(self, action: Action) -> Dict[str, Any]:
        """Execute a single action and return the result."""
        result = {
            "action_type": action.action_type.value,
            "priority": action.priority,
            "message": action.message,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_immediate_response": action.requires_immediate_response,
            "metadata": action.metadata
        }
        
        # Add action-specific logic here
        if action.action_type == ActionType.EMERGENCY_ALERT:
            result["action_taken"] = "Emergency alert processed"
        elif action.action_type == ActionType.FALL_DETECTED:
            result["action_taken"] = "Fall detection alert processed"
        elif action.action_type == ActionType.UNUSUAL_ACTIVITY:
            result["action_taken"] = "Unusual activity alert processed"
        elif action.action_type == ActionType.NORMAL_ACTIVITY:
            result["action_taken"] = "Normal activity logged"
        else:
            result["action_taken"] = "Action processed"
        
        return result
    
    def _should_send_sns_notification(self, action: Action) -> bool:
        """Determine if SNS notification should be sent for this action."""
        return action.priority <= 3 or action.requires_immediate_response
    
    def _should_synthesize_speech(self, action: Action) -> bool:
        """Determine if speech synthesis should be used for this action."""
        return action.priority <= 2 or action.requires_immediate_response
    
    def _send_sns_notification(self, action: Action) -> Dict[str, Any]:
        """Send SNS notification for the action."""
        if not self.alerts_topic_arn:
            raise ValueError("ALERTS_TOPIC_ARN environment variable not set")
        
        # Create notification message
        subject = self._get_notification_subject(action)
        message = self._get_notification_message(action)
        
        try:
            response = self.sns_client.publish(
                TopicArn=self.alerts_topic_arn,
                Subject=subject,
                Message=message,
                MessageAttributes={
                    'Priority': {
                        'DataType': 'String',
                        'StringValue': str(action.priority)
                    },
                    'ActionType': {
                        'DataType': 'String',
                        'StringValue': action.action_type.value
                    },
                    'RequiresImmediateResponse': {
                        'DataType': 'String',
                        'StringValue': str(action.requires_immediate_response)
                    }
                }
            )
            
            return {
                "action_type": action.action_type.value,
                "message_id": response['MessageId'],
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "sent"
            }
            
        except Exception as e:
            logger.error(f"Error sending SNS notification: {str(e)}")
            raise
    
    def _synthesize_speech(self, action: Action) -> Dict[str, Any]:
        """Synthesize speech for the action using Amazon Polly."""
        try:
            # Create speech text based on action type
            speech_text = self._get_speech_text(action)
            
            # Synthesize speech
            response = self.polly_client.synthesize_speech(
                Text=speech_text,
                OutputFormat='mp3',
                VoiceId='Joanna',  # You can make this configurable
                Engine='neural'
            )
            
            # Get the audio stream
            audio_stream = response['AudioStream'].read()
            
            # In a real implementation, you might want to save this to S3
            # or stream it directly to a device
            audio_size = len(audio_stream)
            
            return {
                "action_type": action.action_type.value,
                "speech_text": speech_text,
                "audio_size_bytes": audio_size,
                "voice_id": "Joanna",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "synthesized"
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            raise
    
    def _get_notification_subject(self, action: Action) -> str:
        """Get the subject for SNS notification."""
        if action.action_type == ActionType.EMERGENCY_ALERT:
            return "🚨 EMERGENCY ALERT - Immediate Attention Required"
        elif action.action_type == ActionType.FALL_DETECTED:
            return "⚠️ FALL DETECTED - Elderly Safety Alert"
        elif action.action_type == ActionType.UNUSUAL_ACTIVITY:
            return "📊 Unusual Activity Detected"
        elif action.action_type == ActionType.NORMAL_ACTIVITY:
            return "✅ Normal Activity Confirmed"
        else:
            return "📋 Activity Update"
    
    def _get_notification_message(self, action: Action) -> str:
        """Get the message for SNS notification."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""
Action Type: {action.action_type.value.replace('_', ' ').title()}
Priority: {action.priority}/5
Timestamp: {timestamp}
Requires Immediate Response: {'Yes' if action.requires_immediate_response else 'No'}

Message: {action.message}

Metadata: {json.dumps(action.metadata, indent=2)}
        """.strip()
        
        return message
    
    def _get_speech_text(self, action: Action) -> str:
        """Get the text to be synthesized into speech."""
        if action.action_type == ActionType.EMERGENCY_ALERT:
            return "Emergency alert! Immediate attention required. Please check on the elderly person immediately."
        elif action.action_type == ActionType.FALL_DETECTED:
            return "Fall detected! The elderly person may have fallen. Please check on them immediately."
        elif action.action_type == ActionType.UNUSUAL_ACTIVITY:
            return "Unusual activity detected. Please check on the elderly person when convenient."
        elif action.action_type == ActionType.NORMAL_ACTIVITY:
            return "Normal activity confirmed. Everything appears to be fine."
        else:
            return "Activity update received. Please check the details in your notification."
    
    def get_execution_summary(self, results: Dict[str, Any]) -> str:
        """Get a summary of the execution results."""
        total_actions = len(results["executed_actions"])
        total_sns = len(results["sns_notifications"])
        total_polly = len(results["polly_synthesis"])
        total_errors = len(results["errors"])
        
        summary = f"""
Execution Summary:
- Total actions executed: {total_actions}
- SNS notifications sent: {total_sns}
- Speech synthesis completed: {total_polly}
- Errors encountered: {total_errors}
        """.strip()
        
        if total_errors > 0:
            summary += f"\n\nErrors:\n"
            for error in results["errors"]:
                summary += f"- {error['action_type']}: {error['error']}\n"
        
        return summary
