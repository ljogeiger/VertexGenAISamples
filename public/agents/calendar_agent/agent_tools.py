from googleapiclient.discovery import build
from google.oauth2 import service_account
from agents.tools.tool_context import ToolContext
from googleapiclient.errors import HttpError

import datetime, json

SERVICE_ACCOUNT_FILE = '/Users/lukasgeiger/Desktop/VertexGenAISamples/private/agents/samples/calendar_agent/sandbox-aiml-ee5b56f515cb.json'  # Replace with your service account key file



def check_cal(tool_context: ToolContext,
              start_time: str,
              end_time: str) -> list:
    """
    Description: This function returns a list of events, if any, that conflict with the
    given start_time and end_time.

    Args:
      tool_context: The tool context, containing user information like email.
      start_time (str): the start time of the event (ISO 8601 format, e.g., "2025-03-06T13:00:00-05:00").
      end_time (str): the end time of the event (ISO 8601 format).

    Return:
      event_list (list): a list of events (dictionaries) that conflict with the given start_time and end_time.
        If no events conflict, event_list is an empty list.
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    try:
        # Authenticate and build the service
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)

        # --- Parse and Validate Times ---
        try:
            start_dt = datetime.datetime.fromisoformat(start_time)
            end_dt = datetime.datetime.fromisoformat(end_time)
        except ValueError as e:
            print(f"Invalid date format: {e}.  Dates must be in ISO 8601 format.")
            return []  # Return an empty list on invalid input.

        if start_dt >= end_dt:
            print("Error: Start time must be before end time.")
            return []

        # --- Calculate timeMin and timeMax (with proper timezone handling) ---
        # Get the timezone from the tool_context, or default to UTC if not provided
        timezone_str = tool_context.state["time_zone"] if tool_context.state["time_zone"] else "UTC"

        try:
            # Convert start and end times to the user's timezone. This handles DST correctly.
            import pytz  # Import pytz here, as it's only needed if timezones are involved
            tz = pytz.timezone(timezone_str)
            start_dt_localized = start_dt.astimezone(tz)
            end_dt_localized = end_dt.astimezone(tz)


            time_min = (start_dt_localized - datetime.timedelta(days=1)).isoformat()
            time_max = (end_dt_localized + datetime.timedelta(days=1)).isoformat()
            # No need to append 'Z' if we're using the localized ISO format, which includes the offset.

        except Exception as e:
            print(f"Error handling timezone: {e}.  Using UTC.") # Fallback
            time_min = (start_dt - datetime.timedelta(days=1)).isoformat() + 'Z'
            time_max = (end_dt + datetime.timedelta(days=1)).isoformat() + 'Z'


        # --- Fetch Events ---
        events_result = service.events().list(
            calendarId=tool_context.state["email"],
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # --- Check for Conflicts ---
        conflicting_events = []
        for event in events:
            # Ignore all day events
            if 'date' in event['start']:  # All-day events have 'date', not 'dateTime'
                continue  # Skip to the next event

            event_start_str = event['start'].get('dateTime')
            event_end_str = event['end'].get('dateTime')

            #  Handle missing dateTime (shouldn't happen for non-all-day events, but be robust)
            if not event_start_str or not event_end_str:
                continue

            event_start_dt = datetime.datetime.fromisoformat(event_start_str)
            event_end_dt = datetime.datetime.fromisoformat(event_end_str)

            # Check for overlap
            if start_dt < event_end_dt and end_dt > event_start_dt:
                conflicting_events.append(event)

        return conflicting_events

    except HttpError as error:
        print(f'An HTTP error occurred: {error}')  # More specific error
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def get_user_profile(tool_context: ToolContext):
  """
  Reads user data from a JSON file.

  Args:
      filepath (str, optional): The path to the JSON file.

  Returns:
      dict: A dictionaries, which includes first name, last name, email, time zone, and preferences.
            Returns an empty list if the file doesn't exist or is invalid JSON.
  """
  filepath = "/Users/lukasgeiger/Desktop/VertexGenAISamples/private/agents/samples/calendar_agent/user_info.json"
  try:
      with open(filepath, 'r') as f:
          data = json.load(f)
          tool_context.state["first_name"] = data["first_name"]
          tool_context.state["last_name"] = data["last_name"]
          tool_context.state["email"] = data["email"]
          tool_context.state["time_zone"] = data["time_zone"]
          tool_context.state["double_book"] = data["double_book"]
          return data
  except FileNotFoundError:
      print(f"Error: File not found at '{filepath}'")
      return []
  except json.JSONDecodeError:
      print(f"Error: Invalid JSON format in '{filepath}'")
      return []
  except Exception as e:
      print(f"An unexpected error occurred: {e}")
      return []

def create_event_with_details(email: str,
                 start_time: str,
                 end_time: str,
                 title: str,
                 description: str,
                 location: str,
                 attendees: list) -> bool:
  """
  Description: Create a Google Calendar event.

  Args:
    email (str): email address of the calendar in which to create the event.
    start_time (str): the start time of the event (ISO 8601 format, e.g., "2024-03-15T09:00:00-08:00").
    end_time (str): the end time of the event (ISO 8601 format).
    title (str): The title of the event.
    description (str, optional): The description of the event. Defaults to "".
    location (str, optional): The location of the event. Defaults to "".
    attendees (list, optional): The list of attendees. Can be empty. Ex. ["johndoe@gmail.com","taylorsmith@gmail.com"]

  Return:
    success (bool): True if successfully created event, False if not.
  """
  SCOPES = ['https://www.googleapis.com/auth/calendar']

  creds = None
  # Use service account credentials
  try:
      creds = service_account.Credentials.from_service_account_file(
          SERVICE_ACCOUNT_FILE, scopes=SCOPES)
  except Exception as e:
      print(f"Error loading service account credentials: {e}")
      return False

  if not creds:  # Check if credentials were loaded successfully
      print("Error: Service account credentials could not be loaded.")
      return False


  try:
      service = build('calendar', 'v3', credentials=creds)

      start_datetime = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
      end_datetime = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))

      if start_datetime >= end_datetime:
          print("Error: Start time must be before end time.")
          # TODO: pass error back to model
          return False

      event = {
          'summary': title,
          'location': location,
          'description': description,
          'start': {
              'dateTime': start_time,
              'timeZone': 'America/Los_Angeles',  #  Important: Specify the correct timezone!
          },
          'end': {
              'dateTime': end_time,
              'timeZone': 'America/Los_Angeles',  # Important: Specify the correct timezone!
          },
          'attendees': [attendee for attendee in attendees],
      }

      event = service.events().insert(calendarId=email, body=event).execute()
      print(f"Event created: {event.get('htmlLink')}")
      return True

  except HttpError as error:
      print(f'An error occurred: {error}')
      return False
  except Exception as e:
      print(f"Error creating event: {e}")
      return False

def create_calendar_event(start_time: str,
                 end_time: str,
                 title: str,
                 tool_context: ToolContext) -> bool:
  """
  Description: Create a Google Calendar event.

  Args:
    start_time (str): the start time of the event (ISO 8601 format, e.g., "2024-03-15T09:00:00-08:00").
    end_time (str): the end time of the event (ISO 8601 format).
    title (str): The title of the event.

  Return:
    success (bool): True if successfully created event, False if not.

  Example:
  create_calendar_event(
      start_time='2025-23-02T12:00:00',
      end_time='2025-23-02T12:30:00',
      title='Test Event') -> True
  """
  SCOPES = ['https://www.googleapis.com/auth/calendar']

  creds = None
  # Use service account credentials
  try:
      creds = service_account.Credentials.from_service_account_file(
          SERVICE_ACCOUNT_FILE, scopes=SCOPES)
  except Exception as e:
      print(f"Error loading service account credentials: {e}")
      return False

  if not creds:  # Check if credentials were loaded successfully
      print("Error: Service account credentials could not be loaded.")
      return False


  try:
      service = build('calendar', 'v3', credentials=creds)

      start_datetime = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
      end_datetime = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))

      if start_datetime >= end_datetime:
          print("Error: Start time must be before end time.")
          # TODO: pass error back to model
          return False

      print(tool_context.state["time_zone"])

      event = {
          'summary': title,
          'start': {
              'dateTime': start_time,
              'timeZone': tool_context.state["time_zone"],  #  Important: Specify the correct timezone!
          },
          'end': {
              'dateTime': end_time,
              'timeZone': tool_context.state["time_zone"],  # Important: Specify the correct timezone!
          },
      }

      event = service.events().insert(calendarId=tool_context.state["email"], body=event).execute()
      print(f"Event created: {event.get('htmlLink')}")
      return True

  except HttpError as error:
      print(f'An error occurred: {error}')
      return False
  except Exception as e:
      print(f"Error creating event: {e}")
      return False

def external_agent_call():
   """
   """
   return "NA"

def get_today(tool_context: ToolContext):
    """
    Description: Gets today's date.

    Args:
      tool_context (ToolContext)

    Returns:
      today (str): today's date in '%Y-%m-%dT%H:%M:%S%z' format

    """
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    tool_context.state["today"] = now
    return now


def test_creat_cal():
  now = datetime.datetime.now(datetime.timezone.utc).isoformat()
  one_hour_later = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()


  #  Create an event on the service account's primary calendar (if it has one)
  create_calendar_event(
      email='geiger.ljo@gmail.com',
      start_time=now,
      end_time=one_hour_later,
      title='Test Event from Service Account (Primary)',
      description='This is a test event created by a Python script using a service account.',
      location='My Desk'
  )

def test_check_cal():
    conflict_start = "2025-03-07T13:00:00"
    conflict_end = "2025-03-07T13:30:00"

    check_cal(
      start_time=conflict_start,
      end_time=conflict_end,
      tool_context={"state":{"email":"geiger.ljo@gmail.com","time_zone":"America/New_York"},}
  )

test_check_cal()
