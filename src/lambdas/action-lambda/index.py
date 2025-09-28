import json
import logging
from typing import Dict, Any

from action_handler import ActionHandler
from agent_executor import AgentExecutor

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing Bedrock agent output and executing actions.
    
    This function:
    1. Receives output from Bedrock agent
    2. Determines appropriate actions using ActionHandler
    3. Executes actions using AgentExecutor (SNS + Polly)
    
    Args:
        event: Lambda event containing Bedrock agent output
        context: Lambda context
        
    Returns:
        Dictionary containing execution results
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Initialize handlers
        action_handler = ActionHandler()
        agent_executor = AgentExecutor()
        
        # Process Bedrock output to determine actions
        bedrock_response = event.get('bedrock_response', event)
        actions = action_handler.process_bedrock_output(bedrock_response)
        
        if not actions:
            logger.info("No actions determined from Bedrock output")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "No actions required",
                    "actions_count": 0
                })
            }
        
        # Execute the determined actions
        execution_results = agent_executor.execute_actions(actions)
        
        # Create response
        response = {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Actions executed successfully",
                "actions_count": len(actions),
                "execution_summary": agent_executor.get_execution_summary(execution_results),
                "results": execution_results
            })
        }
        
        logger.info(f"Successfully executed {len(actions)} actions")
        return response
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }