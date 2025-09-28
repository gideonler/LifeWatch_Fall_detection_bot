import os
import aws_cdk as cdk
import json
from src.aws_stack import AwsStack

app = cdk.App()

with open("project_config.json", encoding="utf-8") as f:
    config = json.load(f)

stack_name = config["names"]["stack_name"]

appStack = AwsStack(
    app,
    stack_name,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

# Can add NAG suppressions here if

app.synth()