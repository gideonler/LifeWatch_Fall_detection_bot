import streamlit as st
import cv2
import os
import subprocess
from PIL import Image

from live_stream_demo import combine_to_grid, send_image_to_lambda
# ===================== CONFIG =====================
# LAMBDA for step function 
LAMBDA_URL = "https://eeiao7ouzeqrs2adwzcijtmfda0zqxoi.lambda-url.ap-southeast-1.on.aws/"
CAPTURE_INTERVAL = 3
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

# ===================== STREAMLIT =====================

st.title("🎬 DEMO: LifeWatch using Video as inputs")

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
        else:
            st.error("⚠️ Failed to extract or combine frames.")

        # 4️⃣ Send to Lambda
        result = send_image_to_lambda(grid)
        if result:
            st.subheader("🧠 Grid sent to lambda step function")
            st.json(result)
        else: 
            st.error("⚠️ Failed to send to lambda.")
    