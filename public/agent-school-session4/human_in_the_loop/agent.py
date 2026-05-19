"""
Pattern 7: Human-in-the-Loop Pattern

Structure: Integrates human intervention points within an agent workflow.
ADK Primitives Used:
Interaction: Custom Tool that yields RequestInput to pause execution and wait for human input.
Workflow: SequentialAgent executing Prepare -> Request Approval -> Process Decision.
"""

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from google.adk import agents
from google.adk.tools import FunctionTool

MODEL_NAME = "gemini-3.5-flash"

# Simulated external review system that automatically approves after 10 seconds
async def external_approval_tool(amount: float, reason: str) -> str:
    """Sends the corporate spend request to the human review system for approval.
    
    Args:
        amount: The amount of spend requested.
        reason: The business justification.
    """
    print(f"\n[HITL Tool] Proposing spend of ${amount} for reason: '{reason}'...")
    print(f"[HITL Tool] Waiting 10 seconds for automatic human approval manager response...")
    await asyncio.sleep(10)
    print(f"[HITL Tool] Human approval response received: 'approved'!")
    return "approved"

approval_tool = FunctionTool(func=external_approval_tool)

# Agent 1: Prepares request details
prepare_request = agents.Agent(
    name="PrepareApproval",
    model=MODEL_NAME,
    instruction="Prepare the approval request details based on user input. Store amount under key 'approval_amount' and reason under key 'approval_reason' in session state.",
)

# Agent 2: Triggers human oversight approval tool
request_approval = agents.Agent(
    name="RequestHumanApproval",
    model=MODEL_NAME,
    instruction="Use the external_approval_tool with amount from state['approval_amount'] and reason from state['approval_reason']. Save the final decision to state['human_decision'].",
    tools=[approval_tool],
    output_key="human_decision"
)

# Agent 3: Evaluates the human input and outputs final status
process_decision = agents.Agent(
    name="ProcessDecision",
    model=MODEL_NAME,
    instruction="Check state['human_decision']. If 'approved', confirm success and complete action. If 'rejected', politely inform the user that the request was denied.",
)

# Root Sequential Orchestrator (HumanApprovalWorkflow)
root_agent = agents.SequentialAgent(
    name="root_agent",
    sub_agents=[prepare_request, request_approval, process_decision],
    description="Executes prepare request, request human approval, and process decision sequentially.",
)
