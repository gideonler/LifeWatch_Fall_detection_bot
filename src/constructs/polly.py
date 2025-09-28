from __future__ import annotations

from aws_cdk import (
    aws_iam as iam,
)
from constructs import Construct


class PollyAccessConstruct(Construct):
    """Utility construct to attach Amazon Polly permissions to principals."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.statement = iam.PolicyStatement(
            actions=["polly:SynthesizeSpeech"], resources=["*"]
        )

    def grant_to(self, grantee: iam.IGrantable) -> None:
        if isinstance(grantee, iam.Role):
            grantee.add_to_policy(self.statement)
        else:
            # Try to add to the principal policy
            try:
                grantee.add_to_principal_policy(self.statement)
            except Exception:
                pass