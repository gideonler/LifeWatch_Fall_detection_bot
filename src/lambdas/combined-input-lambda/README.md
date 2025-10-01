# Combined Input Lambda

This Lambda function combines outputs from transcribe-invoke-lambda and video-invoke-lambda and invokes the Bedrock agent for comprehensive elderly safety analysis.

## Functionality

### Input Processing
- **Event ID Based**: Processes data for a specific event_id (30-second window)
- **Multi-Modal Analysis**: Combines audio transcription and video analysis
- **Data Loading**: Reads from S3 events bucket for transcribe and video results

### Bedrock Integration
- **Agent Invocation**: Calls Bedrock agents with combined analysis
- **Comprehensive Input**: Provides both audio and video context to Bedrock
- **Priority Assessment**: Determines overall safety priority based on combined indicators

### Storage
- **S3 Integration**: Stores combined results in events bucket
- **Event Tracking**: Maintains traceability with event_id based storage

## Input Event Format

```json
{
  "event_id": "20240101T120000Z",
  "metadata": {
    "source": "scheduler",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Output Format

```json
{
  "statusCode": 200,
  "body": {
    "message": "Combined input processing completed successfully",
    "results": {
      "event_id": "20240101T120000Z",
      "transcribe_data": {...},
      "video_data": {...},
      "combined_analysis": {
        "has_audio": true,
        "has_video": true,
        "overall_safety_score": 85,
        "priority_level": "MEDIUM",
        "combined_indicators": ["audio_unusual", "person_horizontal_position"]
      },
      "bedrock_analysis": {
        "content": "Analysis results...",
        "priority": "MEDIUM",
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "timestamp": "2024-01-01T12:00:00Z"
    }
  }
}
```

## Environment Variables

- `EVENTS_BUCKET`: S3 bucket containing event data (required)
- Bedrock configuration is retrieved from SSM Parameter Store:
  - `/fall-detection/bedrock/agent-id`
  - `/fall-detection/bedrock/model-id`

## Dependencies

- boto3: AWS SDK for Python
- botocore: Core functionality for boto3

## Analysis Features

### Combined Analysis
- **Multi-Modal Detection**: Combines audio and video indicators
- **Priority Assessment**: Determines overall priority based on all inputs
- **Safety Scoring**: Calculates combined safety score
- **Indicator Tracking**: Tracks fall and emergency indicators from both modalities

### Audio Analysis Integration
- **Transcription Processing**: Analyzes audio transcription for keywords
- **Emergency Detection**: Identifies emergency situations in audio
- **Activity Patterns**: Detects unusual activity patterns in speech

### Video Analysis Integration
- **Person Detection**: Incorporates person count and positioning
- **Movement Analysis**: Includes movement patterns and stability
- **Fall Indicators**: Processes visual fall detection indicators
- **Safety Scoring**: Integrates video-based safety assessments

## Error Handling

- Graceful handling when transcribe or video data is missing
- Comprehensive error handling for S3 operations
- Fallback mock responses when Bedrock is not configured
- Detailed logging for debugging and monitoring

## Use Cases

- **Combined Fall Detection**: Uses both audio and video evidence
- **Emergency Assessment**: Evaluates emergency situations comprehensively
- **Activity Monitoring**: Tracks normal vs. unusual activity patterns
- **Safety Risk Assessment**: Provides holistic safety evaluation
- **Priority Determination**: Assigns appropriate priority levels for alerts
