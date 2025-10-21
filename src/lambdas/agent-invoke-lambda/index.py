import boto3
import json
import base64
from datetime import datetime, timezone, timedelta, date
import uuid
from typing import List, Dict, Any
import os
import requests

# ====== Config ======
BUCKET = "elderly-home-monitoring-images"
EVENTS_BUCKET = os.environ['EVENTS_BUCKET']
PREFIX = f"detected-images/datestr={date.today().strftime('%Y%m%d')}/"
KNOWLEDGE_BASE_PREFIX = "knowledge-base/"
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

# ====== Initialize clients ======
bedrock_runtime = boto3.client("bedrock-runtime", region_name="ap-southeast-1")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# ====== Bedrock model ID ======
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# ====== System prompt ======
SYSTEM_PROMPT = """
You are an AI assistant specialized in monitoring people in their living spaces, both indoors and outdoors. 
Your goal is to identify whether the person in view is safe, relaxed, or in potential distress.

You are to watch for any potentially concerning events. These include falls, medical emergencies, unusual behavior, or safety concerns that require immediate attention.

An image from a camera feed has been attached. Analyze the situation carefully.

You must:
1. Identify **any person** in the image — even small or distant figures.
2. Examine **posture, body angle, and ground contact** to detect falls or unusual positions.
3. Assess **facial expressions, body tension, and comfort cues** — a relaxed face and natural posture usually indicate the person is resting or chilling, **not injured**.
4. Detect **pain, discomfort, confusion, or unconsciousness** through facial expression, limb stiffness, or unnatural positioning.
5. Consider **context clues** — such as being on a bed, couch, or yoga mat (normal) versus on the hard floor (potential fall).
6. Distinguish between **intentional lying down** (resting, sleeping, watching TV) and **accidental lying down** (collapse, slumped, awkward limb positions).
7. Do not ignore small figures — zoom in mentally and judge whether they may have fallen.

You will also be provided with context from previous similar events to help you make better decisions.

Your job is to determine the severity level.
Severity levels can take on the following values:
    0: No issues detected (normal or relaxed posture)
    1: Possible issue detected requiring attention (soft alert, e.g., uncertain posture or mild concern)
    2: Issue requiring immediate action detected (high alert — fall, unconsciousness, visible distress)

When describing the event, given a concise description and use the tone and wording you use as if speaking to a family member of the person in the photo.

Please respond with the following JSON output format:
{
  "alert_level": int,
  "reason": string,
  "log_file_name": string,
  "brief_description": string,
  "full_description": string
}

Do not add any preamble or explanation — your correctly formatted JSON response will trigger the appropriate alerts.
"""

# ====== Telegram helpers ======
def get_all_subscribers() -> List[str]:
    table = dynamodb.Table("telegram_subscribers")
    response = table.scan()
    return [item["chat_id"] for item in response.get("Items", [])]

def send_telegram_message_to(chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    response.raise_for_status()

def broadcast_telegram_message(text: str):
    chat_ids = get_all_subscribers()
    for chat_id in chat_ids:
        try:
            send_telegram_message_to(chat_id, text)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

def trigger_kb_sync():
    try:
        kb_id = os.environ.get("KNOWLEDGE_BASE_ID")
        ds_id = os.environ.get("DATA_SOURCE_ID")
        if not kb_id or not ds_id:
            print("Knowledge Base or Data Source ID not set; skipping sync.")
            return
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        print(f"Triggered Bedrock knowledge base sync: {response['ingestionJob']['ingestionJobId']}")
    except Exception as e:
        print(f"Failed to trigger knowledge base sync: {e}")


# ====== Bedrock helpers ======
def create_multimodal_prompt(image_data: bytes, text: str, content_type: str, system_prompt: str = None, max_tokens: int = 1000, temperature: float = 0.5, model_id: str = MODEL_ID):
    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": base64.b64encode(image_data).decode("utf-8")}},
                    {"type": "text", "text": text},
                ],
            }
        ],
    }
    if system_prompt:
        prompt["system"] = system_prompt
    return prompt

def invoke_bedrock_model(prompt, model_id: str = MODEL_ID):
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(prompt),
            contentType="application/json",
            accept="application/json",
        )
        response_body = json.loads(response.get("body").read())
        if "content" in response_body and len(response_body["content"]) > 0:
            return response_body["content"][0]["text"]
        return response_body.get("text", str(response_body))
    except Exception as e:
        print(f"Error invoking Bedrock: {e}")
        raise

# ====== Knowledge base helpers ======
def get_historical_events(hours_back: int = 24) -> List[Dict[str, Any]]:
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    try:
        response = s3.list_objects_v2(Bucket=EVENTS_BUCKET, Prefix=KNOWLEDGE_BASE_PREFIX)
        if "Contents" not in response:
            return []

        events = []
        for obj in response["Contents"]:
            if obj["Key"].endswith("_analysis.json"):
                try:
                    file_response = s3.get_object(Bucket=EVENTS_BUCKET, Key=obj["Key"])
                    event_data = json.loads(file_response["Body"].read())
                    if "timestamp" in event_data:
                        event_time = datetime.strptime(event_data["timestamp"], "%Y%m%d-%H%M%S")
                        if event_time.replace(tzinfo=timezone.utc) >= cutoff_time:
                            events.append(event_data)
                except Exception as e:
                    print(f"Error reading event {obj['Key']}: {e}")
                    continue
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return events[:10]
    except Exception as e:
        print(f"Error retrieving historical events: {e}")
        return []

