from __future__ import annotations

from typing import Optional

from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
)
from constructs import Construct
from cdklabs.generative_ai_cdk_constructs import bedrock as bedrock_constructs
import os

class BedrockConstruct(Construct):
    """Stores Bedrock Agent and Knowledge Base identifiers in SSM and grants access.

    This construct is intentionally light because Bedrock Agents/KBs are often
    provisioned out-of-band. We keep IDs in SSM Parameters for Lambdas to use.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_executor_lambda,
        config,
        *,
        agent_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        foundation_model_id: Optional[str] = None,
        parameter_prefix: str = "/fall-detection/bedrock",
    ) -> None:
        super().__init__(scope, construct_id)

        # self.param_agent_id = ssm.StringParameter(
        #     self,
        #     "AgentIdParam",
        #     parameter_name=f"{parameter_prefix}/agent-id",
        #     string_value=agent_id or "",
        # )

        # self.param_kb_id = ssm.StringParameter(
        #     self,
        #     "KbIdParam",
        #     parameter_name=f"{parameter_prefix}/kb-id",
        #     string_value=knowledge_base_id or "",
        # )

        # self.param_model_id = ssm.StringParameter(
        #     self,
        #     "ModelIdParam",
        #     parameter_name=f"{parameter_prefix}/model-id",
        #     string_value=foundation_model_id or "",
        # )
        
        # Then create agent and associate knowledge base
        self.agent = self._create_agent(
            agent_executor_lambda, config)

    def grant_read(self, principal: iam.IGrantable) -> None:
        self.param_agent_id.grant_read(principal)
        self.param_kb_id.grant_read(principal)
        self.param_model_id.grant_read(principal) 
        
    def _create_agent(self, agent_executor_lambda, config):
        agent = bedrock_constructs.Agent(
            self,
            "Agent",
            foundation_model=bedrock_constructs.BedrockFoundationModel.MISTRAL_LARGE_2402_V1,
            instruction=config["bedrock_instructions"]["agent_instruction"],
        )

        action_group = bedrock_constructs.AgentActionGroup(
            name="action-group",
            description=config["bedrock_instructions"]["action_group_description"],
            executor=bedrock_constructs.ActionGroupExecutor.fromlambda_function(
                agent_executor_lambda
            ),
            enabled=True,
            api_schema=bedrock_constructs.ApiSchema.from_local_asset(
                os.path.join(
                    os.getcwd(),
                    config["paths"]["assets_folder_name"],
                    "agent_api_schema/schema.json",
                )
            ),
        )

        agent.add_action_group(action_group)
        return agent
