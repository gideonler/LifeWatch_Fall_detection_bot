import json
import os
import boto3
import requests
from datetime import datetime

# Environment variables
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
AGENT_ID = os.environ['AGENT_ID']
AGENT_ALIAS_ID = os.environ['AGENT_ALIAS_ID']
REGION = os.environ.get('REGION', 'ap-southeast-1')
TABLE_NAME = os.environ.get("SUBSCRIBERS_TABLE", "telegram_subscribers")



# AWS Resource
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
bedrock_client = boto3.client("bedrock-agent-runtime", region_name=REGION)

def send_telegram_message(chat_id, text):
    """Send plain text message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)


def parse_agent_response(response):
    """Parse the streaming response from invoke_agent"""
    reply_text = ""
    
    try:
        # The 'completion' field contains the EventStream object
        event_stream = response.get('completion')
        
        if event_stream:
            for event in event_stream:
                # Check for chunk with bytes
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        # Decode the bytes to string
                        byte_str = chunk['bytes']
                        # Remove the b'...' wrapper and decode
                        if isinstance(byte_str, str):
                            # It's already a string representation like "b'...'"
                            # Extract content between b' and '
                            text = byte_str.replace("b'", "").replace("'", "")
                        else:
                            # It's actual bytes
                            text = byte_str.decode('utf-8')
                        reply_text += text
                
                # Also check for other event types that might have text
                if 'contentBlock' in event:
                    content = event['contentBlock']
                    if 'text' in content:
                        reply_text += content['text']
    
    except Exception as e:
        print(f"Error parsing response: {e}")
        import traceback
        traceback.print_exc()
    
    print("Extracted reply_text:", reply_text)
    
    # Fix the formatting issue - convert literal \n to actual newlines
    if reply_text:
        reply_text = reply_text.replace('\\n', '\n')  # Convert literal \n to actual newlines
        reply_text = reply_text.replace('\n\n\n', '\n\n')  # Clean up excessive newlines
    
    return reply_text.strip() if reply_text else None

def handle_subscribe(chat_id, username):
    """Add or update subscriber."""
    table.put_item(
        Item={
            "chat_id": str(chat_id),
            "username": username or "",
            "subscribed_at": datetime.utcnow().isoformat(),
            "active": True
        }
    )
    send_telegram_message(chat_id, "✅ You are now subscribed to alerts!")

def handle_unsubscribe(chat_id):
    """Remove subscriber."""
    table.delete_item(Key={"chat_id": str(chat_id)})
    send_telegram_message(chat_id, "❌ You have been unsubscribed.")

def handle_status(chat_id):
    """Check subscription status."""
    res = table.get_item(Key={"chat_id": str(chat_id)})
    if "Item" in res:
        send_telegram_message(chat_id, "📢 You are currently subscribed.")
    else:
        send_telegram_message(chat_id, "🔕 You are not subscribed.")


def lambda_handler(event, context):
    try:
        # Parse Telegram message
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text')
        username = message.get('from', {}).get('username', '')  
        if not text or not chat_id:
            return {"statusCode": 200, "body": "No text found"}

        session_id = str(chat_id)

        # === Handle subscription commands ===
        lowered = text.lower()
        if lowered == "/subscribe":
            handle_subscribe(chat_id, username)
            return {"statusCode": 200, "body": "Subscribed"}
        elif lowered == "/unsubscribe":
            handle_unsubscribe(chat_id)
            return {"statusCode": 200, "body": "Unsubscribed"}
        elif lowered == "/status":
            handle_status(chat_id)
            return {"statusCode": 200, "body": "Status checked"}
        elif lowered == "/start":
            welcome_message = (
                "👋 Welcome to <b>LifeWatch</b>!\n\n"
                "Start by tapping on the bottom left menu and choosing <b>/subscribe</b> "
                "to receive real-time fall alerts.\n\n"
                "You can also chat with me naturally — for example:\n"
                "• <i>How many falls happened today?</i>\n"
                "• <i>Show me recent alerts</i>\n\n"
                "I can help you with:\n"
                "• Counting fall incidents in a specific time period\n"
                "• Summarizing recent fall events\n"
                "• Identifying patterns in fall incidents\n"
                "• Explaining serious fall events (alert level ≥ 2)\n\n"
                "Let's keep your loved ones safe ❤️"
            )
            send_telegram_message(chat_id, welcome_message)
            return {"statusCode": 200, "body": "Start message sent"}
        # Invoke Bedrock Agent
        print(f"Invoking agent with text: {text}")
        response = bedrock_client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=text
        )
        
        print(f"Response type: {type(response)}")
        print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")

        # Parse the streaming response
        reply = parse_agent_response(response)
        print(f"Final reply after parsing: {reply}")
        
        if not reply:
            reply = "Sorry, I couldn't generate a response."

        # Send reply back to Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply})

        print("Telegram message:", text)
        print("Bedrock response:", reply)

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"statusCode": 500, "body": f"Error: {e}"}