#!/usr/bin/env python3
"""
Example test script to demonstrate the transcribe-invoke-lambda functionality.
This is for testing purposes and not part of the Lambda deployment.
"""

import json
from datetime import datetime

def test_audio_transcription():
    """Test audio transcription scenario."""
    print("Testing Audio Transcription Scenario...")
    
    # Simulate transcription results
    transcription = """
    Speaker 1: Hello, I'm just walking around the room.
    Speaker 1: Everything seems fine today.
    Speaker 1: I'll be in the kitchen for a while.
    """
    
    print("Transcription Results:")
    print(f"Text: {transcription.strip()}")
    print(f"Length: {len(transcription)} characters")
    print(f"Speakers: 1 detected")
    
    return transcription

def test_fall_detection_audio():
    """Test fall detection in audio."""
    print("\nTesting Fall Detection Audio Scenario...")
    
    transcription = """
    Speaker 1: Oh no! I think I fell down.
    Speaker 1: Help! I can't get up.
    Speaker 1: Someone please help me!
    """
    
    print("Fall Detection Transcription:")
    print(f"Text: {transcription.strip()}")
    
    # Check for fall-related keywords
    fall_keywords = ['fall', 'fell', 'help', 'emergency', 'down']
    found_keywords = [word for word in fall_keywords if word.lower() in transcription.lower()]
    
    print(f"Fall Keywords Found: {found_keywords}")
    print(f"Risk Level: {'HIGH' if found_keywords else 'LOW'}")
    
    return transcription

def test_emergency_audio():
    """Test emergency situation in audio."""
    print("\nTesting Emergency Audio Scenario...")
    
    transcription = """
    Speaker 1: Emergency! Emergency!
    Speaker 1: I need immediate medical attention.
    Speaker 1: Call 911 right now!
    """
    
    print("Emergency Transcription:")
    print(f"Text: {transcription.strip()}")
    
    # Check for emergency keywords
    emergency_keywords = ['emergency', 'urgent', 'medical', '911', 'ambulance']
    found_keywords = [word for word in emergency_keywords if word.lower() in transcription.lower()]
    
    print(f"Emergency Keywords Found: {found_keywords}")
    print(f"Priority: {'CRITICAL' if found_keywords else 'NORMAL'}")
    
    return transcription

def test_normal_activity_audio():
    """Test normal activity in audio."""
    print("\nTesting Normal Activity Audio Scenario...")
    
    transcription = """
    Speaker 1: Good morning, I'm having my breakfast.
    Speaker 1: The weather is nice today.
    Speaker 1: I'll go for a walk later.
    """
    
    print("Normal Activity Transcription:")
    print(f"Text: {transcription.strip()}")
    
    # Check for normal activity indicators
    normal_keywords = ['good', 'morning', 'breakfast', 'walk', 'nice']
    found_keywords = [word for word in normal_keywords if word.lower() in transcription.lower()]
    
    print(f"Normal Activity Keywords Found: {found_keywords}")
    print(f"Activity Status: {'NORMAL' if found_keywords else 'UNKNOWN'}")
    
    return transcription

def test_bedrock_analysis():
    """Test Bedrock analysis (mock)."""
    print("\nTesting Bedrock Analysis...")
    
    test_cases = [
        ("I fell down and need help!", "EMERGENCY: Potential fall or emergency situation detected in audio. Immediate attention required.", "HIGH"),
        ("Something unusual is happening here.", "WARNING: Unusual activity detected in audio. Monitor closely.", "MEDIUM"),
        ("I'm walking around normally today.", "NORMAL: Audio indicates normal activity patterns. No immediate concerns.", "LOW")
    ]
    
    for transcription, expected_analysis, expected_priority in test_cases:
        print(f"\nTranscription: {transcription}")
        print(f"Expected Analysis: {expected_analysis}")
        print(f"Expected Priority: {expected_priority}")
        
        # Simulate keyword analysis
        if any(word in transcription.lower() for word in ['fall', 'fell', 'help', 'emergency']):
            detected_priority = "HIGH"
        elif any(word in transcription.lower() for word in ['unusual', 'strange', 'concerning']):
            detected_priority = "MEDIUM"
        else:
            detected_priority = "LOW"
        
        print(f"Detected Priority: {detected_priority}")

def test_speaker_analysis():
    """Test speaker analysis."""
    print("\nTesting Speaker Analysis...")
    
    # Simulate multi-speaker transcription
    multi_speaker_transcription = """
    Speaker 1: Hello, how are you feeling today?
    Speaker 2: I'm doing well, thank you for asking.
    Speaker 1: That's good to hear. Are you taking your medication?
    Speaker 2: Yes, I took it this morning as usual.
    """
    
    print("Multi-Speaker Transcription:")
    print(f"Text: {multi_speaker_transcription.strip()}")
    
    # Count speakers
    speaker_count = len(set(line.split(':')[0] for line in multi_speaker_transcription.strip().split('\n') if ':' in line))
    print(f"Speakers Detected: {speaker_count}")
    
    # Analyze conversation type
    if 'medication' in multi_speaker_transcription.lower():
        print("Conversation Type: Health/Medication Check")
    elif 'feeling' in multi_speaker_transcription.lower():
        print("Conversation Type: Wellness Check")
    else:
        print("Conversation Type: General Conversation")

if __name__ == "__main__":
    print("Transcribe Invoke Lambda Test Examples")
    print("=" * 50)
    
    # Test different scenarios
    test_audio_transcription()
    test_fall_detection_audio()
    test_emergency_audio()
    test_normal_activity_audio()
    test_bedrock_analysis()
    test_speaker_analysis()
    
    print("\n" + "=" * 50)
    print("Test completed! Note: Full testing requires AWS credentials and Transcribe setup.")
