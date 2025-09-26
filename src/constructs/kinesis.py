from __future__ import annotations

from typing import Optional

from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_kinesis as kds,
)
from constructs import Construct

try:
    # Kinesis Video Streams L2 is not in CDK; use IAM grants and names here.
    from aws_cdk import aws_kinesisvideo as kvs  # type: ignore
except Exception:  # pragma: no cover
    kvs = None  # fallback for type checking


class KinesisStreamsConstruct(Construct):
    """Provision streaming primitives for live detection.

    - Kinesis Video Stream: raw camera/video frames (if supported in account/region)
    - Kinesis Data Stream: derived events/metadata for downstream processing
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        video_stream_name: str = "fall-video-stream",
        create_data_stream: bool = True,
        data_stream_name: str = "fall-events",
        data_stream_shards: int = 1,
    ) -> None:
        super().__init__(scope, construct_id)

        self.video_stream_name = video_stream_name

        # Note: Kinesis Video Streams may not have an L2 in all CDK versions.
        # We keep the name and grant permissions via IAM actions.
        if kvs is not None:
            self.video_stream = kvs.CfnStream(self, "VideoStream", name=video_stream_name)
        else:
            self.video_stream = None  # name-only; permissions via grant helpers

        self.data_stream: Optional[kds.Stream] = None
        if create_data_stream:
            self.data_stream = kds.Stream(
                self,
                "DataStream",
                stream_name=data_stream_name,
                shard_count=data_stream_shards,
                retention_period=Duration.hours(24),
            )

    # Grants for Lambdas/principals
    def grant_video_put_media(self, grantee: iam.IGrantable) -> None:
        iam.Grant.add_to_principal(
            grantee=grantee,
            actions=[
                "kinesisvideo:PutMedia",
                "kinesisvideo:UpdateDataRetention",
                "kinesisvideo:GetDataEndpoint",
            ],
            resource_arns=["*"],  # KVS ARNs depend on endpoint; scoping widely for now
        )

    def grant_video_read(self, grantee: iam.IGrantable) -> None:
        iam.Grant.add_to_principal(
            grantee=grantee,
            actions=[
                "kinesisvideo:GetMedia",
                "kinesisvideo:GetDataEndpoint",
                "kinesisvideo:DescribeStream",
                "kinesisvideo:GetMediaForFragmentList",
            ],
            resource_arns=["*"],
        )

    def grant_data_put_records(self, grantee: iam.IGrantable) -> None:
        if self.data_stream is not None:
            self.data_stream.grant_write(grantee)

    def grant_data_read(self, grantee: iam.IGrantable) -> None:
        if self.data_stream is not None:
            self.data_stream.grant_read(grantee) 