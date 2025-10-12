from aws_cdk import (
    aws_iam as iam,
    aws_rekognition as rekognition,
    aws_s3 as s3,
    aws_lambda as _lambda,
)
from constructs import Construct

class RekognitionConstruct(Construct):
    """
    Provisions Rekognition resources and necessary IAM permissions.
    Allows video/image analysis and integrates with S3 buckets and Lambda functions.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        image_bucket: s3.Bucket,
        video_invoke_lambda: _lambda.Function,
    ) -> None:
        super().__init__(scope, construct_id)

        # Create IAM role for Rekognition
        self.rekognition_role = iam.Role(
            self,
            "RekognitionRole",
            assumed_by=iam.ServicePrincipal("rekognition.amazonaws.com"),
        )

        # Grant Rekognition permissions to read from the image bucket
        image_bucket.grant_read(self.rekognition_role)

        # Grant Rekognition permissions to the video invoke lambda
        video_invoke_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "rekognition:DetectFaces",
                    "rekognition:DetectLabels",
                    "rekognition:StartFaceDetection",
                    "rekognition:GetFaceDetection",
                    "rekognition:StartPersonTracking",
                    "rekognition:GetPersonTracking",
                ],
                resources=["*"],
            )
        )

        # Add any additional policies needed for Rekognition
        self.rekognition_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                resources=[
                    image_bucket.bucket_arn,
                    f"{image_bucket.bucket_arn}/*",
                ],
            )
        )

    def grant_rekognition_access(self, lambda_function: _lambda.Function) -> None:
        """
        Grants Rekognition access to a Lambda function.
        """
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "rekognition:DetectFaces",
                    "rekognition:DetectLabels",
                    "rekognition:StartFaceDetection",
                    "rekognition:GetFaceDetection",
                ],
                resources=["*"],
            )
        )