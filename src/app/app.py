# TODO decide on tech stack of app (streamlit?)
# App should provide interface for user to configure email and phone number to send alerts
# App should allow user to customise prompt/ scenarios to monitor (?)
# App should provide interface to interact with agent through voice

## 
import subprocess
import os
import ffmpeg
import boto3
import json
import base64
from PIL import Image
import uuid
import time 
import streamlit as st

# ---------- Step 1: Download YouTube video ----------
def download_youtube_video(url: str, filename: str = "sample.mp4") -> str:
    cmd = ["yt-dlp", "-f", "mp4", "-o", filename, url]
    subprocess.run(cmd, check=True)
    print(f"Downloaded video: {filename}")
    return os.path.abspath(filename)

# ---------- Step 2: Extract audio ----------
def extract_audio(video_path: str, audio_filename: str = "sample_audio.wav") -> str:
    audio_path = os.path.splitext(audio_filename)[0] + ".wav"
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, format="wav", acodec="pcm_s16le", ac=1, ar="16000")
        .overwrite_output()
        .run()
    )
    print(f"Extracted audio: {audio_path}")
    return os.path.abspath(audio_path)


# ---------- Step 3: Extract 10 frames & concatenate ----------
def extract_frames(video_path: str, num_frames: int = 10, out_dir: str = "frames") -> list:
    """
    Extract exactly `num_frames` evenly spaced frames from video.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Get video duration using ffmpeg.probe
    probe = ffmpeg.probe(video_path)
    duration = float(probe['format']['duration'])
    step = duration / num_frames
    

    frame_paths = []
    for i in range(num_frames):
        timestamp = i * step
        frame_file = os.path.join(out_dir, f"frame_{i}.jpg")
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .output(frame_file, vframes=1)
            .overwrite_output()
            .run(quiet=True)
        )
        frame_paths.append(frame_file)

    print(f"Extracted {len(frame_paths)} frames")
    return frame_paths

def create_image_grid(frame_paths, output_path="grid_image.jpg", grid_size=(5, 2), max_width=1024):
    images = [Image.open(p) for p in frame_paths]
    w, h = images[0].size
    grid_w, grid_h = grid_size

    grid_img = Image.new("RGB", (w * grid_w, h * grid_h), color=(255, 255, 255))

    for idx, img in enumerate(images):
        x = (idx % grid_w) * w
        y = (idx // grid_w) * h
        grid_img.paste(img, (x, y))

    # Resize to max_width while keeping aspect ratio
    if grid_img.width > max_width:
        aspect_ratio = grid_img.height / grid_img.width
        new_height = int(max_width * aspect_ratio)
        grid_img = grid_img.resize((max_width, new_height))

    grid_img.save(output_path, format="JPEG", quality=85, optimize=True)
    print(f"Grid image saved at {output_path} (size: {os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


# ---------- TRANSCRIBE ----------
def transcribe_audio(audio_path: str, bucket: str, region="us-east-1"):
    s3 = boto3.client("s3", region_name=region)
    transcribe = boto3.client("transcribe", region_name=region)

    key = f"audio/{uuid.uuid4()}.wav"
    s3.upload_file(audio_path, bucket, key)
    s3_uri = f"s3://{bucket}/{key}"

    job_name = f"job-{uuid.uuid4()}"
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": s3_uri},
        MediaFormat="wav",
        LanguageCode="en-US",
        OutputBucketName=bucket,
    )

    print("⏳ Waiting for transcription to complete...")
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(5)

    if status["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
        raise RuntimeError("❌ Transcription failed")

    transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    print(f"✅ Transcript ready at {transcript_uri}")

    # fetch w boto
    s3 = boto3.client("s3")
    bucket = "test-aws-agent-141516"
    key = "job-c16e0f44-0790-4c04-8e72-0f430aae1a0b.json"

    obj = s3.get_object(Bucket=bucket, Key=key)
    print('obj----- ', obj)
    transcript_json = json.loads(obj["Body"].read())
    print('transcript------ ', transcript_json)
    transcript_text = transcript_json["results"]["transcripts"][0]["transcript"]

    return transcript_text



# ---------- Step 5: Feed image to Bedrock multimodal model ----------

def send_to_bedrock(image_path: str, transcript: str, prompt: str = "What is happening in these video frames?"):
    """
    Send the grid image to a Bedrock multimodal model.
    """
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,  
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{prompt}\n\nTranscript:\n{transcript}"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.b64encode(image_bytes).decode("utf-8"),
                        },
                    },
                ],
            }
        ],
    }

    response = client.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=json.dumps(body),
        contentType="application/json",
    )

    result = json.loads(response["body"].read())
    print("Bedrock response:\n", result)
    return result

# =========================
# Streamlit UI
# =========================

st.title("🎥 Video Safety Monitoring Agent")

video_file = st.file_uploader("Upload a video", type=["mp4", "mov", "avi"])

st.video(video_file)

# bucket_name = st.text_input("Enter S3 Bucket Name for Transcribe")
bucket_name = "test-aws-agent-141516"

prompt_input = st.text_area(
    "Prompt for Bedrock Agent",
    value=(
        "You are a safety-monitoring assistant. Analyze the video frames and transcript "
        "for safety and unusual activities.\n\n"
        "Return ONLY JSON in format:\n"
        "{\n"
        '  "alert_level": 0|1|2,\n'
        '  "reason": "...",\n'
        '  "datetime": "ISO8601 timestamp"\n'
        "}\n\n"
        "0 = safe, 1 = concerning, 2 = dangerous.\n"
        "Be concise but precise in describing any hazards."
    ),
    height=200
)

if video_file and bucket_name and prompt_input:
    with open("uploaded_video.mp4", "wb") as f:
        f.write(video_file.read())

    st.info("Processing video... this may take a while ⏳")

    # Pipeline
    frames = extract_frames("uploaded_video.mp4", num_frames=10)
    grid_img = create_image_grid(frames, "frames_grid.jpg", grid_size=(5, 2))
    st.image(grid_img, caption="Video Frames Grid", use_column_width=True)

    audio_file = extract_audio("uploaded_video.mp4", "audio.wav")
    transcript = transcribe_audio(audio_file, bucket_name)
    st.write("Transcript:", transcript)
    
    bedrock_response = send_to_bedrock(grid_img, transcript, prompt_input)
    st.write("Bedrock Response:", bedrock_response)
