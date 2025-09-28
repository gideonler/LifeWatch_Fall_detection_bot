# fall_detection_agentic_aws_hackathon

## Directory structure

src/app
src/constructs
src/lambdas

## Commit messages

Prefixes:

- infra: for infrastructure (constructs) related commits
- app: for application related commits
- lambda: for lambda related commits
- docs: documentation related commits
- config: configuration related commits

## Instructions

### Creating the virtual environment to install dependencies

```python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt```

### Managing the infrastructure

#### Deploying the infrastruction to AWS

```cdk bootstrap && cdk deploy```
Note that if the deployment fails, you may need to run the destroy command below to destroy the services that were created

#### Destroying the infrastructre

```cdk destroy```
