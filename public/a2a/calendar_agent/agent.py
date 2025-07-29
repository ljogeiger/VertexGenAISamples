import vertexai
from google.adk.agents import Agent
from typing import Dict, List
from google.genai import types
import warnings, os, requests, datetime
# from . import agent_tools_integration_connectors
# from agents.tools.application_integration_tool import ApplicationIntegrationTool
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
    api_endpoint="us-central1-aiplatform.googleapis.com",
    staging_bucket="gs://calendar_agent_bucket",
)


single_cal_agent = Agent(
    model='gemini-2.0-flash-001',
    name='single_cal_agent',
    instruction="""
    Your task is to:
    1. Check if the datetime has conflict using check_calendar tool.
    2. If yes, look at the entire day of events using check_calendar
    3. Suggest some times by looking return event list from check_calendar.
    4. Ask the user to confirm one of the datetimes.
    5. Create calendar event if user confirms a time using create_calendar_event.

    If no times are available continue look at different days. Do not look at datetimes in the past.
    If the user uses a relative datetime, use get_today function to get today's date.
    Check state for user information (name, email, preferences, etc.) before asking the user.

    For create_calendar_event, you can keep description, location, and attendees empty.
    This is the users time zone: {time_zone}.
    Today is: {today}
    """,
    tools=[agent_tools.check_cal,
           agent_tools.create_calendar_event,
           agent_tools.create_event_with_details],
    # ApplicationIntegrationTool(
    #   project=PROJECT_ID,  # project in which connection was created
    #   location=LOCATION,  # region of the connection
    #   tool_name="check_calendar",  # tool name to identify tool called by Agent
    #   connection="calendar-connector",  # name of the connection
    #   actions=["GET_calendars/calendar-connector/events"],
    #   tool_instructions="""
    # Description: This function returns a list of events, if any, that conflict with the
    # given start_time and end_time.

    # Args:
    #   tool_context: The tool context, containing user information like email.
    #   start_time (str): the start time of the event (ISO 8601 format, e.g., "2025-03-06T13:00:00-05:00").
    #   end_time (str): the end time of the event (ISO 8601 format).

    # Return:
    #   event_list (list): a list of events (dictionaries) that conflict with the given start_time and end_time.
    #     If no events conflict, event_list is an empty list.
    # """,  # extra instructions for the tool,
    # )
)

# How do I make this flow better. Currently the agent somtimes doesn't check the first users calendar.

# multi_cal_agent = Agent(
#     model='gemini-2.0-flash-001',
#     name='multi_cal_agent',
#     instruction="""
#     Your job is to help users create calendar events for multiple people.
#     Your user's calendar is {email} and you are the organizer of this event.

#     Follow these steps:
#     1. For each calendar invitee, check the availability of their calendars using external_user_check_cal. For your own calendar use check_cal.
#     2. If there is a conflict, suggest three new times. You must check if that time works with the external user before suggesting it. It's your job to resolve conflicts.
#     3. If there is no conflict for all users, create the calendar even with the calendar invitees' email addresses using create_multi_calendar_event.

#     Your user is in the following time zone: {time_zone}. You can ignore time zone of other users.
#     Today is: {today}
#     """,
#     tools=[agent_tools.check_cal,
#            agent_tools.external_user_check_cal,
#            agent_tools.create_multi_cal_event,
#            agent_tools.get_today]
# )

# external_cal_request_agent = Agent(
#     model='gemini-2.0-flash-001',
#     name='external_cal_request_agent',
#     instruction="""
#     You have recieved an external request to check the calendar of your user using check_cal.
#     Your job is to check if the suggested time works and respond yes or no.
#     If no, suggest up to three alternative times. Make sure the suggested times work with your users calendar. Use check_cal if you are unsure.

#     Be aware of time zones. Your user is in the following time zone: {time_zone}
#     If you still don't know the time zone of your user, use get_user_profile to get your user's time zone.
#     Today is: {today}
#     """,
#     tools=[agent_tools.check_cal, agent_tools.get_user_profile],
# )

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    instruction="""
    You are a helpful calendar assistant.
    Your end goal is to fulfill the user's intention and resolve conflicts as they arise.

    *ALWAYS* run get_user_profile, even if you get "EXTERNAL_CAL_REQUEST"

    Your tasks are to:
    1. Greet the user with their name from get_user_profile.
    2. Explain your task to the user.
    3. Gather details necessary to route the user correctly.
    4. Route the request to the correct next agent. Pass the user information you recieved to the next agent.

    single_cal_agent has tools to create events and check calendars for a single user.
    multi_cal_agent creates events and check calendars for multiple people.
    Only if you recieve a request that starts with "EXTERNAL_CAL_REQUEST" route them to the external_cal_request_agent.
    You can get your email, timezone, preferencees, and more by calling get_user_profile.
    """,
    sub_agents=[single_cal_agent], #, multi_cal_agent, external_cal_request_agent
    tools=[agent_tools.get_user_profile]
)
