# Lambda Testing Guide

This guide covers how to test all the lambda functions in the fall detection system.

## Overview

The system has three main lambda functions:
1. **transcribe-invoke-lambda** - Processes audio files
2. **video-invoke-lambda** - Processes video files  
3. **agent-invoke-lambda** - Combines inputs and invokes Bedrock agent

## Testing Methods

### 1. Local Testing (Recommended for Development)

#### Prerequisites
```bash
# Install Python dependencies
pip install boto3 botocore

# Set up AWS credentials (if testing with real AWS services)
aws configure
```

#### Running Local Tests

**Transcribe Lambda:**
```bash
cd src/lambdas/transcribe-invoke-lambda
python test_example.py
```

**Video Lambda:**
```bash
cd src/lambdas/video-invoke-lambda
python test_example.py
```

**Action Lambda:**
```bash
cd src/lambdas/action-lambda
python test_example.py
```

### 2. Unit Testing with Mock Events

Each lambda includes test examples that simulate real events without requiring AWS services.

### 3. AWS Lambda Testing

#### Using AWS Console
1. Go to AWS Lambda Console
2. Select your lambda function
3. Click "Test" button
4. Create test event with sample JSON
5. Execute and view results

#### Using AWS CLI
```bash
# Test transcribe lambda
aws lambda invoke \
  --function-name transcribe-invoke-lambda \
  --payload file://test-events/transcribe-test.json \
  response.json

# Test video lambda
aws lambda invoke \
  --function-name video-invoke-lambda \
  --payload file://test-events/video-test.json \
  response.json

# Test action lambda
aws lambda invoke \
  --function-name action-lambda \
  --payload file://test-events/action-test.json \
  response.json
```

## Test Event Examples

### Transcribe Lambda Test Events

**Basic Audio Processing:**
```json
{
  "audio_uri": "s3://your-bucket/audio/sample.wav",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "camera_mic",
    "duration": 30
  }
}
```

**Fall Detection Audio:**
```json
{
  "audio_uri": "s3://your-bucket/audio/fall-detected.wav",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "bedroom_camera",
    "duration": 15,
    "priority": "high"
  }
}
```

### Video Lambda Test Events

**Basic Video Processing:**
```json
{
  "video_uri": "s3://your-bucket/video/sample.mp4",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "living_room_camera",
    "duration": 60
  }
}
```

**Fall Detection Video:**
```json
{
  "video_uri": "s3://your-bucket/video/fall-detected.mp4",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "bedroom_camera",
    "duration": 30,
    "priority": "high"
  }
}
```

### Action Lambda Test Events

**Bedrock Response (Fall Detected):**
```json
{
  "bedrock_response": {
    "content": "EMERGENCY: Fall detected! The person appears to have fallen and is lying motionless on the floor. Immediate attention required.",
    "confidence": 0.95,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Bedrock Response (Normal Activity):**
```json
{
  "bedrock_response": {
    "content": "Normal activity confirmed. The person is walking around normally and appears to be in good health.",
    "confidence": 0.85,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Environment Variables for Testing

### Required Environment Variables

**For Transcribe Lambda:**
```bash
TRANSCRIPTION_BUCKET=your-transcription-bucket
```

**For Video Lambda:**
```bash
VIDEO_ANALYSIS_BUCKET=your-video-analysis-bucket
REKOGNITION_SNS_TOPIC=arn:aws:sns:region:account:rekognition-topic
REKOGNITION_ROLE_ARN=arn:aws:iam::account:role/RekognitionRole
```

**For Action Lambda:**
```bash
ALERTS_TOPIC_ARN=arn:aws:sns:region:account:alerts-topic
```

### SSM Parameters (for Bedrock integration)
```bash
/fall-detection/bedrock/agent-id=your-agent-id
/fall-detection/bedrock/kb-id=your-knowledge-base-id
/fall-detection/bedrock/model-id=your-model-id
```

## Testing Scenarios

### 1. Happy Path Testing
- Normal audio/video processing
- Successful Bedrock analysis
- Proper action execution

### 2. Error Handling Testing
- Invalid input data
- Missing environment variables
- AWS service failures
- Network timeouts

### 3. Edge Case Testing
- Empty audio/video files
- Very long processing times
- High-priority emergency scenarios
- Multiple concurrent requests

### 4. Integration Testing
- End-to-end flow from audio/video to actions
- SNS notification delivery
- S3 storage verification
- Bedrock agent responses

## Monitoring and Debugging

### CloudWatch Logs
- Check `/aws/lambda/function-name` log groups
- Look for ERROR, WARN, and INFO messages
- Monitor execution duration and memory usage

### Common Issues and Solutions

**Transcribe Lambda Issues:**
- Audio format not supported → Convert to WAV/MP3
- Transcription job timeout → Increase lambda timeout
- No audio content → Check audio file validity

**Video Lambda Issues:**
- Rekognition job failure → Check video format and size
- Person not detected → Verify video quality and lighting
- Analysis timeout → Increase lambda timeout

**Action Lambda Issues:**
- SNS publish failure → Check topic ARN and permissions
- Polly synthesis error → Verify voice ID and text length
- Bedrock response parsing → Check response format

## Performance Testing

### Load Testing
```bash
# Test with multiple concurrent invocations
for i in {1..10}; do
  aws lambda invoke \
    --function-name your-lambda \
    --payload file://test-event.json \
    response-$i.json &
done
wait
```

### Memory and Timeout Testing
- Test with large audio/video files
- Monitor memory usage in CloudWatch
- Adjust lambda configuration as needed

## Security Testing

### IAM Permissions
- Verify lambda execution role has required permissions
- Test with minimal required permissions
- Check for overly broad permissions

### Data Privacy
- Ensure no sensitive data in logs
- Verify S3 bucket encryption
- Check data retention policies

## Best Practices

1. **Always test locally first** before deploying
2. **Use realistic test data** that matches production scenarios
3. **Test error conditions** not just happy paths
4. **Monitor performance** and optimize as needed
5. **Keep test data secure** and don't commit sensitive information
6. **Document test results** for future reference
7. **Automate testing** where possible with CI/CD pipelines
