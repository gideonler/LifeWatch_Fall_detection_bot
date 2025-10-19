import streamlit as st
import cv2
import os
import subprocess
from PIL import Image
import io
import base64
import requests

# ===================== CONFIG =====================

LAMBDA_URL = "https://eeiao7ouzeqrs2adwzcijtmfda0zqxoi.lambda-url.ap-southeast-1.on.aws/"
CAPTURE_INTERVAL = 2
FRAME_COUNT = 10
MAX_SIZE_KB = 150
TIMEOUT_SECONDS = 30

# ===================== VID UTILS =====================

def download_youtube_video(url: str, filename: str) -> str:
    """
    Download YouTube video as MP4 using yt-dlp.
    """
    cmd = ["yt-dlp", "-f", "mp4", "--force-overwrites", "-o", filename, url]
    subprocess.run(cmd, check=True)
    print(f"Downloaded video: {filename}")
    return os.path.abspath(filename)

# ===================== IMG UTILS =====================

def resize_image_for_step_function(image, max_size_kb=150):
    """Resize image to fit within Step Functions 256KB limit."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    current_size_kb = len(buf.getvalue()) / 1024
    if current_size_kb <= max_size_kb:
        return image
    resize_factor = (max_size_kb / current_size_kb) ** 0.5
    new_width = int(image.width * resize_factor)
    new_height = int(image.height * resize_factor)
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    for quality in [75, 65, 55, 45]:
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=quality)
        if len(buf.getvalue()) / 1024 <= max_size_kb:
            break
    return resized

def extract_frames(video_path, interval=3, count=10):
    """Extract `count` frames from video every `interval` seconds."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    print(f"🎥 Duration: {duration:.2f}s, FPS: {fps:.1f}")

    for i in range(count):
        cap.set(cv2.CAP_PROP_POS_MSEC, i * interval * 1000)
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame_rgb))
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

# ===================== SEND TO LAMBDA =====================

def send_image_to_lambda(image):
    image = resize_image_for_step_function(image)
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    payload = {"image_base64": img_b64}

    try:
        st.info("📤 Sending image to Lambda...")
        response = requests.post(LAMBDA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        st.success("✅ Lambda response received.")
        return response.json()
    except Exception as e:
        st.error(f"❌ Error sending to Lambda: {e}")
        return None

# ===================== STREAMLIT =====================

st.title("🎬 DEMO: Video Frame Capture + Lambda Processing")

VIDEO_SAVE_PATH = 'test-data/test_video.mp4'
FRAME_SAVE_PATH = 'frames/output_frames_grid.jpg'

# 1️⃣ YouTube URL input
default_url = 'https://www.youtube.com/watch?v=3-dvsT8pqbQ'

youtube_url = st.text_input("Enter YouTube Video URL:", default_url)

if "youtube.com/shorts/" in youtube_url:
    video_id = youtube_url.split("shorts/")[-1].split("?")[0]
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

# 2️⃣ Display YouTube video
# Show Default demo video: 
if youtube_url == 'https://www.youtube.com/watch?v=3-dvsT8pqbQ': 
    st.video(VIDEO_SAVE_PATH)
else: 
    st.video(youtube_url)

# 3️⃣ Process button
if st.button("📥 Download & Process Video"):
    with st.spinner("Downloading video..."):
        video_path = download_youtube_video(youtube_url, filename=VIDEO_SAVE_PATH)

    st.success(f"✅ Video downloaded successfully at {video_path}")

    # 2️⃣ Display downloaded video
    st.video(video_path)   

    with st.spinner("Extracting frames..."):
        frames = extract_frames(video_path=video_path, interval=CAPTURE_INTERVAL, count=FRAME_COUNT)
        grid = combine_to_grid(frames)
        if grid:
            st.image(grid, caption="🎞️ Combined Frame Grid", use_container_width=True)

            grid.save(FRAME_SAVE_PATH, format="JPEG", quality=85, optimize=True)
            print(f"Grid image saved at {FRAME_SAVE_PATH} (size: {os.path.getsize(FRAME_SAVE_PATH)/1024:.1f} KB)")
            
            # 4️⃣ Send to Lambda
            result = send_image_to_lambda(grid)
            if result:
                st.subheader("🧠 Lambda Result")
                st.json(result)
        else:
            st.error("⚠️ Failed to extract or combine frames.")
