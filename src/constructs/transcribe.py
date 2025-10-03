from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_transcribe as transcribe,
)
from constructs import Construct

class TranscribeConstruct(Construct):
    """
    Provisions Transcribe resources and necessary IAM permissions.
    Integrates with S3 buckets for audio file processing and Lambda functions.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        audio_bucket: s3.Bucket,
        transcribe_invoke_lambda: _lambda.Function,
    ) -> None:
        super().__init__(scope, construct_id)

        # Create IAM role for Transcribe
        self.transcribe_role = iam.Role(
            self,
            "TranscribeRole",
            assumed_by=iam.ServicePrincipal("transcribe.amazonaws.com"),
        )

        # Grant Transcribe permissions to read from audio bucket and write to events bucket
        audio_bucket.grant_read(self.transcribe_role)

        # Grant Transcribe permissions to the transcribe invoke lambda
        transcribe_invoke_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                ],
                resources=["*"],
            )
        )

        # Add permissions for Transcribe service
        self.transcribe_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                resources=[
                    audio_bucket.bucket_arn,
                    f"{audio_bucket.bucket_arn}/*",
                ],
            )
        )

    def grant_transcribe_access(self, lambda_function: _lambda.Function) -> None:
        """
        Grants Transcribe access to a Lambda function.
        """
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                    "transcribe:ListTranscriptionJobs",
                ],
                resources=["*"],
            )
        )