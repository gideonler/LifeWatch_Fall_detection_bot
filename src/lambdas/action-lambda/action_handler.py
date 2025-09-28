import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of actions that can be taken based on analysis."""
    EMERGENCY_ALERT = "emergency_alert"
    FALL_DETECTED = "fall_detected"
    UNUSUAL_ACTIVITY = "unusual_activity"
    NORMAL_ACTIVITY = "normal_activity"
    CHECK_IN_REMINDER = "check_in_reminder"
    MEDICATION_REMINDER = "medication_reminder"

@dataclass
class Action:
    """Represents an action to be taken."""
    action_type: ActionType
    priority: int  # 1-5, where 1 is highest priority
    message: str
    metadata: Dict[str, Any]
    requires_immediate_response: bool = False

class ActionHandler:
    """Handles the determination of appropriate actions based on Bedrock agent output."""
    
    def __init__(self):
        self.fall_keywords = [
            "fall", "fallen", "fell", "collapsed", "unconscious", 
            "motionless", "lying down", "on floor", "emergency"
        ]
        self.emergency_keywords = [
            "emergency", "urgent", "critical", "immediate", "help needed",
            "medical emergency", "ambulance", "911"
        ]
        self.unusual_activity_keywords = [
            "unusual", "abnormal", "concerning", "worrisome", "strange",
            "out of ordinary", "not normal"
        ]
    
    def process_bedrock_output(self, bedrock_response: Dict[str, Any]) -> List[Action]:
        """
        Process Bedrock agent output and determine appropriate actions.
        
        Args:
            bedrock_response: The response from Bedrock agent containing analysis
            
        Returns:
            List of actions to be taken
        """
        try:
            actions = []
            
            # Extract the main content from Bedrock response
            content = self._extract_content(bedrock_response)
            if not content:
                logger.warning("No content found in Bedrock response")
                return actions
            
            # Analyze the content for different scenarios
            actions.extend(self._analyze_fall_detection(content))
            actions.extend(self._analyze_emergency_situations(content))
            actions.extend(self._analyze_unusual_activity(content))
            actions.extend(self._analyze_normal_activity(content))
            
            # Sort actions by priority
            actions.sort(key=lambda x: x.priority)
            
            logger.info(f"Generated {len(actions)} actions from Bedrock output")
            return actions
            
        except Exception as e:
            logger.error(f"Error processing Bedrock output: {str(e)}")
            return [Action(
                action_type=ActionType.EMERGENCY_ALERT,
                priority=1,
                message="Error in analysis - manual check required",
                metadata={"error": str(e)},
                requires_immediate_response=True
            )]
    
    def _extract_content(self, bedrock_response: Dict[str, Any]) -> str:
        """Extract text content from Bedrock response."""
        if isinstance(bedrock_response, dict):
            # Try different possible keys for content
            for key in ['content', 'text', 'response', 'output', 'message']:
                if key in bedrock_response:
                    content = bedrock_response[key]
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, dict) and 'text' in content:
                        return content['text']
            
            # If no direct content, try to extract from nested structures
            if 'completion' in bedrock_response:
                completion = bedrock_response['completion']
                if isinstance(completion, str):
                    return completion
                elif isinstance(completion, dict) and 'text' in completion:
                    return completion['text']
        
        return str(bedrock_response)
    
    def _analyze_fall_detection(self, content: str) -> List[Action]:
        """Analyze content for fall detection scenarios."""
        actions = []
        content_lower = content.lower()
        
        # Check for fall-related keywords
        fall_indicators = [keyword for keyword in self.fall_keywords if keyword in content_lower]
        
        if fall_indicators:
            actions.append(Action(
                action_type=ActionType.FALL_DETECTED,
                priority=1,
                message=f"Fall detected: {content[:200]}...",
                metadata={
                    "indicators": fall_indicators,
                    "full_content": content
                },
                requires_immediate_response=True
            ))
        
        return actions
    
    def _analyze_emergency_situations(self, content: str) -> List[Action]:
        """Analyze content for emergency situations."""
        actions = []
        content_lower = content.lower()
        
        # Check for emergency keywords
        emergency_indicators = [keyword for keyword in self.emergency_keywords if keyword in content_lower]
        
        if emergency_indicators:
            actions.append(Action(
                action_type=ActionType.EMERGENCY_ALERT,
                priority=1,
                message=f"Emergency situation detected: {content[:200]}...",
                metadata={
                    "indicators": emergency_indicators,
                    "full_content": content
                },
                requires_immediate_response=True
            ))
        
        return actions
    
    def _analyze_unusual_activity(self, content: str) -> List[Action]:
        """Analyze content for unusual activity patterns."""
        actions = []
        content_lower = content.lower()
        
        # Check for unusual activity keywords
        unusual_indicators = [keyword for keyword in self.unusual_activity_keywords if keyword in content_lower]
        
        if unusual_indicators:
            actions.append(Action(
                action_type=ActionType.UNUSUAL_ACTIVITY,
                priority=3,
                message=f"Unusual activity detected: {content[:200]}...",
                metadata={
                    "indicators": unusual_indicators,
                    "full_content": content
                },
                requires_immediate_response=False
            ))
        
        return actions
    
    def _analyze_normal_activity(self, content: str) -> List[Action]:
        """Analyze content for normal activity patterns."""
        actions = []
        content_lower = content.lower()
        
        # Check for normal activity indicators
        normal_indicators = [
            "normal", "regular", "routine", "fine", "okay", "good", 
            "healthy", "active", "moving", "walking"
        ]
        
        normal_found = any(keyword in content_lower for keyword in normal_indicators)
        
        if normal_found:
            actions.append(Action(
                action_type=ActionType.NORMAL_ACTIVITY,
                priority=5,
                message=f"Normal activity confirmed: {content[:200]}...",
                metadata={
                    "full_content": content
                },
                requires_immediate_response=False
            ))
        
        return actions
    
    def should_send_alert(self, action: Action) -> bool:
        """Determine if an alert should be sent for this action."""
        return action.priority <= 3 or action.requires_immediate_response
    
    def should_synthesize_speech(self, action: Action) -> bool:
        """Determine if speech synthesis should be used for this action."""
        return action.priority <= 2 or action.requires_immediate_response
