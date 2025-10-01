#!/usr/bin/env python3
"""
Comprehensive testing script for all lambda functions.
This script tests the lambda functions locally and provides examples for AWS testing.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add lambda directories to Python path
sys.path.append(str(Path(__file__).parent / "transcribe-invoke-lambda"))
sys.path.append(str(Path(__file__).parent / "video-invoke-lambda"))
sys.path.append(str(Path(__file__).parent / "action-lambda"))

def test_transcribe_lambda():
    """Test the transcribe-invoke-lambda function."""
    print("=" * 60)
    print("TESTING TRANSCRIBE INVOKE LAMBDA")
    print("=" * 60)
    
    try:
        from transcribe_invoke_lambda.index import handler as transcribe_handler
        
        # Test cases
        test_cases = [
            {
                "name": "Normal Activity Audio",
                "event": {
                    "audio_uri": "s3://test-bucket/normal-activity.wav",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "living_room_camera",
                        "duration": 30
                    }
                }
            },
            {
                "name": "Fall Detection Audio",
                "event": {
                    "audio_uri": "s3://test-bucket/fall-detected.wav",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "bedroom_camera",
                        "duration": 15,
                        "priority": "high"
                    }
                }
            },
            {
                "name": "Emergency Audio",
                "event": {
                    "audio_uri": "s3://test-bucket/emergency.wav",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "bedroom_camera",
                        "duration": 45,
                        "priority": "critical"
                    }
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n--- {test_case['name']} ---")
            try:
                result = transcribe_handler(test_case['event'], {})
                print(f"Status Code: {result['statusCode']}")
                if result['statusCode'] == 200:
                    body = json.loads(result['body'])
                    print(f"Message: {body['message']}")
                    if 'results' in body:
                        results = body['results']
                        print(f"Transcription: {results.get('transcription', 'N/A')[:100]}...")
                        print(f"Bedrock Analysis: {results.get('bedrock_analysis', {}).get('content', 'N/A')[:100]}...")
                else:
                    print(f"Error: {result['body']}")
            except Exception as e:
                print(f"Error: {str(e)}")
                
    except ImportError as e:
        print(f"Could not import transcribe lambda: {e}")
        print("Make sure you're running from the correct directory")

def test_video_lambda():
    """Test the video-invoke-lambda function."""
    print("\n" + "=" * 60)
    print("TESTING VIDEO INVOKE LAMBDA")
    print("=" * 60)
    
    try:
        from video_invoke_lambda.index import handler as video_handler
        
        # Test cases
        test_cases = [
            {
                "name": "Normal Activity Video",
                "event": {
                    "video_uri": "s3://test-bucket/normal-activity.mp4",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "living_room_camera",
                        "duration": 60
                    }
                }
            },
            {
                "name": "Fall Detection Video",
                "event": {
                    "video_uri": "s3://test-bucket/fall-detected.mp4",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "bedroom_camera",
                        "duration": 30,
                        "priority": "high"
                    }
                }
            },
            {
                "name": "Emergency Video",
                "event": {
                    "video_uri": "s3://test-bucket/emergency.mp4",
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "bedroom_camera",
                        "duration": 45,
                        "priority": "critical"
                    }
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n--- {test_case['name']} ---")
            try:
                result = video_handler(test_case['event'], {})
                print(f"Status Code: {result['statusCode']}")
                if result['statusCode'] == 200:
                    body = json.loads(result['body'])
                    print(f"Message: {body['message']}")
                    if 'results' in body:
                        results = body['results']
                        video_analysis = results.get('video_analysis', {})
                        print(f"Person Count: {video_analysis.get('person_count', 'N/A')}")
                        print(f"Safety Score: {video_analysis.get('safety_score', 'N/A')}/100")
                        print(f"Fall Indicators: {video_analysis.get('fall_indicators', [])}")
                        print(f"Bedrock Analysis: {results.get('bedrock_analysis', {}).get('content', 'N/A')[:100]}...")
                else:
                    print(f"Error: {result['body']}")
            except Exception as e:
                print(f"Error: {str(e)}")
                
    except ImportError as e:
        print(f"Could not import video lambda: {e}")
        print("Make sure you're running from the correct directory")

def test_agent_invoke_lambda():
    """Test the agent-invoke-lambda function."""
    print("\n" + "=" * 60)
    print("TESTING AGENT INVOKE LAMBDA")
    print("=" * 60)
    
    try:
        from agent_invoke_lambda.index import handler as agent_handler
        
        # Test cases
        test_cases = [
            {
                "name": "Both Inputs Available",
                "event": {
                    "event_id": "20240101T120000Z"
                }
            },
            {
                "name": "Audio Only",
                "event": {
                    "event_id": "20240101T120030Z"
                }
            },
            {
                "name": "Video Only",
                "event": {
                    "event_id": "20240101T120100Z"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n--- {test_case['name']} ---")
            try:
                result = agent_handler(test_case['event'], {})
                print(f"Status Code: {result['statusCode']}")
                if result['statusCode'] == 200:
                    body = json.loads(result['body'])
                    print(f"Message: {body['message']}")
                    print(f"Event ID: {body.get('results', {}).get('event_id', 'N/A')}")
                    if 'results' in body:
                        results = body['results']
                        print(f"Has Audio: {results.get('combined_analysis', {}).get('has_audio', 'N/A')}")
                        print(f"Has Video: {results.get('combined_analysis', {}).get('has_video', 'N/A')}")
                        print(f"Priority Level: {results.get('combined_analysis', {}).get('priority_level', 'N/A')}")
                else:
                    print(f"Error: {result['body']}")
            except Exception as e:
                print(f"Error: {str(e)}")
                
    except ImportError as e:
        print(f"Could not import agent invoke lambda: {e}")
        print("Make sure you're running from the correct directory")

def test_integration_flow():
    """Test the complete integration flow."""
    print("\n" + "=" * 60)
    print("TESTING INTEGRATION FLOW")
    print("=" * 60)
    
    print("This would test the complete flow:")
    print("1. Audio/Video → Transcribe/Video Lambda")
    print("2. Bedrock Analysis → Agent Invoke Lambda")
    print("3. SNS Notifications + Polly Synthesis")
    print("\nNote: Full integration testing requires AWS services to be configured.")

def generate_aws_test_commands():
    """Generate AWS CLI test commands."""
    print("\n" + "=" * 60)
    print("AWS CLI TEST COMMANDS")
    print("=" * 60)
    
    commands = [
        "# Test Transcribe Lambda",
        "aws lambda invoke \\",
        "  --function-name transcribe-invoke-lambda \\",
        "  --payload file://test-events/transcribe-test.json \\",
        "  response.json",
        "",
        "# Test Video Lambda",
        "aws lambda invoke \\",
        "  --function-name video-invoke-lambda \\",
        "  --payload file://test-events/video-test.json \\",
        "  response.json",
        "",
        "# Test Agent Invoke Lambda",
        "aws lambda invoke \\",
        "  --function-name agent-invoke-lambda \\",
        "  --payload file://test-events/agent-invoke-test.json \\",
        "  response.json",
        "",
        "# View response",
        "cat response.json | jq ."
    ]
    
    for command in commands:
        print(command)

def main():
    """Main testing function."""
    print("FALL DETECTION LAMBDA TESTING SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.utcnow().isoformat()}")
    
    # Test individual lambdas
    test_transcribe_lambda()
    test_video_lambda()
    test_agent_invoke_lambda()
    
    # Test integration flow
    test_integration_flow()
    
    # Generate AWS test commands
    generate_aws_test_commands()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)
    print(f"Test completed at: {datetime.utcnow().isoformat()}")
    print("\nNext steps:")
    print("1. Deploy lambdas to AWS")
    print("2. Configure environment variables")
    print("3. Set up S3 buckets and SNS topics")
    print("4. Test with real AWS services")
    print("5. Monitor CloudWatch logs for any issues")

if __name__ == "__main__":
    main()
