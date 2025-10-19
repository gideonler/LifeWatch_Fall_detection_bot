# SCRIPT Objective: 
# Live Stream CAM Script - without streamlit interface
# Calls function every 30s to 
# (1) capture frame 
# (2) create grid 
# (3) send to lambda 

## ISSUE: 500 server error when sending req to lambda 
"""
Live Webcam Stream -> Lambda Sender
- Captures 10 frames (3s apart)
- Combines into grid
- Saves grid locally (for testing)
- Sends to Lambda URL (VideoInvoke) + Event_ID
- Repeats every 30s
"""

import cv2
import time
import requests
import base64
from PIL import Image
import io

import boto3
from botocore.config import Config
import json

# ===================== CONFIG =====================
LAMBDA_URL = "https://eeiao7ouzeqrs2adwzcijtmfda0zqxoi.lambda-url.ap-southeast-1.on.aws/"
# LAMBDA_URL = 'https://abrpnerwsi3dglatgaapzb5qia0ofkqw.lambda-url.ap-southeast-1.on.aws/'
CAPTURE_INTERVAL = 3       # seconds between frames
FRAME_COUNT = 10           # number of frames per cycle
CYCLE_INTERVAL = 30        # seconds between each full send cycle
SAVE_PATH = "frames/frame_grid.jpg"

TIMEOUT_SECONDS = 60
# lambda_client = boto3.client("lambda", region_name="ap-southeast-1", config=Config(connect_timeout=TIMEOUT_SECONDS)) # read_timeout=TIMEOUT_SECONDS, 
# LAMBDA_NAME = 'trigger_step_function'
# LAMBDA_NAME = 'elderly-home-monitoring-s-LambdasVideoInvokeB03202-zHGWQu2gYAJ1'

SAVE_RESPONSE_LOGS = 'responses/log.txt'
# ===================================================

def resize_image_for_step_function(image, max_size_kb=150):
    """Resize image to fit within Step Functions 256KB limit"""
    # Convert to bytes to check size
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    current_size_kb = len(buf.getvalue()) / 1024
    
    if current_size_kb <= max_size_kb:
        return image  # Already small enough
    
    # Calculate resize factor
    resize_factor = (max_size_kb / current_size_kb) ** 0.5
    new_width = int(image.width * resize_factor)
    new_height = int(image.height * resize_factor)
    
    # Resize image
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Try different quality levels if still too big
    for quality in [75, 65, 55, 45]:
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=quality)
        if len(buf.getvalue()) / 1024 <= max_size_kb:
            break
    
    return resized


def capture_frames(interval=3, count=10):
    """Capture `count` frames from webcam, every `interval` seconds."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Unable to access webcam.")
        return []

    frames = []
    print(f"📸 Capturing {count} frames every {interval}s...")

    for i in range(count):
        ret, frame = cap.read()
        if not ret:
            print(f"⚠️ Frame {i+1} failed to capture.")
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame_rgb))
        print(f"✅ Captured frame {i+1}/{count}")
        ## 3s interval between captures
        time.sleep(interval)

    cap.release()
    return frames


def combine_to_grid(frames, grid_size=(2, 5)):
    """Combine list of PIL Images into a grid."""
    if not frames:
        return None
    w, h = frames[0].size
    grid_w = grid_size[1] * w
    grid_h = grid_size[0] * h
    grid = Image.new("RGB", (grid_w, grid_h))

    for idx, img in enumerate(frames):
        x = (idx % grid_size[1]) * w
        y = (idx // grid_size[1]) * h
        grid.paste(img, (x, y))
    return grid


def send_image_to_lambda(image):
    image = resize_image_for_step_function(image)

    buf = io.BytesIO() ## creates in-mem binary stream, file in RAM
    image.save(buf, format="JPEG") ## instead of saving to disk, save to mem
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    
    payload = {
        "image_base64": img_b64
        #"metadata": {"source": "python-live-stream"}
               }

    try:
        print("📤 Sending grid to Lambda...")
        response = requests.post(LAMBDA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        print("✅ Lambda response received.")
        return response.json()
    except Exception as e:
        print(f"❌ Error sending to Lambda URL: {e}")
        # print("⚠️ URL failed, using boto3 fallback...")
        # resp = lambda_client.invoke(
        #     FunctionName=LAMBDA_NAME,
        #     InvocationType="RequestResponse",
        #     Payload=json.dumps(payload)
        # )
        # return json.load(resp["Payload"])
    

def log_lambda_response(response):
    """Append Lambda response (JSON) to local log file."""
    if not response:
        return
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "response": response
    }
    with open(SAVE_RESPONSE_LOGS, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"🗂️ Logged Lambda response to {SAVE_RESPONSE_LOGS}")

def main_loop():
    print("🎬 Starting live stream loop...")
    while True:
        start_time = time.time()

        # 1️⃣ Capture frames
        frames = capture_frames(interval=CAPTURE_INTERVAL, count=FRAME_COUNT)
        if not frames:
            print("⚠️ No frames captured, retrying next cycle.")
            # sleep before retrying to avoid tight retry loops
            time.sleep(CYCLE_INTERVAL)
            continue

        # 2️⃣ Combine into grid
        grid = combine_to_grid(frames)
        if grid is None:
            print("⚠️ Grid creation failed, skipping upload.")
            time.sleep(CYCLE_INTERVAL)
            continue

        # 3️⃣ Save locally
        grid.save(SAVE_PATH)
        print(f"💾 Saved grid locally as {SAVE_PATH}")

        # from PIL import Image
        # # Open image
        # grid = Image.open("test-data/frames_grid.jpg")

        # 4️⃣ Send to Lambda
        result = send_image_to_lambda(grid)
        if result:
            print("🧠 Lambda result:", result)
        else:
            print("⚠️ No response or failed request.")

        # 5️⃣ Wait until next cycle
        elapsed = time.time() - start_time
        wait_time = max(0, CYCLE_INTERVAL - elapsed)
        print(f"⏳ Waiting {wait_time:.1f}s for next cycle...\n")
        time.sleep(wait_time)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n🛑 Stream stopped by user.")