def format_context_for_prompt(events: List[Dict[str, Any]]) -> str:
    if not events:
        return "No previous events found in the knowledge base."
    context = "Previous events from knowledge base:\n"
    for i, event in enumerate(events, 1):
        context += f"{i}. Time: {event.get('timestamp', 'Unknown')}\n"
        context += f"   Alert Level: {event.get('alert_level', 'Unknown')}\n"
        context += f"   Reason: {event.get('reason', 'Unknown')}\n"
        context += f"   Brief: {event.get('brief_description', 'Unknown')}\n\n"
    return context

def save_to_knowledge_base(analysis_result: Dict[str, Any], image_key: str):
    try:
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
        kb_key = f"{KNOWLEDGE_BASE_PREFIX}{analysis_result.get('timestamp', 'unknown')}_{analysis_result.get('log_file_name', 'event')}.json"
        s3.put_object(
            Bucket=EVENTS_BUCKET,
            Key=kb_key,
            Body=json.dumps(kb_entry, indent=2),
            ContentType="application/json"
        )
        print(f"Saved to knowledge base: s3://{BUCKET}/{kb_key}")
    except Exception as e:
        print(f"Error saving to knowledge base: {e}")

# ====== Lambda handler ======
def lambda_handler(event, context):
    # 1️⃣ List images
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    if "Contents" not in response:
        return {"statusCode": 404, "body": "No files found."}
    jpg_files = [obj for obj in response["Contents"] if obj["Key"].lower().endswith('.jpg')]
    if not jpg_files:
        return {"statusCode": 404, "body": "No JPG images found."}
    latest_file = max(jpg_files, key=lambda x: x["LastModified"])
    key = latest_file["Key"]
    print(f"Analyzing frame: s3://{BUCKET}/{key}")

    # 2️⃣ Historical context
    historical_events = get_historical_events(hours_back=24)
    context_text = format_context_for_prompt(historical_events)

    # 3️⃣ Download image
    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        image_data = response["Body"].read()
        content_type = response.get("ContentType", "image/jpeg")
    except Exception as e:
        return {"statusCode": 500, "body": f"Failed to download image: {e}"}

    # 4️⃣ Prompt
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    monitoring_instruction = "Monitor for falls, medical emergencies, or unusual behavior in person's living space"
    agent_prompt = f"""
    Analyze the provided image. {monitoring_instruction}
    Use the timestamp '{timestamp}' for log file name.
    
    CONTEXT FROM PREVIOUS EVENTS:
    {context_text}
    
    If no concerning activity is detected, set 'alert_level':0 and all other fields to 'no concerning activity detected' and explain why
    Please return your valid formatted JSON (confirm no double quotes appear in description text):
    """

    prompt = create_multimodal_prompt(
        image_data=image_data,
        text=agent_prompt,
        content_type=content_type,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.5,
        model_id=MODEL_ID
    )

    # 5️⃣ Bedrock analysis
    try:
        analysis_result = invoke_bedrock_model(prompt, model_id=MODEL_ID)
        final_text = analysis_result.strip()
        if final_text.startswith("```json"):
            final_text = final_text.split("```json")[1].split("```")[0].strip()
        try:
            report = json.loads(final_text)
            report["timestamp"] = timestamp
            report["image_key"] = key
            report["model_used"] = MODEL_ID
            report["historical_context_used"] = len(historical_events)
        except json.JSONDecodeError:
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

    # 6️⃣ Send Telegram alert to all subscribers
    try:
        if int(report["alert_level"]) >= 2:
            presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET, 'Key': key}, ExpiresIn=3600)
            dt_obj = datetime.strptime(report.get('timestamp', "N/A"), "%Y%m%d-%H%M%S")
            readable_timestamp = dt_obj.strftime("%d %b %Y, %H:%M:%S") if dt_obj else "N/A"
            alert_emoji = "🚨" if int(report["alert_level"]) == 2 else "⚠️"
            message = (
                f"{alert_emoji} <b>ALERT DETECTED</b>\n\n"
                f"<b>🕒 Time:</b> {readable_timestamp}\n"
                f"<b>💬 Reason:</b> {report.get('reason', 'N/A')}\n\n"
                f"<b>📝 Summary:</b> {report.get('brief_description', 'N/A')}\n\n"
                f"<b>📖 Full Description:</b>\n<i>{report.get('full_description', 'N/A')}</i>\n\n"
                f"<b>🖼️ Image:</b> <a href=\"{presigned_url}\">View Frame</a>"
            )
            broadcast_telegram_message(message)
            print("Alert sent to all Telegram subscribers")
    except Exception as e:
        print(f"Failed to send alert to Telegram: {e}")

    # 7️⃣ Save analysis to S3
    output_key = key.replace(".jpg", "_analysis.json")
    try:
        s3.put_object(Bucket=EVENTS_BUCKET, Key=output_key, Body=json.dumps(report, indent=2), ContentType="application/json")
    except Exception as e:
        print(f"Failed to save to S3: {e}")

    # 8️⃣ Save to knowledge base
    save_to_knowledge_base(report, key)

    # 9️⃣ Trigger Bedrock knowledge base sync
    trigger_kb_sync()
    print("Final Analysis Report:", json.dumps(report, indent=2))
    return {"statusCode": 200, "body": json.dumps(report)}
