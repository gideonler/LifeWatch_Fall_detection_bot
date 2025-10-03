# © 2025 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
#
# This AWS Content is provided subject to the terms of the AWS Customer Agreement
# available at http://aws.amazon.com/agreement or other written agreement between
# Customer and either Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.

from aws_cdk import Stack, CfnOutput
from constructs import Construct
from .constructs.lambdas import LambdasConstruct
from .constructs.bedrock import BedrockConstruct
from .constructs.buckets import BucketsConstruct
# from .constructs.kinesis import KinesisConstruct
from .constructs.notifications import NotificationsConstruct
from .constructs.polly import PollyAccessConstruct
from .constructs.rekognition import RekognitionConstruct
from .constructs.transcribe import TranscribeConstruct
import json


class AwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get configuration first
        config = self.get_config()

        # Create SNS topics
        topics = NotificationsConstruct(self, "Notifications")

        # Create S3 resources
        buckets = BucketsConstruct(
            self, "Buckets", bucket_name_prefix=construct_id.lower()
        )
        
        # Create Lambda resources
        lambdas = LambdasConstruct(self, "Lambdas")
        buckets.audio_bucket.grant_read(lambdas.transcribe_lambda)
        buckets.image_bucket.grant_read(lambdas.video_invoke)

        # Create Agent (includes Knowledge Base)
        agent = BedrockConstruct(self, "BedrockSecrets", lambdas.agent_executor, config)
        buckets.events_bucket.grant_read_write(self.agent)

        # Create Kinesis construct
        # kinesis = KinesisConstruct(self, "Kinesis")

        # Create Polly construct
        polly = PollyAccessConstruct(self, "PollyAccess")
        
        #Create Rekognition construct
        rekognition = RekognitionConstruct(
            self,
            "Rekognition",
            image_bucket=buckets.image_bucket,
            video_invoke_lambda=lambdas.video_invoke,
        )
        
        # Create Transcribe construct
        transcribe = TranscribeConstruct(
            self,
            "Transcribe",
            audio_bucket=buckets.audio_bucket,
            transcribe_invoke_lambda=lambdas.transcribe_invoke
        )
        
        CfnOutput(self, "EventsBucket", value=buckets.events_bucket.bucket_name)
        CfnOutput(self, "ImagesBucket", value=buckets.images_bucket.bucket_name)


    def get_config(self):
        """Get configuration from context"""

        # read in agent_config.json
        with open("project_config.json", "r") as f:
            config = json.load(f)

        self.BEDROCK_AGENT_NAME = config["names"]["bedrock_agent_name"]
        self.BEDROCK_AGENT_ALIAS = config["names"]["bedrock_agent_alias"]

        self.BEDROCK_AGENT_FM = config["models"]["bedrock_agent_foundation_model"]

        self.AGENT_INSTRUCTION = config["bedrock_instructions"]["agent_instruction"]

        self.LAMBDAS_SOURCE_FOLDER = config["paths"]["lambdas_source_folder"]
        self.AGENT_API_SCHEMA_DESTINATION_PREFIX = config["paths"]["agent_schema_destination_prefix"]

        return config