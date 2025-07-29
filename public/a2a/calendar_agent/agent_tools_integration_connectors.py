
from agents.tools.application_integration_tool import ApplicationIntegrationTool

PROJECT_ID = "sandbox-aiml"
LOCATION = "us-central1"

check_cal = ApplicationIntegrationTool(
      project=PROJECT_ID,  # project in which connection was created
      location=LOCATION,  # region of the connection
      tool_name="check_calendar",  # tool name to identify tool called by Agent
      connection="calendar-connector",  # name of the connection
      actions=["calendar.events.list"],
      tool_instructions="""
    Description: This function returns a list of events, if any, that conflict with the
    given start_time and end_time.

    Args:
      tool_context: The tool context, containing user information like email.
      start_time (str): the start time of the event (ISO 8601 format, e.g., "2025-03-06T13:00:00-05:00").
      end_time (str): the end time of the event (ISO 8601 format).

    Return:
      event_list (list): a list of events (dictionaries) that conflict with the given start_time and end_time.
        If no events conflict, event_list is an empty list.
    """,  # extra instructions for the tool,
  )
