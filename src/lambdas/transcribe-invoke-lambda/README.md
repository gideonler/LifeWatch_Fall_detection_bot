# Transcribe Invoke Lambda

This Lambda function processes audio files for elderly safety monitoring by transcribing audio content and invoking Bedrock agents for analysis.

## Functionality

### Audio Processing
- **Transcription**: Uses Amazon Transcribe to convert audio to text
- **Speaker Detection**: Identifies multiple speakers in audio streams
- **Format Support**: Handles various audio formats (WAV, MP3, etc.)

### Bedrock Integration
- **Agent Invocation**: Calls Bedrock agents for elderly safety analysis
- **Knowledge Base**: Leverages Bedrock knowledge base for context
- **Fall Detection**: Analyzes transcription for fall-related keywords
- **Emergency Detection**: Identifies emergency situations in audio

### Storage
- **S3 Integration**: Stores transcription results and analysis
- **Metadata**: Tracks timestamps, audio sources, and analysis results

## Input Event Format

```json
{
  "audio_uri": "s3://bucket/path/to/audio.wav",
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "camera_mic"
  }
}
```

## Output Format

```json
{
  "statusCode": 200,
  "body": {
    "message": "Audio processing completed successfully",
    "results": {
      "transcription": "Audio transcript text...",
      "bedrock_analysis": {
        "content": "Analysis results...",
        "priority": "HIGH",
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "timestamp": "2024-01-01T12:00:00Z",
      "audio_uri": "s3://bucket/path/to/audio.wav"
    }
  }
}
```

## Environment Variables

- `TRANSCRIPTION_BUCKET`: S3 bucket for storing transcription results
- Bedrock configuration is retrieved from SSM Parameter Store:
  - `/fall-detection/bedrock/agent-id`
  - `/fall-detection/bedrock/kb-id`
  - `/fall-detection/bedrock/model-id`

## Dependencies

- boto3: AWS SDK for Python
- botocore: Core functionality for boto3

## Error Handling

- Comprehensive error handling for transcription failures
- Graceful degradation when Bedrock services are unavailable
- Mock responses for testing when Bedrock is not configured
- Detailed logging for debugging and monitoring

## Use Cases

- **Fall Detection**: Analyze audio for fall-related sounds and speech
- **Emergency Monitoring**: Detect emergency situations in audio streams
- **Activity Monitoring**: Track normal vs. unusual activity patterns
- **Safety Alerts**: Generate alerts based on audio analysis
