# Video Invoke Lambda

This Lambda function processes single images containing multiple frame grids for elderly safety monitoring by analyzing image content using Amazon Rekognition and sending results to Agent Invoke Lambda for comprehensive analysis.

## Functionality

### Image Processing
- **Human Detection**: Uses Amazon Rekognition to detect people in multiple frame grid images
- **Label Detection**: Identifies objects, furniture, and environment elements
- **Face Detection**: Detects faces for person counting and analysis
- **Text Detection**: Extracts timestamps and other text from images
- **Fall Analysis**: Analyzes the image for fall detection patterns

### Agent Integration
- **Agent Invoke Lambda**: Sends analysis results to Agent Invoke Lambda
- **Conditional Processing**: Only processes images if human is detected
- **Batch Filtering**: Discards images with no human presence

### Smart Filtering
- **Human Detection Filter**: Only processes images containing humans
- **Efficient Processing**: Discards empty images to save storage and costs
- **Quality Control**: Ensures only relevant images are processed

## Input Event Format

```json
{
  "image_uri": "s3://bucket/path/to/grid-image.jpg"
}
```

## Output Format

### Successful Processing (Human Detected)
```json
{
  "statusCode": 200,
  "body": {
    "message": "Image processing completed",
    "results": {
      "status": "processed",
      "image_analysis": {
        "image_uri": "s3://bucket/grid-image.jpg",
        "labels": [
          {
            "Name": "Person",
            "Confidence": 99.14,
            "Instances": [...]
          }
        ],
        "faces": [...],
        "text": ["7:24PM", "7:25PM"],
        "person_count": 6,
        "human_detected": true,
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "fall_analysis": {
        "fall_detected": true,
        "fall_confidence": 60,
        "fall_indicators": ["multiple_people_present", "indoor_environment"],
        "safety_score": 80,
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "agent_response": {...},
      "timestamp": "2024-01-01T12:00:00Z",
      "image_uri": "s3://bucket/grid-image.jpg"
    }
  }
}
```

### Discarded Processing (No Human Detected)
```json
{
  "statusCode": 200,
  "body": {
    "message": "Image processing completed",
    "results": {
      "status": "discarded",
      "reason": "no_human_detected",
      "image_analysis": {...},
      "timestamp": "2024-01-01T12:00:00Z"
    }
  }
}
```

## Environment Variables

- `AGENT_INVOKE_LAMBDA_NAME`: Name of the Agent Invoke Lambda function
- `IMAGE_BUCKET`: S3 bucket for storing images

## Dependencies

- boto3: AWS SDK for Python
- botocore: Core functionality for boto3

## Analysis Features

### Human Detection
- Detects people using Rekognition label detection
- Identifies faces for person counting
- High confidence threshold (80%) for reliable detection
- Supports multiple people detection

### Fall Detection Analysis
- **Multiple People**: Detects assistance scenarios (multiple people present)
- **Indoor Environment**: Identifies home/indoor settings
- **Safety Scoring**: Calculates safety scores based on indicators
- **Fall Confidence**: Provides confidence levels for fall detection

### Text Extraction
- Extracts timestamps from images (e.g., "7:24PM", "7:25PM")
- Detects dates and other relevant text
- Supports multiple timestamp formats

### Label Analysis
- **Person Detection**: High-confidence person identification
- **Environment Detection**: Indoor/outdoor classification
- **Furniture Detection**: Identifies furniture and room elements
- **Object Detection**: Detects accessories, bags, and other objects

## Processing Logic

### Human Detection Threshold
- **Person Label**: Confidence > 80% for person detection
- **Face Detection**: Confidence > 80% for face detection
- **Combined Logic**: Either person label OR face detection triggers processing

### Fall Analysis Indicators
- **Multiple People Present**: Indicates potential assistance scenario
- **Indoor Environment**: Home setting increases fall risk context
- **Safety Score Calculation**: 100 - (indicators × 20)

### Agent Integration
- Sends complete analysis to Agent Invoke Lambda
- Includes image analysis, fall analysis, and metadata
- Handles Agent Invoke Lambda unavailability gracefully

## Error Handling

- Comprehensive error handling for image processing failures
- Graceful degradation when Rekognition services are unavailable
- Mock responses for testing when services are not configured
- Detailed logging for debugging and monitoring
- Fallback to mock analysis when Rekognition fails

## Use Cases

- **Fall Detection**: Analyze multiple frame grid images for fall scenarios
- **Activity Monitoring**: Track human presence in surveillance images
- **Emergency Detection**: Identify emergency situations in grid images
- **Quality Control**: Filter out images with no human activity
- **Cost Optimization**: Only process images containing people

## Testing

### Test Event Format
```json
{
  "image_uri": "s3://your-bucket-name/fall_inside_house_grid.jpg"
}
```

### Expected Results
- **With Human**: Returns processed analysis with fall detection
- **Without Human**: Returns discarded status with reason
- **Mock Mode**: Returns mock analysis for testing without S3

## Architecture Integration

This lambda is part of the fall detection pipeline:
1. **Input**: Single image (possibly with multiple frames) from Streamlit
2. **Processing**: Rekognition analysis for human detection
3. **Filtering**: Only processes if human detected
4. **Output**: Sends results to Agent Invoke Lambda
5. **Integration**: Connects to Bedrock Agent for final analysis