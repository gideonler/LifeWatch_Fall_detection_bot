# Action Lambda

This Lambda function processes output from the Bedrock agent and executes appropriate actions for elderly safety monitoring.

## Components

### 1. ActionHandler (`action_handler.py`)
- Processes Bedrock agent output to determine appropriate actions
- Analyzes content for different scenarios:
  - Fall detection
  - Emergency situations
  - Unusual activity
  - Normal activity
- Returns prioritized actions based on analysis

### 2. AgentExecutor (`agent_executor.py`)
- Executes actions using AWS SNS and Amazon Polly
- Sends notifications via SNS for alerts
- Synthesizes speech using Polly for immediate audio alerts
- Handles different action types with appropriate responses

### 3. Main Handler (`index.py`)
- Entry point for the Lambda function
- Orchestrates the flow between ActionHandler and AgentExecutor
- Handles errors and returns appropriate responses

## Action Types

- **EMERGENCY_ALERT**: Critical situations requiring immediate attention
- **FALL_DETECTED**: Fall detection scenarios
- **UNUSUAL_ACTIVITY**: Unusual behavior patterns
- **NORMAL_ACTIVITY**: Regular, expected behavior
- **CHECK_IN_REMINDER**: Scheduled check-in reminders
- **MEDICATION_REMINDER**: Medication reminder alerts

## Environment Variables

- `ALERTS_TOPIC_ARN`: SNS topic ARN for sending notifications

## Dependencies

- boto3: AWS SDK for Python
- botocore: Core functionality for boto3

## Usage

The Lambda function expects an event containing Bedrock agent output. It will:

1. Analyze the output using ActionHandler
2. Determine appropriate actions based on content analysis
3. Execute actions using AgentExecutor
4. Send SNS notifications and synthesize speech as needed
5. Return execution results

## Error Handling

- Comprehensive error handling for all components
- Graceful degradation when services are unavailable
- Detailed logging for debugging and monitoring
