"""
Session 4: Sequential Pipeline Pattern Demo

Demonstrates an orchestrator executing a list of sub-agents one after the other in a strictly predefined order.
They share the same InvocationContext and pass data sequentially via shared session state.
"""

import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from google.adk import agents
from google.adk import runners
from google.adk.agents import callback_context as callback_context_module
from google.adk.models import llm_response as llm_response_module
from google.adk.sessions import in_memory_session_service
from google.genai import types

MODEL_NAME = "gemini-3.5-flash"

# Step 2 Instruction: Read raw data from session state and format
def get_process_agent_instruction(
    context: callback_context_module.ReadonlyContext,
) -> str:
    raw_data = context.state.get("raw_customer_data", "No raw data found in state.")
    return f"""You are a Data Processing Agent.
Your job is to read the raw customer data provided below, clean it up, and generate a professional executive summary.

Raw Data from Session State:
{raw_data}

Format the output with clear headings:
- Customer Profile
- Purchase History Summary
- Recommended Action
"""

# Presenter Instruction: Read final summary from state and present beautifully
def get_presenter_instruction(
    context: callback_context_module.ReadonlyContext,
) -> str:
    final_summary = context.state.get("final_summary", "No final summary report found in session state.")
    return f"""You are a Customer Success Presenter.
Your job is to read the executive summary report processed by the background agents and present it beautifully and professionally directly to the user.

Executive Summary Report:
{final_summary}

Make sure to include a polite greeting at the beginning, and format the report with elegant headers and bullet points so it is highly readable for the client.
"""

# Leaf 1: FetchAgent runs silently in background and saves data to "raw_customer_data"
fetch_agent = agents.Agent(
    name="fetch_agent",
    model=MODEL_NAME,
    output_key="raw_customer_data",
    description="Retrieves raw data from a database based on the query.",
    instruction="You are a Data Fetcher Agent. Your job is to simulate retrieving raw customer transaction records from a database based on the user's request. Output a mock JSON or raw text representing the database records.",
)

# Leaf 2: ProcessAgent runs silently in background and saves summary to "final_summary"
process_agent = agents.Agent(
    name="process_agent",
    model=MODEL_NAME,
    output_key="final_summary",
    description="Processes and summarizes raw data from session state.",
    instruction=get_process_agent_instruction,
)

# Conversational Chat Agent to present the final report to the user
presenter_agent = agents.Agent(
    name="presenter_agent",
    model=MODEL_NAME,
    description="Presents the final summary beautifully to the end user.",
    instruction=get_presenter_instruction,
)

# Clean ADK 3.12 SequentialAgent orchestrating sequential execution
root_agent = agents.SequentialAgent(
    name="root_agent",
    sub_agents=[fetch_agent, process_agent, presenter_agent],
    description="Executes a step-by-step data processing pipeline.",
)
