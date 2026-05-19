"""
Pattern 6: Iterative Refinement Pattern

Structure: Uses a LoopAgent containing one or more agents that work on a task over multiple iterations.
ADK Primitives Used:
Workflow: LoopAgent manages the repetition.
Communication: Shared Session State is essential for agents to read the previous iteration's output.
Termination: StopChecker agent setting escalate=True in the Event Actions when satisfactory.

Input: Write a Python function named `generate_fibonacci(n)` that generates a list of the first `n` Fibonacci numbers.
Edge cases (n <= 0) should return an empty list. For n = 5, it must return [0, 1, 1, 2, 3].
"""

import os
from typing import AsyncGenerator
from dotenv import load_dotenv
load_dotenv()

from google.adk import agents
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions

MODEL_NAME = "gemini-3.5-flash"

# Coder agent to refine based on requirements and previous drafts in shared state
code_refiner = agents.Agent(
    name="CodeRefiner",
    model=MODEL_NAME,
    instruction="""Read the previous draft in state['current_code'] (if it exists) and the goals in state['requirements'].
Use the built-in code execution tool to test your script first.
Save your verified final python code block in state['current_code'].""",
    output_key="current_code",
    code_executor=BuiltInCodeExecutor(),
)

# Quality checker agent to evaluate draft code
quality_checker = agents.Agent(
    name="QualityChecker",
    model=MODEL_NAME,
    instruction="""Evaluate the Python code in state['current_code'] against requirements in state['requirements'].
Your output must be exactly one word: 'pass' if it meets all constraints, or 'fail' if it has any bugs or missing specs.""",
    output_key="quality_status",
)

# Custom base agent that reads quality_status from state and yields escalation to exit loop
class CheckStatusAndEscalate(BaseAgent):
    # @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("quality_status", "fail")
        should_stop = (status == "pass")
        print(f"\n[Iteration Refinement] Loop iteration evaluated. Quality Status: '{status}'. Should Stop: {should_stop}")
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))

root_agent = agents.LoopAgent(
    name="root_agent",
    max_iterations=5,
    sub_agents=[code_refiner, quality_checker, CheckStatusAndEscalate(name="StopChecker")],
)
