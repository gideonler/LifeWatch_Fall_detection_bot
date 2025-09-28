from __future__ import annotations

from typing import Optional

from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
)
from constructs import Construct


class BedrockSecretsConstruct(Construct):
    """Stores Bedrock Agent and Knowledge Base identifiers in SSM and grants access.

    This construct is intentionally light because Bedrock Agents/KBs are often
    provisioned out-of-band. We keep IDs in SSM Parameters for Lambdas to use.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        agent_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        foundation_model_id: Optional[str] = None,
        parameter_prefix: str = "/fall-detection/bedrock",
    ) -> None:
        super().__init__(scope, construct_id)

        self.param_agent_id = ssm.StringParameter(
            self,
            "AgentIdParam",
            parameter_name=f"{parameter_prefix}/agent-id",
            string_value=agent_id or "",
        )

        self.param_kb_id = ssm.StringParameter(
            self,
            "KbIdParam",
            parameter_name=f"{parameter_prefix}/kb-id",
            string_value=knowledge_base_id or "",
        )

        self.param_model_id = ssm.StringParameter(
            self,
            "ModelIdParam",
            parameter_name=f"{parameter_prefix}/model-id",
            string_value=foundation_model_id or "",
        )

    def grant_read(self, principal: iam.IGrantable) -> None:
        self.param_agent_id.grant_read(principal)
        self.param_kb_id.grant_read(principal)
        self.param_model_id.grant_read(principal) 