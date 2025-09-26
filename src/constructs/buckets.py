from __future__ import annotations

from aws_cdk import (
    RemovalPolicy,
    aws_s3 as s3,
)
from constructs import Construct


class BucketsConstruct(Construct):
    """Provision S3 buckets used by the system.

    Creates two buckets:
    - events_bucket: stores structured events (JSON/logs) from the pipeline
    - images_bucket: stores snapshot images captured by the video agent
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name_prefix: str,
    ) -> None:
        super().__init__(scope, construct_id)

        events_bucket_name = f"{bucket_name_prefix}-events"
        images_bucket_name = f"{bucket_name_prefix}-images"

        self.events_bucket = s3.Bucket(
            self,
            "EventsBucket",
            bucket_name=None,
            enforce_ssl=True,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.images_bucket = s3.Bucket(
            self,
            "ImagesBucket",
            bucket_name=None,
            enforce_ssl=True,
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.events_bucket_name_output = events_bucket_name
        self.images_bucket_name_output = images_bucket_name 