# DynamoDB Setup Guide for Fall Detection System

## Overview

This guide walks you through setting up DynamoDB tables for the elderly fall detection system. The system uses DynamoDB to store Telegram subscriber information and other operational data.

### Required Services
- Amazon DynamoDB
- IAM (for role management)
- AWS Lambda (for integration)

## Table Setup

### Table 1: `telegram_subscribers`

This table stores information about users who have subscribed to receive fall detection alerts via Telegram.

#### Table Configuration
- **Table Name**: `telegram_subscribers`
- **Partition Key**: `chat_id` (String)
- **Sort Key**: None
- **Capacity Mode**: On-demand
- **Table Status**: Active

#### Schema Design
```json
{
  "chat_id": "1301587578",
  "username": "gdlrr",
  "active": true,
  "subscribed_at": "2025-10-19T09:25:18.452053"
}
```

**Table Attributes:**
- **chat_id** (String) - Partition key - Telegram chat ID
- **username** (String) - Telegram username
- **active** (Boolean) - Subscription status (true/false)
- **subscribed_at** (String) - ISO timestamp when user subscribed

## Step-by-Step Setup

### Create DynamoDB Table

#### Using AWS Console
1. **Navigate to DynamoDB Console**
   - Go to [AWS DynamoDB Console](https://console.aws.amazon.com/dynamodb/)
   - Select your region (e.g., `ap-southeast-1`)

2. **Create Table**
   - Click **"Create table"**
   - **Table name**: `telegram_subscribers`
   - **Partition key**: `chat_id` (String)
   - **Sort key**: Leave empty
   - **Table settings**: Use default settings
   - **Capacity mode**: **On-demand**

3. **Configure Table**
   - **Encryption**: Use AWS owned keys (default)
   - **Point-in-time recovery**: Enable if needed
   - **Tags**: Add appropriate tags for cost tracking

#### Using AWS CLI
```bash
# Create telegram_subscribers table
aws dynamodb create-table \
    --table-name telegram_subscribers \
    --attribute-definitions \
        AttributeName=chat_id,AttributeType=S \
    --key-schema \
        AttributeName=chat_id,KeyType=HASH \
    --billing-mode ON_DEMAND \
    --region ap-southeast-1
```

