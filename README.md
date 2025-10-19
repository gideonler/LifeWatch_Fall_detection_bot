# fall_detection_agentic_aws_hackathon

## Directory structure

src/app: contains code to run the streaming app
src/lambdas: contains the code of our lambda functions deployed on AWS

## Instructions to set up

These instructions detail how to set up the streaming app to perform real time monitoring of alerts. 

### Create the virtual environment to install dependencies for app

```python3 -m venv .venv && source .venv/bin/activate && cd src/app && pip install -r requirements.txt```

### Run streaming app
```python live_stream_cam.py```

Script Workflow:
    0. Checks available camera device and prompts User to select desired device to use. 
    1. Capture N frames from webcam at fixed intervals.
    2. Combine captured frames into a single image grid.
    3. Save the grid locally (for debugging/testing).
    4. Send the grid image (base64-encoded) to Lambda Step function.
    5. Log the Lambda response to a local file.
    6. Repeat the process every cycle (e.g., every 30 seconds).

