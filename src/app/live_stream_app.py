import streamlit as st
import cv2
import time
import requests
# import boto3
import base64
from PIL import Image
import io

st.title("🎥 Webcam Capture + Lambda Upload")

# AWS_REGION = "ap-southeast-2"  # 🔧 change to your region
# LAMBDA_NAME = "video-invoke-lambda"  # 🔧 change to your Lambda name

# # Initialize boto3 Lambda client
# lambda_client = boto3.client("lambda", region_name=AWS_REGION)

LAMBDA_URL = "https://eeiao7ouzeqrs2adwzcijtmfda0zqxoi.lambda-url.ap-southeast-1.on.aws/"

def capture_frames(interval=3, count=10):
    """Capture `count` frames from webcam, every `interval` seconds."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Unable to access webcam.")
        return []

    frames = []
    st.write("📸 Capturing frames...")
    progress = st.progress(0)

    for i in range(count):
        ret, frame = cap.read()
        if not ret:
            st.warning(f"⚠️ Frame {i+1} failed.")
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame_rgb))
        progress.progress((i + 1) / count)
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

def send_image_to_lambda_url(image: Image.Image):
    """Send image grid to Lambda function URL."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    payload = {
        "image_base64": img_b64,
        "metadata": {"source": "streamlit-webcam"}
    }

    try:
        response = requests.post(LAMBDA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error sending to Lambda: {e}")
        return None

# # --- UI ---
st.write("Click below to start webcam capture.")
if st.button("Start Capture"):
    with st.spinner("Activating webcam..."):
        frames = capture_frames(interval=3, count=4)
    if frames:
        grid = combine_to_grid(frames)
        if grid:
            st.image(grid, caption="🖼️ Combined Frame Grid", use_container_width=True)
            grid.save("frame_grid.jpg")
            st.success("✅ Saved as frame_grid.jpg")
            st.info("upload to lambda")
            result = send_image_to_lambda_url(grid)
            print(result)
        if result:
            st.success("✅ Uploaded successfully!")
            st.json(result)
