"""
Pattern 5: Review / Critique Pattern (Generator-Critic)

Structure: Typically involves two agents within a SequentialAgent: a Generator and a Critic/Reviewer.
ADK Primitives Used:
Workflow: SequentialAgent ensures generation happens before review.
Communication: Shared Session State (Generator uses output_key to save output; Reviewer reads {draft_text} from state).
"""

import os
from dotenv import load_dotenv
load_dotenv()

from google.adk import agents

MODEL_NAME = "gemini-3.5-flash"

generator = agents.Agent(
    name="DraftWriter",
    model=MODEL_NAME,
    instruction="Write a short, exciting 1-paragraph narrative about the first Moon Landing in 1969.",
    output_key="draft_text"
)

reviewer = agents.Agent(
    name="FactChecker",
    model=MODEL_NAME,
    instruction="Review the text in {draft_text} for factual accuracy and composition style. Output a quality rating (1-10) and a final status ('valid' or 'invalid') with clear reasons.",
    output_key="review_status"
)

root_agent = agents.SequentialAgent(
    name="root_agent",
    sub_agents=[generator, reviewer],
    description="Executes copywriting generation followed by factual editorial critique.",
)
