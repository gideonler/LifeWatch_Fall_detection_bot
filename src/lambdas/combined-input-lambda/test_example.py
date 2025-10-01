#!/usr/bin/env python3
"""
Example test script to demonstrate the combined-input-lambda functionality.
This is for testing purposes and not part of the Lambda deployment.
"""

import json
from datetime import datetime

def test_combined_analysis():
    """Test combined analysis scenario."""
    print("Testing Combined Analysis Scenario...")
    
    # Simulate transcribe data
    transcribe_data = {
        "transcription": "I'm walking around the room normally today.",
        "audio_present": True,
        "input_mode": "s3_uri",
        "event_id": "20240101T120000Z",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Simulate video data
    video_data = {
        "analysis": {
            "person_count": 1,
            "safety_score": 85,
            "fall_indicators": [],
            "movement_analysis": [{
                "person_id": 0,
                "movement": {
                    "movement_type": "walking",
                    "stability": "stable"
                },
                "confidence": 95.5
            }]
        },
        "input_mode": "image_grid",
        "event_id": "20240101T120000Z",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Transcribe Data:")
    print(f"- Transcription: {transcribe_data['transcription']}")
    print(f"- Audio Present: {transcribe_data['audio_present']}")
    
    print("\nVideo Data:")
    print(f"- Person Count: {video_data['analysis']['person_count']}")
    print(f"- Safety Score: {video_data['analysis']['safety_score']}/100")
    print(f"- Fall Indicators: {video_data['analysis']['fall_indicators']}")
    
    # Simulate combined analysis
    combined_analysis = {
        "event_id": "20240101T120000Z",
        "has_audio": True,
        "has_video": True,
        "overall_safety_score": 85,
        "priority_level": "LOW",
        "combined_indicators": []
    }
    
    print("\nCombined Analysis:")
    print(f"- Has Audio: {combined_analysis['has_audio']}")
    print(f"- Has Video: {combined_analysis['has_video']}")
    print(f"- Overall Safety Score: {combined_analysis['overall_safety_score']}/100")
    print(f"- Priority Level: {combined_analysis['priority_level']}")
    
    return combined_analysis

def test_emergency_scenario():
    """Test emergency scenario with combined data."""
    print("\nTesting Emergency Scenario...")
    
    # Simulate emergency transcribe data
    transcribe_data = {
        "transcription": "Help! I fell down and can't get up!",
        "audio_present": True,
        "input_mode": "base64",
        "event_id": "20240101T120030Z",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Simulate emergency video data
    video_data = {
        "analysis": {
            "person_count": 1,
            "safety_score": 20,
            "fall_indicators": ["person_horizontal_position", "person_lying_down"],
            "movement_analysis": [{
                "person_id": 0,
                "movement": {
                    "movement_type": "lying",
                    "stability": "unstable"
                },
                "confidence": 88.2
            }]
        },
        "input_mode": "image_grid",
        "event_id": "20240101T120030Z",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Emergency Transcribe Data:")
    print(f"- Transcription: {transcribe_data['transcription']}")
    print(f"- Audio Present: {transcribe_data['audio_present']}")
    
    print("\nEmergency Video Data:")
    print(f"- Person Count: {video_data['analysis']['person_count']}")
    print(f"- Safety Score: {video_data['analysis']['safety_score']}/100")
    print(f"- Fall Indicators: {video_data['analysis']['fall_indicators']}")
    
    # Simulate combined emergency analysis
    combined_analysis = {
        "event_id": "20240101T120030Z",
        "has_audio": True,
        "has_video": True,
        "overall_safety_score": 20,
        "priority_level": "HIGH",
        "combined_indicators": ["audio_emergency", "person_horizontal_position", "person_lying_down"]
    }
    
    print("\nCombined Emergency Analysis:")
    print(f"- Has Audio: {combined_analysis['has_audio']}")
    print(f"- Has Video: {combined_analysis['has_video']}")
    print(f"- Overall Safety Score: {combined_analysis['overall_safety_score']}/100")
    print(f"- Priority Level: {combined_analysis['priority_level']}")
    print(f"- Combined Indicators: {combined_analysis['combined_indicators']}")
    
    return combined_analysis

def test_missing_data_scenario():
    """Test scenario with missing transcribe or video data."""
    print("\nTesting Missing Data Scenario...")
    
    # Only video data available
    video_data = {
        "analysis": {
            "person_count": 1,
            "safety_score": 90,
            "fall_indicators": [],
            "movement_analysis": [{
                "person_id": 0,
                "movement": {
                    "movement_type": "standing",
                    "stability": "stable"
                },
                "confidence": 92.1
            }]
        },
        "input_mode": "video",
        "event_id": "20240101T120100Z",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Video Only Data:")
    print(f"- Person Count: {video_data['analysis']['person_count']}")
    print(f"- Safety Score: {video_data['analysis']['safety_score']}/100")
    print(f"- Fall Indicators: {video_data['analysis']['fall_indicators']}")
    
    # Simulate combined analysis with missing audio
    combined_analysis = {
        "event_id": "20240101T120100Z",
        "has_audio": False,
        "has_video": True,
        "overall_safety_score": 90,
        "priority_level": "LOW",
        "combined_indicators": [],
        "input_sources": ["video"],
        "note": "Analysis based on video input only"
    }
    
    print("\nCombined Analysis (Video Only):")
    print(f"- Has Audio: {combined_analysis['has_audio']}")
    print(f"- Has Video: {combined_analysis['has_video']}")
    print(f"- Input Sources: {combined_analysis['input_sources']}")
    print(f"- Overall Safety Score: {combined_analysis['overall_safety_score']}/100")
    print(f"- Priority Level: {combined_analysis['priority_level']}")
    print(f"- Note: {combined_analysis['note']}")
    
    return combined_analysis

def test_audio_only_scenario():
    """Test scenario with only audio data available."""
    print("\nTesting Audio Only Scenario...")
    
    # Only transcribe data available
    transcribe_data = {
        "transcription": "I'm feeling a bit dizzy and need to sit down.",
        "audio_present": True,
        "input_mode": "base64",
        "event_id": "20240101T120200Z",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Audio Only Data:")
    print(f"- Transcription: {transcribe_data['transcription']}")
    print(f"- Audio Present: {transcribe_data['audio_present']}")
    
    # Simulate combined analysis with missing video
    combined_analysis = {
        "event_id": "20240101T120200Z",
        "has_audio": True,
        "has_video": False,
        "overall_safety_score": 100,
        "priority_level": "MEDIUM",
        "combined_indicators": ["audio_unusual"],
        "input_sources": ["audio"],
        "note": "Analysis based on audio input only"
    }
    
    print("\nCombined Analysis (Audio Only):")
    print(f"- Has Audio: {combined_analysis['has_audio']}")
    print(f"- Has Video: {combined_analysis['has_video']}")
    print(f"- Input Sources: {combined_analysis['input_sources']}")
    print(f"- Overall Safety Score: {combined_analysis['overall_safety_score']}/100")
    print(f"- Priority Level: {combined_analysis['priority_level']}")
    print(f"- Combined Indicators: {combined_analysis['combined_indicators']}")
    print(f"- Note: {combined_analysis['note']}")
    
    return combined_analysis

def test_no_data_scenario():
    """Test scenario with no input data available."""
    print("\nTesting No Data Scenario...")
    
    # No data available
    combined_analysis = {
        "event_id": "20240101T120300Z",
        "has_audio": False,
        "has_video": False,
        "overall_safety_score": 100,
        "priority_level": "UNKNOWN",
        "combined_indicators": [],
        "input_sources": [],
        "note": "No input data available"
    }
    
    print("No Data Available:")
    print(f"- Has Audio: {combined_analysis['has_audio']}")
    print(f"- Has Video: {combined_analysis['has_video']}")
    print(f"- Input Sources: {combined_analysis['input_sources']}")
    print(f"- Priority Level: {combined_analysis['priority_level']}")
    print(f"- Note: {combined_analysis['note']}")
    
    return combined_analysis

def test_bedrock_integration():
    """Test Bedrock integration (mock)."""
    print("\nTesting Bedrock Integration...")
    
    test_cases = [
        {
            "name": "Normal Activity",
            "combined_data": {
                "priority_level": "LOW",
                "overall_safety_score": 90,
                "combined_indicators": []
            },
            "expected_analysis": "NORMAL: Activity patterns appear normal. No immediate concerns."
        },
        {
            "name": "Moderate Risk",
            "combined_data": {
                "priority_level": "MEDIUM",
                "overall_safety_score": 60,
                "combined_indicators": ["audio_unusual"]
            },
            "expected_analysis": "WARNING: Moderate risk detected. Monitor closely."
        },
        {
            "name": "High Risk Emergency",
            "combined_data": {
                "priority_level": "HIGH",
                "overall_safety_score": 20,
                "combined_indicators": ["audio_emergency", "person_horizontal_position"]
            },
            "expected_analysis": "EMERGENCY: High risk situation detected. Immediate attention required."
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"- Priority: {test_case['combined_data']['priority_level']}")
        print(f"- Safety Score: {test_case['combined_data']['overall_safety_score']}/100")
        print(f"- Indicators: {test_case['combined_data']['combined_indicators']}")
        print(f"- Expected Analysis: {test_case['expected_analysis']}")

def test_event_processing_flow():
    """Test the complete event processing flow."""
    print("\nTesting Event Processing Flow...")
    
    # Simulate the 30-second window processing
    event_id = "20240101T120000Z"
    
    print(f"Processing Event ID: {event_id}")
    print("1. Load transcribe data from s3://events-bucket/events/transcribe/{event_id}.json")
    print("2. Load video data from s3://events-bucket/events/video/{event_id}.json")
    print("3. Combine analysis from both sources")
    print("4. Invoke Bedrock agent with combined data")
    print("5. Store combined results in s3://events-bucket/events/combined/{event_id}.json")
    print("6. Return comprehensive analysis")

if __name__ == "__main__":
    print("Combined Input Lambda Test Examples")
    print("=" * 50)
    
    # Test different scenarios
    test_combined_analysis()
    test_emergency_scenario()
    test_missing_data_scenario()
    test_audio_only_scenario()
    test_no_data_scenario()
    test_bedrock_integration()
    test_event_processing_flow()
    
    print("\n" + "=" * 50)
    print("Test completed! Note: Full testing requires AWS credentials and S3 setup.")
