import vertexai
from agents import Agent, Runner
from agents.artifacts import InMemoryArtifactService
from agents.events import Event
from agents.sessions import InMemorySessionService
from typing import Dict, List
from google.genai import types
import warnings, os, requests, datetime
from . import agent_tools

PROJECT_ID = "sandbox-aiml"
LOCATION = "us-central1"
APP_NAME = 'calendar_app'
USER_ID = 'TEST_USER'

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    # api_endpoint="us-central1-autopush-aiplatform.sandbox.googleapis.com",
    api_endpoint="us-central1-aiplatform.googleapis.com",
    staging_bucket="gs://calendar_agent_bucket",
)

# TODO: How do I pass context to this agent?
single_cal_agent = Agent(
    model='gemini-2.0-flash-001',
    name='single_cal_agent',
    instruction="""
    Your task is to:
    1. Check if the datetime has conflict using check_cal tool.
    2. If yes, look at the entire day of events using check_cal
    3. Suggest some times by looking return event list from check_cal.
    4. Ask the user to confirm one of the datetimes.
    5. Create calendar event if user confirms a time using create_calendar_event.

    If no times are available continue look at different days. Do not look at datetimes in the past.
    If the user uses a relative datetime, use get_today function to get today's date.
    Check state for user information (name, email, preferences, etc.) before asking the user.

    For create_calendar_event, you can keep description, location, and attendees empty.
    This is your time zone: {time_zone}.
    """,
    tools=[agent_tools.check_cal, agent_tools.create_calendar_event, agent_tools.create_event_with_details, agent_tools.get_today]
)

# TODO: create multi-calendar agent interaction.
# This agent needs to be able to make external calls.
# Perhaps if I deploy another instance of calendar agent and
# then I have a mapping of agent id to users.
# OR
# The agent has access to all calendars
multi_cal_agent = Agent(
    model='gemini-2.0-flash-001',
    name='multi_cal_agent',
    instruction="""
    Respond with "I have not been implemented yet"
    """,
)

external_cal_request_agent = Agent(
    model='gemini-2.0-flash-001',
    name='external_cal_request_agent',
    instruction="""
    Respond with "I have not been implemented yet"
    """,
)

# TODO: this agent should load user details to get calendar ID and Oauth scopes.
# Could probably be a JSON file for now.
root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    instruction="""
    You are a helpful calendar assistant.
    Your end goal is to create calendar events and resolve conflicts as they arise.
    Your task is to
    1. Greet the user with their name which you can get by calling get_user_info.
    2. Explain your task to the user
    3. Route the request to the correct next agent. Pass the user infromation you recieved to the next agent.

    single_cal_agent has tools to create events and check calendars.
    """,
    children=[single_cal_agent, multi_cal_agent, external_cal_request_agent],
    tools=[agent_tools.get_user_profile],
    flow="auto", # Should probably create customer BaseFlow because this goes back to root_agent after a child performs a tool call.
)

# Agent that reads in the check_cal return list for the day and suggests a new time

