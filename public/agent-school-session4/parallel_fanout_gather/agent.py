"""
Session 4: Parallel Fan-out / Gather Pattern Demo

Demonstrates an orchestrator triggering multiple sub-agents to run concurrently on distinct context branches.
They read/write to shared session state using distinct keys to avoid race conditions, followed by a compiler agent.
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

# Weather Callback: Save weather data to session state
def save_weather_data(
    callback_context: callback_context_module.CallbackContext,
    llm_response: llm_response_module.LlmResponse,
) -> Optional[llm_response_module.LlmResponse]:
    if llm_response.content and llm_response.content.parts:
        weather_text = llm_response.content.parts[0].text
        callback_context.state["weather_report"] = weather_text
        print(f"\n[Fan-out Branch 1] WeatherFetcher saved data to session state under key 'weather_report'.")
    return None

# News Callback: Save news data to session state
def save_news_data(
    callback_context: callback_context_module.CallbackContext,
    llm_response: llm_response_module.LlmResponse,
) -> Optional[llm_response_module.LlmResponse]:
    if llm_response.content and llm_response.content.parts:
        news_text = llm_response.content.parts[0].text
        callback_context.state["news_report"] = news_text
        print(f"\n[Fan-out Branch 2] NewsFetcher saved data to session state under key 'news_report'.")
    return None

# Compiler Instruction: Read both state keys and compile
def get_compiler_instruction(
    context: callback_context_module.ReadonlyContext,
) -> str:
    weather_report = context.state.get("weather_report", "No weather report found.")
    news_report = context.state.get("news_report", "No news report found.")
    print(f"\n[Gather Step] CompilerAgent reading 'weather_report' and 'news_report' from session state...")
    return f"""You are a Morning Briefing Compiler Agent.
Your job is to read the separate reports gathered concurrently by the Weather and News agents and compile them into a cohesive, professional morning briefing.

Weather Report:
{weather_report}

News Report:
{news_report}

Format the briefing with:
- Executive Summary
- Today's Weather Outlook
- Key Industry News
"""

weather_agent = agents.Agent(
    name="weather_agent",
    model=MODEL_NAME,
    description="Fetches weather forecast data.",
    instruction="You are a Weather Fetcher Agent. Simulate retrieving the weather forecast for New York City today (Sunny, High 75F, Low 60F).",
    after_model_callback=save_weather_data,
)

news_agent = agents.Agent(
    name="news_agent",
    model=MODEL_NAME,
    description="Fetches top news headlines.",
    instruction="You are a News Fetcher Agent. Simulate retrieving top tech industry headlines for today (AI advancements, market trends).",
    after_model_callback=save_news_data,
)

parallel_fanout_agent = agents.ParallelAgent(
    name="parallel_fanout_agent",
    sub_agents=[weather_agent, news_agent],
    description="Executes WeatherFetcher and NewsFetcher concurrently.",
)

compiler_agent = agents.Agent(
    name="compiler_agent",
    model=MODEL_NAME,
    description="Compiles gathered reports into a morning briefing.",
    instruction=get_compiler_instruction,
)

pipeline_orchestrator = agents.SequentialAgent(
    name="pipeline_orchestrator",
    sub_agents=[parallel_fanout_agent, compiler_agent],
    description="Orchestrates Fan-out gathering followed by compiler synthesis.",
)

root_agent = agents.Agent(
    name="root_agent",
    model=MODEL_NAME,
    description="Frontdoor agent for parallel fan-out/gather briefing.",
    instruction="You are an Executive Briefing Frontdoor Agent. Delegate the user request to the pipeline_orchestrator to generate the morning briefing.",
    sub_agents=[pipeline_orchestrator],
)
