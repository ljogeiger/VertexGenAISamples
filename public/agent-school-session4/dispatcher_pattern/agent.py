"""
Session 4: Coordination / Dispatcher Pattern Demo

Demonstrates a central LLM coordinator acting as a router to interpret ambiguous user intent
and delegate to specialized sub-agents (Billing & Support).
"""

import os
from dotenv import load_dotenv
load_dotenv()

from google.adk import agents
from google.genai import types

MODEL_NAME = "gemini-3.5-flash"

# Define specialized sub-agents
billing_agent = agents.Agent(
    name="billing_agent",
    model=MODEL_NAME,
    description="Handles billing inquiries, payment failures, refunds, and invoice requests.",
    instruction="You are a specialized Billing Support Agent. Your goal is to resolve customer billing issues. When a customer asks about failed payments or refunds, explain the billing resolution process politely and clearly.",
)

support_agent = agents.Agent(
    name="support_agent",
    model=MODEL_NAME,
    description="Handles technical support, login issues, password resets, and account access.",
    instruction="You are a specialized Technical Support Agent. Your goal is to help users with login issues, password resets, and system access. Guide them step-by-step to regain access to their accounts.",
)

# Define Coordinator / Dispatcher
root_agent = agents.Agent(
    name="root_agent",
    model=MODEL_NAME,
    description="Central coordinator that routes user inquiries to the correct specialized sub-agent.",
    instruction="""You are a Help Desk Coordinator. Your job is to route user inquiries to the appropriate specialized sub-agent.
If the user asks about billing, payment failures, or refunds, delegate to billing_agent.
If the user asks about login issues, password resets, or account access, delegate to support_agent.
If the request does not match either, answer politely yourself.""",
    sub_agents=[billing_agent, support_agent],
)

