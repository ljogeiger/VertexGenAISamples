"""
Pattern 4: Hierarchical Task Decomposition

Structure: A multi-level tree of agents where higher-level agents break down complex goals and delegate sub-tasks to lower-level agents.
ADK Primitives Used:
Hierarchy: Multi-level LlmAgent structures wrapped in AgentTool.
Interaction: Explicit Invocation (AgentTool) used by parent agents to assign tasks to subagents.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from google.adk import agents
from google.adk.tools import agent_tool

MODEL_NAME = "gemini-3.5-flash"

# Low-level tool-like agent for fetching facts
fact_fetcher = agents.Agent(
    name="FactFetcher",
    model=MODEL_NAME,
    description="Performs research and extracts key factual data about a historical event.",
    instruction="You are a Fact Fetcher Agent. Extract key factual bullet points about the California Gold Rush. Focus purely on dates, locations, and milestones.",
)

# Low-level tool-like agent for generating structures
outliner = agents.Agent(
    name="Outliner",
    model=MODEL_NAME,
    description="Organizes facts into a highly structured outline.",
    instruction="You are a Document Outliner. Read the historical facts provided and organize them into a structured 3-section document outline.",
)

# Mid-level agent combining low-level tools
research_assistant = agents.Agent(
    name="ResearchAssistant",
    model=MODEL_NAME,
    description="Finds facts and organizes them into a structured outline.",
    instruction="Identify key facts about the California Gold Rush using FactFetcher, and then organize them using Outliner.",
    tools=[
        agent_tool.AgentTool(agent=fact_fetcher),
        agent_tool.AgentTool(agent=outliner),
    ]
)

# High-level coordinator agent delegating to the research assistant tool
root_agent = agents.Agent(
    name="root_agent",
    model=MODEL_NAME,
    description="A premium narrative writer that writes reports.",
    instruction="Write a comprehensive, engaging historical report on the California Gold Rush. Use the ResearchAssistant to gather facts and get a structured outline first.",
    tools=[
        agent_tool.AgentTool(agent=research_assistant),
    ]
)
