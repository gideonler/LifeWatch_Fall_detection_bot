# Agent Invoke Lambda

## Overview

The Agent Invoke Lambda, as its name suggests, invokes AWS Bedrock to analyze camera images for potential falls, medical emergencies, and other safety concerns in elderly care environments. It is currentlh configured to use AWS Bedrock's Claude 3.5 Sonnet model.

This Lambda function:
- Invokes bedrock with the prompt and incident image
- Determines alert severity levels based on detected activities
- Maintains a knowledge base of historical events for context-aware analysis
- Triggers appropriate alerts based on the analysis results

## Features

### 🧠 AI-Powered Analysis
- Uses Claude 3.5 Sonnet for multimodal image and text analysis
- Specialized prompt engineering for elderly care monitoring
- Context-aware decision making using historical events

### 📊 Alert Classification
- **Level 0**: No issues detected
- **Level 1**: Possible issue requiring attention (soft alert)
- **Level 2**: Issue requiring immediate action (high alert)

### 🗄️ Knowledge Base Integration
- Maintains historical event database in S3
- Uses past events for improved decision making
- Automatic context retrieval from last 24 hours

## Architecture

```
S3 Bucket (Images) → Agent Invoke Lambda → AWS Bedrock (Claude 3.5) → Analysis Results
                        ↓
                   Knowledge Base (S3)
                        ↓
                   Historical Context
```

## Configuration

### Environment Variables
- `BUCKET`: S3 bucket name for image storage (`elderly-home-monitoring-images`)
- `PREFIX`: S3 prefix for detected images (`detected-images/datestr=20251006/`)
- `KNOWLEDGE_BASE_PREFIX`: S3 prefix for knowledge base (`knowledge-base/`)
- `MODEL_ID`: Bedrock model identifier (`anthropic.claude-3-5-sonnet-20240620-v1:0`)

### AWS Services Used
- **AWS Bedrock**: AI model inference
- **Amazon S3**: Image storage and knowledge base
- **AWS Lambda**: Serverless compute

## Input/Output

### Input
The Lambda expects to be triggered by events (typically from S3 or scheduled invocations) and will automatically:
1. List objects in the configured S3 prefix
2. Find the latest JPG image
3. Download and analyze the image

### Output
Returns a JSON response with the following structure:
```json
{
  "alert_level": 0,
  "reason": "No concerning activity detected",
  "log_file_name": "20250106-143022_analysis.json",
  "brief_description": "Elderly person sitting normally in living room",
  "full_description": "Detailed analysis of the scene...",
  "timestamp": "20250106-143022",
  "image_key": "detected-images/datestr=20251006/image_001.jpg",
  "model_used": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "historical_context_used": 5
}
```

## Alert Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| 0 | No issues detected | Continue monitoring |
| 1 | Possible concern | Review and monitor closely |
| 2 | Immediate attention needed | Trigger emergency protocols |

## Knowledge Base

The system maintains a knowledge base of historical events that helps improve decision making:

### Storage Location
- S3 bucket: `elderly-home-monitoring-images`
- Prefix: `knowledge-base/`
- Format: JSON files with timestamp naming

### Knowledge Base Entry Structure
```json
{
  "timestamp": "20250106-143022",
  "image_key": "detected-images/datestr=20251006/image_001.jpg",
  "alert_level": 0,
  "reason": "No concerning activity detected",
  "log_file_name": "20250106-143022_analysis.json",
  "brief_description": "Normal activity",
  "full_description": "Detailed description...",
  "model_used": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "knowledge_base_id": "uuid-string",
  "created_at": "2025-01-06T14:30:22Z"
}
```

## Error Handling

The Lambda includes comprehensive error handling for:
- S3 access issues
- Image download failures
- Bedrock API errors
- JSON parsing errors
- Knowledge base access problems

In case of errors, the function returns appropriate error codes and fallback analysis results.

## Dependencies

### Python Packages
- `boto3>=1.34.0`: AWS SDK for Python
- `botocore>=1.34.0`: Low-level AWS service access

### AWS Permissions Required
- S3 read/write access to the monitoring bucket
- Bedrock model invocation permissions
- CloudWatch Logs write permissions

## Monitoring and Logging

The Lambda function logs:
- Image processing steps
- Bedrock API calls and responses
- Knowledge base operations
- Error conditions and fallback scenarios

Monitor CloudWatch Logs for:
- Processing times
- API errors
- Knowledge base access patterns
- Alert level distributions

## Performance Considerations

- **Cold Start**: ~2-3 seconds for first invocation
- **Processing Time**: ~5-10 seconds per image analysis
- **Memory**: Recommended 1024MB for optimal performance
- **Timeout**: Set to 5 minutes to handle large images

## Security

- Uses IAM roles for AWS service access
- No hardcoded credentials
- Secure image processing in AWS infrastructure
- Knowledge base data encrypted at rest in S3

## Troubleshooting

### Common Issues

1. **No images found**: Check S3 bucket and prefix configuration
2. **Bedrock errors**: Verify model permissions and region settings
3. **Knowledge base errors**: Ensure S3 write permissions
4. **JSON parsing errors**: Check Bedrock response format

### Debug Steps

1. Check CloudWatch Logs for detailed error messages
2. Verify S3 bucket permissions and image availability
3. Test Bedrock model access with simple prompts
4. Validate knowledge base S3 permissions

## Future Enhancements

Potential improvements:
- Multi-model ensemble analysis
- Real-time alert thresholds
- Integration with emergency services
- Advanced pattern recognition in knowledge base
- Custom model fine-tuning for specific care scenarios