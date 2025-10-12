import boto3
import json
import base64
from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Dict, Any

BUCKET = "elderly-home-monitoring-images"
PREFIX = "detected-images/datestr=20251012/"
KNOWLEDGE_BASE_PREFIX = "knowledge-base/"

# Initialize clients
bedrock_runtime = boto3.client("bedrock-runtime", region_name="ap-southeast-1")
s3 = boto3.client("s3")

# Model ID
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# Enhanced system prompt with knowledge base context
SYSTEM_PROMPT = """
You are an AI language model assistant specialized in monitoring people in their living spaces. Be it out doors or in doors. 

You are to watch for any potentially concerning events. These include falls, medical emergencies, unusual behavior, or safety concerns that require immediate attention.

I have attached an image from a camera feed. Look for signs of distress, falls, medical emergencies, or any situation where the person might need help.

You must:
1. Identify **any person** in the image — even small or distant figures.
2. Examine **posture, body angle, and ground contact** to detect falls or unusual positions.
3. Notice **unusual stillness or lying posture** compared to surroundings (e.g., on the floor, couch edge, or bathroom).
4. Consider **context clues** — body near furniture, motion blur suggesting collapse, limbs in unnatural orientation.
5. Do not ignore small figures — zoom in mentally and judge whether they may have fallen.

You will also be provided with context from previous similar events to help you make better decisions.

Your job is to determine the severity level.
Severity levels can take on the following values:
    0: No issues detected requiring immediate attention
    1: Possible issue detected requiring attention (soft alert)
    2: Issue requiring immediate action detected (high alert)

Please respond with the following JSON output format:
{"alert_level":int,
"reason":string,
"log_file_name":string,
"brief_description": string,
"full_description": string}

Do not add any preamble or explanation - your correctly formatted JSON response will trigger the appropriate alerts.
"""

def create_multimodal_prompt(image_data: bytes, text: str, content_type: str, system_prompt: str = None, max_tokens: int = 1000, temperature: float = 0.5, model_id: str = MODEL_ID):
    """Create a multimodal prompt structure - handles both Claude and Mistral formats"""
    
    if "anthropic" in model_id.lower():
        prompt = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64.b64encode(image_data).decode("utf-8"),
                            },
                        },
                        {"type": "text", "text": text},
                    ],
                }
            ],
        }
        if system_prompt:
            prompt["system"] = system_prompt
    else:
        prompt = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64.b64encode(image_data).decode("utf-8"),
                            },
                        },
                        {"type": "text", "text": text},
                    ],
                }
            ],
        }
        if system_prompt:
            prompt["system"] = system_prompt
    
    return prompt

def invoke_bedrock_model(prompt, model_id: str = MODEL_ID, max_tokens: int = 1000, temperature: float = 0.5):
    """Invoke Bedrock model with given prompt and return the response text"""
    try:
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(prompt),
            contentType="application/json",
            accept="application/json",
        )
        
        response_body = json.loads(response.get("body").read())
        print(f"Bedrock response: {response_body}")
        
        if "content" in response_body and len(response_body["content"]) > 0:
            analysis = response_body["content"][0]["text"]
        else:
            analysis = response_body.get("text", str(response_body))
        
        print(f"Bedrock analysis: {analysis}")
        
        return analysis
        
    except Exception as e:
        print(f"Error invoking Bedrock: {e}")
        raise

def get_historical_events(hours_back: int = 24) -> List[Dict[str, Any]]:
    """Retrieve historical events from the knowledge base"""
    try:
        # Get events from the last N hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        response = s3.list_objects_v2(
            Bucket=BUCKET, 
            Prefix=KNOWLEDGE_BASE_PREFIX
        )
        
        if "Contents" not in response:
            return []
        
        events = []
        for obj in response["Contents"]:
            if obj["Key"].endswith("_analysis.json"):
                try:
                    # Get the object
                    file_response = s3.get_object(Bucket=BUCKET, Key=obj["Key"])
                    event_data = json.loads(file_response["Body"].read())
                    
                    # Parse timestamp and filter by time
                    if "timestamp" in event_data:
                        event_time = datetime.strptime(event_data["timestamp"], "%Y%m%d-%H%M%S")
                        if event_time.replace(tzinfo=timezone.utc) >= cutoff_time:
                            events.append(event_data)
                except Exception as e:
                    print(f"Error reading event {obj['Key']}: {e}")
                    continue
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return events[:10]  # Return last 10 events
        
    except Exception as e:
        print(f"Error retrieving historical events: {e}")
        return []

def format_context_for_prompt(events: List[Dict[str, Any]]) -> str:
    """Format historical events into context for the prompt"""
    if not events:
        return "No previous events found in the knowledge base."
    
    context = "Previous events from knowledge base:\n"
    for i, event in enumerate(events, 1):
        context += f"{i}. Time: {event.get('timestamp', 'Unknown')}\n"
        context += f"   Alert Level: {event.get('alert_level', 'Unknown')}\n"
        context += f"   Reason: {event.get('reason', 'Unknown')}\n"
        context += f"   Brief: {event.get('brief_description', 'Unknown')}\n"
        context += "\n"
    
    return context

