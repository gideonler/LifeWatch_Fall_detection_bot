# Telegram Bedrock Handler Lambda

## Overview

This Lambda function handles Telegram bot interactions and integrates with AWS Bedrock Agent for intelligent fall detection analysis. It processes user commands, manages subscriptions, and provides conversational AI responses about fall detection events.

##  Prerequisites

### Required AWS Resources
- **AWS Account** with Lambda, API Gateway, and Bedrock access
- **DynamoDB Table**: `telegram_subscribers` (for user management)
- **Bedrock Agent**: Configured with knowledge base
- **Telegram Bot**: Created via [@BotFather](https://t.me/botfather)

### Required Services
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon Bedrock (Agent)
- Telegram Bot API

## Environment Variables

Configure these environment variables in your Lambda function:

```bash
# Required
TELEGRAM_TOKEN=your_telegram_bot_token
AGENT_ID=your_bedrock_agent_id
AGENT_ALIAS_ID=your_agent_alias_id

# Optional (with defaults)
REGION=ap-southeast-1
SUBSCRIBERS_TABLE=telegram_subscribers
```

## API Gateway Setup

### Step 1: Create API Gateway

#### Using AWS Console
1. **Navigate to API Gateway Console**
   - Go to [AWS API Gateway Console](https://console.aws.amazon.com/apigateway/)
   - Click **"Create API"**

2. **Choose API Type**
   - Select **"REST API"**
   - Click **"Build"**
   - Choose **"New API"**
   - **API name**: `telegram-fall-detection-bot`
   - **Description**: `API Gateway for Telegram bot webhook`
   - **Endpoint Type**: Regional

### Step 2: Create Resource and Method

#### Create POST Method
1. **Create Resource**
   - Click **"Actions"** → **"Create Resource"
   - **Resource Name**: `webhook`
   - **Resource Path**: `/webhook`
   - **Enable CORS**: No (for now)

2. **Create POST Method**
   - Select the `/webhook` resource
   - Click **"Actions"** → **"Create Method"**
   - Choose **"POST"**
   - Click the checkmark

3. **Configure Method**
   - **Integration type**: Lambda Function
   - **Use Lambda Proxy integration**: ✅ Check this
   - **Lambda Region**: Select your region
   - **Lambda Function**: Select your `telegram_bedrock_handler` function
   - **Use Default Timeout**: ✅ Check this

### Step 3: Deploy API

1. **Deploy API**
   - Click **"Actions"** → **"Deploy API"**
   - **Deployment stage**: `[New Stage]`
   - **Stage name**: `prod`
   - **Stage description**: `Production stage`
   - Click **"Deploy"**

2. **Note the Invoke URL**
   - Copy the **Invoke URL** (e.g., `https://abc123.execute-api.ap-southeast-1.amazonaws.com/prod`)
   - Your webhook URL will be: `https://abc123.execute-api.ap-southeast-1.amazonaws.com/prod/webhook`

### Step 2: Set Webhook

#### Using Telegram API
```bash
# Set webhook URL
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-api-gateway-url.amazonaws.com/prod/webhook"
  }'

# Verify webhook is set
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```



### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/subscribe` | Subscribe to fall detection alerts | `/subscribe` |
| `/unsubscribe` | Unsubscribe from alerts | `/unsubscribe` |
| `/status` | Check subscription status | `/status` |
| `How many falls this week?` | Ask about fall statistics | Natural language |
| `Show me recent falls` | Get recent fall events | Natural language |
| `What patterns do you see?` | Analyze fall patterns | Natural language |

### Natural Language Queries

Users can ask questions in natural language about:
- Fall statistics and counts
- Recent fall events
- Fall patterns and trends
- Specific time periods
- Alert levels and severity

