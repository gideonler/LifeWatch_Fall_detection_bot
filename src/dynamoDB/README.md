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

### Step 1: Create DynamoDB Table

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

### Step 2: Configure IAM Permissions

#### Lambda Execution Role Permissions
Add these permissions to your Lambda execution role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:ap-southeast-1:*:table/telegram_subscribers"
        }
    ]
}
```

### Step 3: Test Table Operations

#### Python Test Script
```python
# test_dynamodb.py
import boto3
import json
from datetime import datetime

def test_dynamodb_operations():
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table('telegram_subscribers')
    
    # Test 1: Add a subscriber
    test_subscriber = {
        'chat_id': '123456789',
        'username': 'test_user',
        'active': True,
        'subscribed_at': datetime.utcnow().isoformat()
    }
    
    # Put item
    response = table.put_item(Item=test_subscriber)
    print("✅ Subscriber added successfully")
    
    # Test 2: Get subscriber
    response = table.get_item(Key={'chat_id': '123456789'})
    if 'Item' in response:
        print("✅ Subscriber retrieved successfully")
        print(f"Username: {response['Item']['username']}")
    
    # Test 3: Update subscriber
    table.update_item(
        Key={'chat_id': '123456789'},
        UpdateExpression='SET active = :active',
        ExpressionAttributeValues={':active': False}
    )
    print("✅ Subscriber updated successfully")
    
    # Test 4: Scan all subscribers
    response = table.scan()
    print(f"✅ Found {response['Count']} subscribers")
    
    # Test 5: Delete test subscriber
    table.delete_item(Key={'chat_id': '123456789'})
    print("✅ Test subscriber deleted")

if __name__ == "__main__":
    test_dynamodb_operations()
```

## Data Operations

### Common Operations

#### Add New Subscriber
```python
def add_subscriber(chat_id, username):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('telegram_subscribers')
    
    subscriber = {
        'chat_id': chat_id,
        'username': username,
        'active': True,
        'subscribed_at': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=subscriber)
    return subscriber
```

#### Get All Active Subscribers
```python
def get_all_subscribers():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('telegram_subscribers')
    
    response = table.scan(
        FilterExpression='active = :active',
        ExpressionAttributeValues={':active': True}
    )
    
    return response['Items']
```

#### Update Subscriber Status
```python
def update_subscriber_status(chat_id, active_status):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('telegram_subscribers')
    
    table.update_item(
        Key={'chat_id': chat_id},
        UpdateExpression='SET active = :active',
        ExpressionAttributeValues={':active': active_status}
    )
```

#### Deactivate Subscriber
```python
def deactivate_subscriber(chat_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('telegram_subscribers')
    
    table.update_item(
        Key={'chat_id': chat_id},
        UpdateExpression='SET active = :inactive',
        ExpressionAttributeValues={':inactive': False}
    )
```

#### Get Subscriber by Chat ID
```python
def get_subscriber(chat_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('telegram_subscribers')
    
    response = table.get_item(Key={'chat_id': chat_id})
    return response.get('Item')
```

## Monitoring & Maintenance

### CloudWatch Metrics
Monitor these key metrics:
- **ConsumedReadCapacityUnits**: Read operations
- **ConsumedWriteCapacityUnits**: Write operations
- **ThrottledRequests**: Rate limiting issues
- **UserErrors**: Client-side errors

### Regular Maintenance Tasks
1. **Monitor table size** and performance
2. **Review access patterns** and optimize queries
3. **Clean up inactive subscribers** periodically
4. **Backup important data** before major changes
5. **Review and update IAM permissions**

### Cost Optimization
- **Use on-demand billing** for variable workloads
- **Implement data archiving** for old records
- **Optimize query patterns** to reduce read/write units
- **Use batch operations** for bulk updates

## Troubleshooting

### Common Issues

#### Access Denied Errors
- **Check IAM permissions**: Ensure Lambda role has DynamoDB access
- **Verify table name**: Ensure table name matches exactly
- **Check region**: Ensure you're accessing the correct region

#### Throttling Issues
- **Review capacity settings**: Consider increasing capacity
- **Optimize queries**: Use batch operations when possible
- **Implement exponential backoff**: For retry logic

#### Data Consistency Issues
- **Use conditional writes**: Prevent overwriting data
- **Implement optimistic locking**: Handle concurrent updates
- **Validate data before writes**: Ensure data integrity

### Debugging Tools
```python
# Enable debug logging
import logging
boto3.set_stream_logger('boto3.resources', logging.DEBUG)

# Check table status
def check_table_status():
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.describe_table(TableName='telegram_subscribers')
    print(f"Table status: {response['Table']['TableStatus']}")
    print(f"Item count: {response['Table']['ItemCount']}")
```

## Performance Optimization

### Best Practices
1. **Use appropriate data types** for keys
2. **Design for single-table access patterns**
3. **Implement proper indexing** for queries
4. **Use batch operations** for bulk data
5. **Monitor and optimize** query performance

### Query Optimization
```python
# Use projection expressions to limit returned data
response = table.scan(
    ProjectionExpression='chat_id, username, active'
)

# Use filter expressions efficiently
response = table.scan(
    FilterExpression='active = :active',
    ExpressionAttributeValues={':active': True}
)
```

## Security Considerations

### Data Protection
- **Encrypt sensitive data** at rest and in transit
- **Use IAM roles** instead of access keys
- **Implement least privilege** access
- **Regular security audits** of permissions

### Access Control
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/telegram_subscribers",
            "Condition": {
                "StringEquals": {
                    "dynamodb:Attributes": [
                        "chat_id",
                        "username",
                        "active"
                    ]
                }
            }
        }
    ]
}
```

## Support

For issues or questions:
- **AWS Support**: Use AWS Support Center
- **Documentation**: [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- **Community**: AWS re:Post DynamoDB forum

---

**Next Steps**: After setting up DynamoDB, integrate it with your Telegram bot and Lambda functions for subscriber management.
