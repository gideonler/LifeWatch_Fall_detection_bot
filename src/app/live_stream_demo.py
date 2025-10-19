"""
Live Webcam Stream → Lambda Sender

This script continuously captures frames from the webcam, combines them into a 
grid image, and sends the image to an AWS Lambda endpoint at regular intervals. 

Workflow:
    1. Capture N frames from webcam at fixed intervals.
    2. Combine captured frames into a single image grid.
    3. Save the grid locally (for debugging/testing).
    4. Send the grid image (base64-encoded) to Lambda Step function.
    5. Log the Lambda response to a local file.
    6. Repeat the process every cycle (e.g., every 30 seconds).

Attributes:
    LAMBDA_URL (str): Direct Lambda Function URL for POST requests.
    CAPTURE_INTERVAL (int): Time in seconds between frame captures.
    FRAME_COUNT (int): Number of frames to capture per cycle.
    CYCLE_INTERVAL (int): Time in seconds between send cycles.
    SAVE_PATH (str): Local path to save the combined image grid.
    SAVE_RESPONSE_LOGS (str): Log file to store Lambda responses.

Functions:
    capture_frames(interval, count):
        Captures a set of frames from the webcam at a specified interval.
    combine_to_grid(frames, grid_size):
        Combines a list of images into a single grid layout.
    send_image_to_lambda(image):
        Sends the image to Lambda via HTTP POST
    log_lambda_response(response):
        Logs the Lambda response locally for record keeping.
    main_loop():
        Runs the continuous capture–combine–send cycle until interrupted.

Example:
    Run the script directly to start the live stream process:
        $ python live_stream_cam.py
"""

import cv2
import time
import requests
import base64
import subprocess
from PIL import Image
import io

from botocore.config import Config
import json

# ===================== CONFIG =====================

# step function lambda url
LAMBDA_URL = "https://eeiao7ouzeqrs2adwzcijtmfda0zqxoi.lambda-url.ap-southeast-1.on.aws/"
CAPTURE_INTERVAL = 3       # seconds between frames
FRAME_COUNT = 10           # number of frames per cycle
CYCLE_INTERVAL = 30        # seconds between each full send cycle

SAVE_PATH = "frames/frame_grid.jpg"
SAVE_RESPONSE_LOGS = 'responses/log.txt'

TIMEOUT_SECONDS = 60

# =================== IMAGE UTILS =====================

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

def capture_frames(interval=3, count=10, cam_index=0):
    """Capture `count` frames from webcam, every `interval` seconds."""

    cap = cv2.VideoCapture(cam_index)
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

# ===================== SEND IMAGE TO LAMBDA =====================

def send_image_to_lambda(image):
    image = resize_image_for_step_function(image)

    buf = io.BytesIO() ## creates in-mem binary stream, file in RAM
    image.save(buf, format="JPEG") ## instead of saving to disk, save to mem
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    
    payload = {
        "image_base64": img_b64
        }

    try:
        print("📤 Sending grid to Lambda...")
        response = requests.post(LAMBDA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        print("✅ Lambda response received.")
        return response.json()
    except Exception as e:
        print(f"❌ Error sending to Lambda URL: {e}")

# ===================== OTHER UTILS =====================

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

def check_devices(): 
    print("\n📸 Checking available camera devices:")
    cmd = ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    print(result.stderr)
# ===================== MAIN LOOP =====================

def main_loop():
    print("🎬 Starting live stream loop...")

    check_devices()
    selected_camera = int(input("Enter camera index to use: "))

    while True:
        start_time = time.time()

        # 1️⃣ Capture frames
        frames = capture_frames(interval=CAPTURE_INTERVAL, count=FRAME_COUNT, cam_index=selected_camera)
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
