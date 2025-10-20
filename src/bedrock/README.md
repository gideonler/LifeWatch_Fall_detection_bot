# AWS Bedrock Knowledge Base & Agent Setup Guide

## Overview

This comprehensive guide walks you through setting up AWS Bedrock Knowledge Base and Agent for the elderly fall detection system. The system stores historical event data and provides intelligent analysis through conversational AI.

## Prerequisites

### Required AWS Resources
- **AWS Account** with Bedrock access enabled
- **S3 Bucket**: `elderly-home-monitoring-events`
- **S3 Prefix**: `knowledge-base/` (for storing analysis files)
- **IAM Permissions**: Bedrock, OpenSearch, and S3 access

### Required AWS Services
- Amazon Bedrock (Knowledge Base & Agents)
- Amazon OpenSearch Serverless
- Amazon S3
- IAM (for role management)

## Part 1: Knowledge Base Setup

### Step 1: Navigate to Bedrock Console
1. **Open AWS Bedrock Console**
   - Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
   - Select your region (e.g., `ap-southeast-1`)

2. **Access Knowledge Bases**
   - Click **"Knowledge bases"** in the left sidebar
   - Click **"Create knowledge base"**
   - Choose **"Create with vector store"**

### Step 2: Configure Knowledge Base Details

#### Basic Information
- **Knowledge base name**: `elderly-fall-detection-kb`
- **Description**: `Knowledge base for elderly fall detection system historical events and analysis`
- **IAM role**: 
  - Click **"Create and use a new service role"**
  - Role name: `BedrockKnowledgeBaseRole`
  - This role will have permissions for S3 and OpenSearch

#### Data Source Configuration
- **Data source type**: **Amazon S3**
- **Data source name**: `fall-detection-events`
- **S3 URI**: `s3://elderly-home-monitoring-events/knowledge-base/`
- **File format**: **JSON**
- **Scanning schedule**: **On demand** (for real-time updates)

### Step 3: Configure Vector Store

#### Vector Store Settings
- **Vector store type**: **Amazon OpenSearch Serverless**
- **Collection name**: `elderly-fall-detection-collection`
- **Vector index name**: `fall-detection-index`
- **Vector dimension**: `1024` (for Cohere v3)

#### Embeddings Configuration
- **Embeddings model**: **Cohere Embeddings Model v3**
- **Chunking strategy**: **Fixed size chunking**
- **Chunk size**: `1000` characters
- **Chunk overlap**: `200` characters
- **Maximum chunk size**: `2000` characters

### Step 4: Review and Create
1. **Review Configuration**
   - ✅ Verify knowledge base name and description
   - ✅ Check S3 URI is correct
   - ✅ Confirm OpenSearch settings
   - ✅ Validate IAM role permissions

2. **Create Knowledge Base**
   - Click **"Create knowledge base"**
   - Wait for creation to complete (5-10 minutes)
   - Note down the **Knowledge Base ID** and **Data Source ID**

## Part 2: Bedrock Agent Setup

### Step 1: Create Agent
1. **Navigate to Agents**
   - Go to **"Agents"** in the left sidebar
   - Click **"Create agent"**

2. **Basic Agent Configuration**
   - **Agent name**: `elderly-fall-monitoring-agent`
   - **Description**: `AI agent for analyzing and summarizing elderly fall detection events`
   - **Agent resource role**: Use existing role `AmazonBedrockExecutionRoleForAgents_*`

### Step 2: Configure Agent Instructions

#### System Instructions
Add the following instructions in the **"Instructions for agent"** field:

```
You are an AI assistant specialized in elderly fall monitoring and safety analysis. Your primary role is to help family members and caregivers understand fall events and patterns through conversational analysis.

## Your Capabilities:
- Analyze fall detection events from JSON logs
- Provide summaries and insights about fall patterns
- Answer time-based queries (this week, yesterday, last month)
- Identify concerning trends and alert levels
- Offer contextual information about fall events

## Response Guidelines:
- Use clear, empathetic language suitable for family members
- Provide concise answers unless detailed analysis is requested
- Focus on safety and well-being implications
- Use appropriate emojis for better readability in Telegram

## Data Analysis:
- Count fall events in specific time periods
- Summarize recent falls with timestamps and locations
- Identify patterns (repeated falls, time of day, locations)
- Highlight serious events (alert_level ≥ 2)
- Provide trend analysis and recommendations

## Example Interactions:
- "How many falls happened this week?"
- "Show me the latest fall event details"
- "What's the trend of incidents this month?"
- "Are there any concerning patterns I should know about?"

Always base your analysis on the JSON data from the knowledge base and provide actionable insights for family members and caregivers.
```

