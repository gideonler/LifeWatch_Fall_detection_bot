# Video Invoke Lambda

This Lambda function processes video files for elderly safety monitoring by analyzing video content using Amazon Rekognition and invoking Bedrock agents for comprehensive analysis.

## Functionality

### Video Processing
- **Person Tracking**: Uses Amazon Rekognition to track people in video
- **Movement Analysis**: Analyzes person movement patterns and positions
- **Fall Detection**: Identifies potential fall indicators in video frames
- **Safety Scoring**: Calculates safety scores based on analysis

### Bedrock Integration
- **Agent Invocation**: Calls Bedrock agents for elderly safety analysis
- **Knowledge Base**: Leverages Bedrock knowledge base for context
- **Risk Assessment**: Analyzes video data for safety risks
- **Action Recommendations**: Provides actionable insights

### Storage
- **S3 Integration**: Stores video analysis results and metadata
- **Metadata Tracking**: Tracks timestamps, video sources, and analysis results

## Input Event Format

```json
{
  "video_uri": "s3://bucket/path/to/video.mp4",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "camera_1",
    "duration": 30
  }
}
```

## Output Format

```json
{
  "statusCode": 200,
  "body": {
    "message": "Video processing completed successfully",
    "results": {
      "video_analysis": {
        "person_count": 1,
        "movement_analysis": [...],
        "fall_indicators": [],
        "safety_score": 85,
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "bedrock_analysis": {
        "content": "Analysis results...",
        "priority": "MEDIUM",
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "timestamp": "2024-01-01T12:00:00Z",
      "video_uri": "s3://bucket/path/to/video.mp4"
    }
  }
}
```

## Environment Variables

- `VIDEO_ANALYSIS_BUCKET`: S3 bucket for storing video analysis results
- `REKOGNITION_SNS_TOPIC`: SNS topic for Rekognition job notifications
- `REKOGNITION_ROLE_ARN`: IAM role for Rekognition service
- Bedrock configuration is retrieved from SSM Parameter Store:
  - `/fall-detection/bedrock/agent-id`
  - `/fall-detection/bedrock/kb-id`
  - `/fall-detection/bedrock/model-id`

## Dependencies

- boto3: AWS SDK for Python
- botocore: Core functionality for boto3

## Analysis Features

### Person Tracking
- Detects and tracks people in video frames
- Analyzes bounding box positions and movements
- Calculates confidence scores for detections

### Fall Detection
- Identifies horizontal positioning (person lying down)
- Detects unstable movement patterns
- Flags potential fall indicators

### Safety Scoring
- Calculates safety scores (0-100) based on analysis
- Considers fall indicators and movement stability
- Provides risk assessment

### Movement Analysis
- Tracks movement types (walking, standing, sitting, lying)
- Analyzes movement speed and direction
- Assesses movement stability

## Error Handling

- Comprehensive error handling for video processing failures
- Graceful degradation when Rekognition services are unavailable
- Mock responses for testing when services are not configured
- Detailed logging for debugging and monitoring

## Use Cases

- **Fall Detection**: Analyze video for fall-related movements and positions
- **Activity Monitoring**: Track normal vs. unusual activity patterns
- **Safety Assessment**: Evaluate safety risks in video streams
- **Emergency Detection**: Identify emergency situations requiring attention
- **Behavioral Analysis**: Monitor behavioral patterns for health insights
