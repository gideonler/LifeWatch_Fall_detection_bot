"""
SCRIPT Objective: 
# Live Stream CAM + AUDIO

# Every 30 seconds:
# (1) capture frame + audio 
# (2) create grid + get transcript (AWS Transcribe Job)
# (3) send both as payload to lambda 

## TODO: check which lambda endpoint 
## Current: send to video_invoke_lambda
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

import threading
import sounddevice as sd
import soundfile as sf
import os 
import uuid

from aws_transcribe import transcribe_audio
# ===================== CONFIG =====================
# LAMBDA_URL = "https://eeiao7ouzeqrs2adwzcijtmfda0zqxoi.lambda-url.ap-southeast-1.on.aws/"
## VIDEO INVOKE LAMBDA
AWS_REGION = "ap-southeast-1"
LAMBDA_URL = 'https://abrpnerwsi3dglatgaapzb5qia0ofkqw.lambda-url.ap-southeast-1.on.aws/'

CAPTURE_INTERVAL = 3       # seconds between frames
FRAME_COUNT = 10           # number of frames per cycle
CYCLE_INTERVAL = 30        # seconds between each full send cycle

TIMEOUT_SECONDS = 60

LAMBDA_NAME = 'elderly-home-monitoring-s-LambdasVideoInvokeB03202-zHGWQu2gYAJ1'
lambda_client = boto3.client("lambda", region_name=AWS_REGION, config=Config(connect_timeout=TIMEOUT_SECONDS)) # read_timeout=TIMEOUT_SECONDS, 

IMG_PATH = "frames/frame_grid.jpg"
AUDIO_PATH = "audio/audio_record.wav"
SAVE_RESPONSE_LOGS = 'responses/log.txt'

# Ensure dirs exist
os.makedirs("frames", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("responses", exist_ok=True)
# ===================================================

# ============== AUDIO CAPTURE ======================
def record_audio(duration=15, 
                 samplerate=16000, 
                 filename=AUDIO_PATH):
    """Record audio for `duration` seconds and save as WAV."""
    print(f"🎙️ Recording audio for {duration}s...")

    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait() # wait till recording is finished
    sf.write(filename, data=audio, samplerate=samplerate)
    print(f"💾 Audio saved to {filename}")
    return filename
# ===================================================

# ============== FRAMES CAPTURE ======================
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

# ================== SEND TO LAMBDA =======================

def send_image_to_lambda(image, transcript_text=None):
    buf = io.BytesIO() ## creates in-mem binary stream, file in RAM
    image.save(buf, format="JPEG") ## instead of saving to disk, save to mem
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    payload = {
        "image_base64": img_b64, 
        'transcript': transcript_text or "",
        "metadata": {"source": "python-live-stream"}
        }

    try:
        print("📤 Sending grid + transcript (if any) to Lambda...")
        response = requests.post(LAMBDA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        print("✅ Lambda response received.")
        return response.json()
    except Exception as e:
        print(f"❌ Error sending to Lambda URL: {e}")
        print("⚠️ URL failed, using boto3 fallback...")
        resp = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )
        return json.load(resp["Payload"])
    
# ===================================================

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
    available_cams = []
    for index in range(3):  # test first 3 indices (0–4)
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"  ✅ Camera {index} detected")
            available_cams.append(index)
            cap.release()
        else:
            print(f"  ❌ Camera {index} not found")

    if available_cams:
        print(f"\n🎥 Default camera device index: {available_cams[0]}")
    else:
        print("\n⚠️ No camera devices found.")

    print("\n🎧 Checking available audio devices:")
    print(sd.query_devices())

    # Get default input/output info
    default_input = sd.default.device[0]
    print(f"\n🎙️ Default input device index: {default_input}")
    print("🔍 Using:", sd.query_devices(default_input)["name"])

def main_loop():
    
    print("🎬 Starting live stream loop...")

    # check_devices()

    while True:
        start_time = time.time()
        
        # Parallel audio recording while capturing frames
        duration = CAPTURE_INTERVAL * FRAME_COUNT
        audio_thread = threading.Thread(
            target=record_audio,
            args=(duration, 16000, AUDIO_PATH)
        )
        audio_thread.start()

        # 1️⃣ Capture frames
        frames = capture_frames(interval=CAPTURE_INTERVAL, count=FRAME_COUNT)

        audio_thread.join() # wait for audio to finish

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
        grid.save(IMG_PATH)
        print(f"💾 Saved grid locally as {IMG_PATH}")

        # Transcribe the just-recorded audio
        transcript_text = transcribe_audio(AUDIO_PATH)

        # 4️⃣ Send to Lambda
        result = send_image_to_lambda(grid, transcript_text)
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
