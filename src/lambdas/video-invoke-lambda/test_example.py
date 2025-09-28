#!/usr/bin/env python3
"""
Example test script to demonstrate the video-invoke-lambda functionality.
This is for testing purposes and not part of the Lambda deployment.
"""

import json
from datetime import datetime

def test_video_analysis():
    """Test video analysis scenario."""
    print("Testing Video Analysis Scenario...")
    
    # Simulate video analysis results
    video_analysis = {
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
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Video Analysis Results:")
    print(f"- Person Count: {video_analysis['person_count']}")
    print(f"- Safety Score: {video_analysis['safety_score']}/100")
    print(f"- Fall Indicators: {video_analysis['fall_indicators']}")
    print(f"- Movement Analysis: {len(video_analysis['movement_analysis'])} persons tracked")
    
    return video_analysis

def test_fall_detection_scenario():
    """Test fall detection scenario."""
    print("\nTesting Fall Detection Scenario...")
    
    video_analysis = {
        "person_count": 1,
        "movement_analysis": [{
            "person_id": 0,
            "bounding_box": {"Width": 0.3, "Height": 0.2, "Left": 0.3, "Top": 0.6},
            "movement": {
                "movement_type": "lying",
                "speed": "none",
                "direction": "none",
                "stability": "unstable"
            },
            "confidence": 88.2
        }],
        "fall_indicators": ["person_horizontal_position", "person_lying_down"],
        "safety_score": 30,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Fall Detection Analysis:")
    print(f"- Person Count: {video_analysis['person_count']}")
    print(f"- Safety Score: {video_analysis['safety_score']}/100")
    print(f"- Fall Indicators: {video_analysis['fall_indicators']}")
    print(f"- Movement Type: {video_analysis['movement_analysis'][0]['movement']['movement_type']}")
    
    return video_analysis

def test_emergency_scenario():
    """Test emergency scenario."""
    print("\nTesting Emergency Scenario...")
    
    video_analysis = {
        "person_count": 1,
        "movement_analysis": [{
            "person_id": 0,
            "bounding_box": {"Width": 0.15, "Height": 0.15, "Left": 0.4, "Top": 0.7},
            "movement": {
                "movement_type": "lying",
                "speed": "none",
                "direction": "none",
                "stability": "unstable"
            },
            "confidence": 92.1
        }],
        "fall_indicators": ["person_horizontal_position", "person_lying_down", "unstable_movement"],
        "safety_score": 10,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Emergency Analysis:")
    print(f"- Person Count: {video_analysis['person_count']}")
    print(f"- Safety Score: {video_analysis['safety_score']}/100")
    print(f"- Fall Indicators: {video_analysis['fall_indicators']}")
    print(f"- Risk Level: {'HIGH' if video_analysis['safety_score'] < 50 else 'MEDIUM' if video_analysis['safety_score'] < 75 else 'LOW'}")
    
    return video_analysis

def test_bedrock_integration():
    """Test Bedrock integration (mock)."""
    print("\nTesting Bedrock Integration...")
    
    # Simulate different safety scores and their corresponding Bedrock responses
    test_cases = [
        (85, "NORMAL: Video shows normal activity patterns. No immediate concerns."),
        (60, "WARNING: Moderate risk detected in video. Monitor closely."),
        (25, "EMERGENCY: High risk situation detected in video. Immediate attention required.")
    ]
    
    for safety_score, expected_analysis in test_cases:
        print(f"\nSafety Score: {safety_score}/100")
        print(f"Expected Analysis: {expected_analysis}")
        
        # Determine priority based on safety score
        if safety_score < 50:
            priority = "HIGH"
        elif safety_score < 75:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        print(f"Priority Level: {priority}")

if __name__ == "__main__":
    print("Video Invoke Lambda Test Examples")
    print("=" * 50)
    
    # Test different scenarios
    test_video_analysis()
    test_fall_detection_scenario()
    test_emergency_scenario()
    test_bedrock_integration()
    
    print("\n" + "=" * 50)
    print("Test completed! Note: Full testing requires AWS credentials and Rekognition setup.")