### Step 3: Configure Model and Knowledge Base

#### Model Selection
- **Foundation model**: **Amazon Nova Lite** (cost-effective for this use case)
- **Temperature**: `0.3` (balanced creativity and consistency)
- **Max tokens**: `1000`

#### Knowledge Base Integration
1. **Add Knowledge Base**
   - Click **"Add knowledge base"**
   - Select the knowledge base created in Part 1
   - **Knowledge base instruction for agent**:
   ```
   This knowledge base contains JSON logs of detected fall events from an elderly monitoring system. Each entry includes:
   - timestamp: When the event occurred
   - alert_level: Severity (0=normal, 1=concerning, 2=urgent)
   - reason: Brief description of what was detected
   - brief_description: Summary of the event
   - full_description: Detailed analysis
   - location: Where the event occurred (if available)
   
   Use this data to answer questions about fall patterns, recent events, and safety trends.
   ```

### Step 4: Prepare and Test Agent
1. **Prepare Agent**
   - Click **"Prepare"** to initialize the agent
   - Wait for preparation to complete (2-3 minutes)

2. **Test Agent**
   - Use the test interface to verify functionality
   - Test queries:
     - "What can you help me with?"
     - "How many falls occurred this week?"
     - "Show me the latest fall event"
     - "What patterns do you see in recent falls?"

3. **Create Agent Alias**
   - Click **"Create alias"**
   - **Alias name**: `fall-monitoring-v1`
   - **Description**: `Production version of fall monitoring agent`

## Part 3: Integration & Testing

### Environment Variables
Add these to your Lambda functions:

```bash
# Knowledge Base Configuration
KNOWLEDGE_BASE_ID=your-knowledge-base-id
DATA_SOURCE_ID=your-data-source-id
COLLECTION_ID=your-collection-id

# Agent Configuration
AGENT_ID=your-agent-id
AGENT_ALIAS_ID=your-alias-id
```


## Part 4: Data Format & Structure

### Expected JSON Format
Ensure your analysis files in S3 follow this structure:

```json
{
    "timestamp": "20241020-143052",
    "image_key": "detected-images/datestr=20241020/143052.jpg",
    "alert_level": 2,
    "reason": "Fall detected - person lying on floor",
    "brief_description": "Elderly person fell in living room",
    "full_description": "Detailed analysis of the fall event with context and recommendations",
    "location": "living room",
    "model_used": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "confidence_score": 0.85,
    "created_at": "2024-10-20T14:30:52Z"
}
```

## 🛠️ Troubleshooting

### Common Issues

#### Knowledge Base Not Retrieving Data
- **Check S3 permissions**: Ensure Bedrock can access the bucket
- **Verify file format**: Files must be valid JSON
- **Check ingestion status**: Look for failed ingestion jobs
- **Review chunking settings**: Adjust chunk size if needed

#### Agent Not Responding
- **Check agent status**: Ensure agent is prepared and ready
- **Verify knowledge base connection**: Test knowledge base separately
- **Review IAM permissions**: Ensure agent has access to knowledge base
- **Check model availability**: Verify model is available in your region

#### Data Not Updating
- **Trigger ingestion**: Manually start ingestion job after adding new data
- **Check S3 events**: Ensure new files are being detected
- **Review scanning schedule**: Set to "On demand" for real-time updates

### Monitoring & Logs
- **CloudWatch Logs**: Monitor agent and knowledge base performance
- **Bedrock Console**: Check agent and knowledge base status
- **S3 Metrics**: Monitor data source updates
- **OpenSearch Metrics**: Track vector search performance

## 💰 Cost Optimization

### Knowledge Base Costs
- **Chunk size**: Larger chunks reduce processing costs
- **Overlap**: Lower overlap reduces duplicate processing
- **Retrieval**: Limit number of results to reduce costs
- **Storage**: Use S3 lifecycle policies for old data

### Agent Costs
- **Model selection**: Use appropriate model for your use case
- **Token limits**: Set reasonable max token limits
- **Session management**: Implement proper session cleanup

## 🔄 Maintenance

### Regular Tasks
1. **Monitor ingestion jobs** for failures
2. **Review agent performance** and user feedback
3. **Update knowledge base** with new data formats
4. **Optimize chunking strategy** based on data patterns
5. **Clean up old sessions** and temporary data

### Updates
- **Model updates**: Test new model versions before deploying
- **Knowledge base updates**: Re-index when data structure changes
- **Agent improvements**: Update instructions based on user feedback

