#!/usr/bin/env python3
"""
Example test script to demonstrate the action-lambda functionality.
This is for testing purposes and not part of the Lambda deployment.
"""

import json
from action_handler import ActionHandler, ActionType
from agent_executor import AgentExecutor

def test_fall_detection():
    """Test fall detection scenario."""
    print("Testing Fall Detection Scenario...")
    
    # Simulate Bedrock output for fall detection
    bedrock_output = {
        "content": "The person appears to have fallen and is lying motionless on the floor. This requires immediate attention.",
        "confidence": 0.95
    }
    
    action_handler = ActionHandler()
    actions = action_handler.process_bedrock_output(bedrock_output)
    
    print(f"Generated {len(actions)} actions:")
    for action in actions:
        print(f"- {action.action_type.value}: {action.message}")
        print(f"  Priority: {action.priority}, Immediate: {action.requires_immediate_response}")
    
    return actions

def test_emergency_scenario():
    """Test emergency scenario."""
    print("\nTesting Emergency Scenario...")
    
    bedrock_output = {
        "content": "Emergency situation detected! The person is unconscious and needs immediate medical attention.",
        "confidence": 0.98
    }
    
    action_handler = ActionHandler()
    actions = action_handler.process_bedrock_output(bedrock_output)
    
    print(f"Generated {len(actions)} actions:")
    for action in actions:
        print(f"- {action.action_type.value}: {action.message}")
        print(f"  Priority: {action.priority}, Immediate: {action.requires_immediate_response}")
    
    return actions

def test_normal_activity():
    """Test normal activity scenario."""
    print("\nTesting Normal Activity Scenario...")
    
    bedrock_output = {
        "content": "The person is walking normally around the room and appears to be in good health.",
        "confidence": 0.85
    }
    
    action_handler = ActionHandler()
    actions = action_handler.process_bedrock_output(bedrock_output)
    
    print(f"Generated {len(actions)} actions:")
    for action in actions:
        print(f"- {action.action_type.value}: {action.message}")
        print(f"  Priority: {action.priority}, Immediate: {action.requires_immediate_response}")
    
    return actions

def test_agent_executor():
    """Test AgentExecutor (without actual AWS calls)."""
    print("\nTesting AgentExecutor...")
    
    # Create mock actions
    from action_handler import Action
    actions = [
        Action(
            action_type=ActionType.FALL_DETECTED,
            priority=1,
            message="Test fall detection",
            metadata={"test": True},
            requires_immediate_response=True
        )
    ]
    
    # Note: This would normally require AWS credentials and environment variables
    print("AgentExecutor would execute the following actions:")
    for action in actions:
        print(f"- {action.action_type.value}: {action.message}")
        print(f"  Would send SNS: {action.priority <= 3 or action.requires_immediate_response}")
        print(f"  Would synthesize speech: {action.priority <= 2 or action.requires_immediate_response}")

if __name__ == "__main__":
    print("Action Lambda Test Examples")
    print("=" * 40)
    
    # Test different scenarios
    test_fall_detection()
    test_emergency_scenario()
    test_normal_activity()
    test_agent_executor()
    
    print("\n" + "=" * 40)
    print("Test completed! Note: AgentExecutor requires AWS credentials for full testing.")
