# Lambda construct
# To configure Lambda using code and deploy to AWS

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from aws_cdk import (
	Duration,
	aws_iam as iam,
	aws_lambda as _lambda,
)
from constructs import Construct


LAMBDA_SRC_ROOT = Path(__file__).resolve().parents[1] / "lambdas"


class LambdaFunctionsConstruct(Construct):
	"""Creates and configures Lambda functions used in the system.

	Functions:
	- transcribe_invoke
	- video_invoke
	- agent_executor
	- action
	"""

	def __init__(
		self,
		scope: Construct,
		construct_id: str,
		*,
		environment: Optional[Dict[str, str]] = None,
	) -> None:
		super().__init__(scope, construct_id)

		common_env = environment or {}

		self.transcribe_invoke = self._create_python_lambda(
			"TranscribeInvoke",
			LAMBDA_SRC_ROOT / "transcribe-invoke-lambda",
			environment=common_env,
		)

		self.video_invoke = self._create_python_lambda(
			"VideoInvoke",
			LAMBDA_SRC_ROOT / "video-invoke-lambda",
			environment=common_env,
			timeout=Duration.seconds(60),
			memory_mb=1024,
		)

		self.agent_executor = self._create_python_lambda(
			"AgentExecutor",
			LAMBDA_SRC_ROOT / "action-lambda",
			environment=common_env,
			timeout=Duration.seconds(120),
			memory_mb=1024,
		)

		self.action = self._create_python_lambda(
			"ActionHandler",
			LAMBDA_SRC_ROOT / "action-lambda",
			environment=common_env,
		)

	def grant_s3_access(self, *, read_buckets: list, write_buckets: list) -> None:
		for fn in [self.transcribe_invoke, self.video_invoke, self.agent_executor, self.action]:
			for b in read_buckets:
				b.grant_read(fn)
			for b in write_buckets:
				b.grant_write(fn)

	def allow_bedrock_invoke(self) -> None:
		policy = iam.ManagedPolicy(self, "BedrockInvokePolicy", statements=[
			iam.PolicyStatement(
				actions=[
					"bedrock:InvokeModel",
					"bedrock:InvokeModelWithResponseStream",
				],
				resources=["*"],
			)
		])
		for fn in [self.agent_executor, self.transcribe_invoke, self.video_invoke]:
			fn.role.add_managed_policy(policy)

	def allow_polly_synthesize(self) -> None:
		for fn in [self.agent_executor, self.action]:
			fn.add_to_role_policy(iam.PolicyStatement(
				actions=["polly:SynthesizeSpeech"],
				resources=["*"]
			))

	def allow_sns_publish(self, topic_arn: str) -> None:
		for fn in [self.agent_executor, self.action]:
			fn.add_environment("ALERTS_TOPIC_ARN", topic_arn)
			fn.add_to_role_policy(iam.PolicyStatement(
				actions=["sns:Publish"],
				resources=[topic_arn]
			))

	def _create_python_lambda(
		self,
		id_: str,
		src_dir: Path,
		*,
		environment: Optional[Dict[str, str]] = None,
		timeout: Duration = Duration.seconds(30),
		memory_mb: int = 512,
	) -> _lambda.Function:
		return _lambda.Function(
			self,
			id_,
			runtime=_lambda.Runtime.PYTHON_3_12,
			handler="index.handler",
			code=_lambda.Code.from_asset(str(src_dir)),
			environment=environment or {},
			timeout=timeout,
			memory_size=memory_mb,
		)