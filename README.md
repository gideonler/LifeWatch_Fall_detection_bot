# LifeWatch
Your loved one’s digital guardian.

LifeWatch is an AI-powered caregiver assistant that uses video, voice, and real-time decision-making to detect falls, monitor wellbeing, and provide instant communication for elderly safety. It helps families gain peace of mind while supporting elders to live independently.

# Features
- **Fall Detection** – Analyze video feeds to identify possible falls or abnormal behavior.
- **Voice Monitoring** – Transcribe and interpret spoken input for signs of distress.
- **Real-Time AI Decisions** – Amazon Bedrock agent determines appropriate actions.
- **Instant Responses** – Send alerts, make calls, or provide spoken reassurance.
- **Caregiver Dashboard** – Built with Streamlit for easy monitoring and feedback.

# Tech Stack
- **Languages & Frameworks:** Python, Streamlit, OpenCV/ffmpeg
- **AWS Services:** Rekognition, Transcribe, Polly, Bedrock, Kinesis (optional), S3, Lambda, SNS, DynamoDB, CloudWatch
- **Integrations:** Twilio (calls & WhatsApp notifications)

# How It Works
1. Video or audio is uploaded or streamed into AWS.
2. Rekognition (video) and Transcribe (audio) analyze the inputs.
3. Results are sent to a Bedrock agent, which makes a structured decision.
4. The system executes the decision:
  - Sends alerts via SNS/Twilio
  - Generates voice responses via Polly
  - Logs events into S3/DynamoDB
5. Caregivers see alerts and history in the dashboard.

# Getting Started
1. Clone the repository.
2. Deploy infrastructure with AWS CDK:
  cdk bootstrap
  cdk deploy
3. Run the Streamlit dashboard locally:
  streamlit run app.py
4. Upload test video/audio files into the designated S3 bucket.
5. Monitor outputs in the dashboard or via SNS/Twilio alerts.

# Directory structure
src/app
src/constructs
src/lambdas

# Commit messages
Prefixes
- infra: for infrastructure (constructs) related commits
- app: for application related commits
- lambda: for lambda related commits
- docs: documentation related commits
- config: configuration related commits