def save_to_knowledge_base(analysis_result: Dict[str, Any], image_key: str):
    """Save analysis result to knowledge base"""
    try:
        # Create knowledge base entry
        kb_entry = {
            "timestamp": analysis_result.get("timestamp"),
            "image_key": image_key,
            "alert_level": analysis_result.get("alert_level", 0),
            "reason": analysis_result.get("reason", ""),
            "log_file_name": analysis_result.get("log_file_name", ""),
            "brief_description": analysis_result.get("brief_description", ""),
            "full_description": analysis_result.get("full_description", ""),
            "model_used": analysis_result.get("model_used", MODEL_ID),
            "knowledge_base_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to knowledge base
        kb_key = f"{KNOWLEDGE_BASE_PREFIX}{analysis_result.get('timestamp', 'unknown')}_{analysis_result.get('log_file_name', 'event')}.json"
        
        s3.put_object(
            Bucket=BUCKET,
            Key=kb_key,
            Body=json.dumps(kb_entry, indent=2),
            ContentType="application/json"
        )
        
        print(f"Saved to knowledge base: s3://{BUCKET}/{kb_key}")
        
    except Exception as e:
        print(f"Error saving to knowledge base: {e}")

def lambda_handler(event, context):
    # 1️⃣ List objects in S3
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    if "Contents" not in response:
        return {"statusCode": 404, "body": "No files found."}

    jpg_files = [obj for obj in response["Contents"] if obj["Key"].lower().endswith('.jpg')]
    if not jpg_files:
        return {"statusCode": 404, "body": "No JPG images found."}

    # 2️⃣ Pick the latest image
    latest_file = max(jpg_files, key=lambda x: x["LastModified"])
    key = latest_file["Key"]
    print(f"Analyzing frame: s3://{BUCKET}/{key}")

    # 3️⃣ Get historical context from knowledge base
    print("Retrieving historical events...")
    historical_events = get_historical_events(hours_back=24)  # Last 24 hours
    context_text = format_context_for_prompt(historical_events)
    print(f"Found {len(historical_events)} historical events")

    # 4️⃣ Download image data directly
    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        image_data = response["Body"].read()
        content_type = response.get("ContentType", "image/jpeg")
        print(f"Downloaded image: {len(image_data)} bytes, content type: {content_type}")
    except Exception as e:
        return {"statusCode": 500, "body": f"Failed to download image: {e}"}

    # 5️⃣ Create enhanced analysis prompt with knowledge base context
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    monitoring_instruction = "Monitor for falls, medical emergencies, or unusual behavior in person's living space"
    
    agent_prompt = f"""
    Analyze the provided image. {monitoring_instruction}
    Use the timestamp '{timestamp}' for log file name.
    
    CONTEXT FROM PREVIOUS EVENTS:
    {context_text}
    
    Use this historical context to help determine if the current situation is normal, concerning, or requires immediate attention. Consider patterns, frequency, and severity of similar past events.
    
    If no concerning activity is detected, set 'alert_level':0 and all other fields to 'no concerning activity detected' and explain why
    Please return your valid formatted JSON (confirm no double quotes appear in description text):
    """

    # 6️⃣ Create multimodal prompt
    prompt = create_multimodal_prompt(
        image_data=image_data,
        text=agent_prompt,
        content_type=content_type,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.5,
        model_id=MODEL_ID
    )

    # 7️⃣ Invoke Bedrock with knowledge base context
    try:
        analysis_result = invoke_bedrock_model(
            prompt=prompt, 
            model_id=MODEL_ID
        )
        
        # Parse JSON from response
        final_text = analysis_result.strip()
        if final_text.startswith("```json"):
            final_text = final_text.split("```json")[1].split("```")[0].strip()
        
        try:
            report = json.loads(final_text)
            # Add metadata
            report["timestamp"] = timestamp
            report["image_key"] = key
            report["model_used"] = MODEL_ID
            report["historical_context_used"] = len(historical_events)
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Bedrock response as JSON: {e}")
            report = {
                "timestamp": timestamp,
                "image_key": key,
                "alert_level": 0,
                "reason": "JSON parsing failed",
                "log_file_name": f"{timestamp}_parsing_error.json",
                "brief_description": "Failed to parse AI response",
                "full_description": f"Raw response: {final_text}",
                "model_used": MODEL_ID,
                "historical_context_used": len(historical_events)
            }

    except Exception as e:
        print(f"Bedrock invocation failed: {e}")
        report = {
            "timestamp": timestamp,
            "image_key": key,
            "alert_level": 0,
            "reason": "Bedrock invocation failed",
            "log_file_name": f"{timestamp}_invocation_error.json",
            "brief_description": "AI analysis failed",
            "full_description": f"Error: {str(e)}",
            "model_used": MODEL_ID,
            "historical_context_used": len(historical_events)
        }

    # 8️⃣ Save analysis to regular location
    output_key = key.replace(".jpg", "_analysis.json")
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=output_key,
            Body=json.dumps(report, indent=2),
            ContentType="application/json"
        )
        print(f"Saved analysis to s3://{BUCKET}/{output_key}")
    except Exception as e:
        print(f"Failed to save to S3: {e}")

    # 9️⃣ Save to knowledge base for future context
    save_to_knowledge_base(report, key)

    print("Final Analysis Report:", json.dumps(report, indent=2))
    return {
        "statusCode": 200,
        "body": json.dumps(report)
    }
