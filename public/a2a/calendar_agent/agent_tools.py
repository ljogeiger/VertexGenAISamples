from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.adk.tools import ToolContext
from googleapiclient.errors import HttpError
from vertexai import agent_engines

from google.api_core import exceptions as google_exceptions

import datetime, json, logging

SERVICE_ACCOUNT_FILE = './calendar_agent/sandbox-aiml-193fff073cd4.json'  # Replace with your service account key file
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_cal_creds(user_to_impersonate):
  SCOPES = ['https://www.googleapis.com/auth/calendar']

  creds = None
  # Use service account credentials
  try:
      creds = service_account.Credentials.from_service_account_file(
          SERVICE_ACCOUNT_FILE,
          scopes=SCOPES,
          subject=user_to_impersonate)
  except Exception as e:
      print(f"Error loading service account credentials: {e}")
      return False

  if not creds:  # Check if credentials were loaded successfully
      print("Error: Service account credentials could not be loaded.")
      return False
  return creds

def check_cal(
        tool_context: ToolContext,
        start_time: str,
        end_time: str) -> list:
    """
    Description: This function returns a list of events, if any, that conflict with the
    given start_time and end_time.

    Args:
      tool_context: The tool context, containing user information like email.
      start_time (str): the start date and time of the event (ISO 8601 format, e.g., "2025-03-06T13:00:00-05:00").
      end_time (str): the end date and time of the event (ISO 8601 format).

    Return:
      event_list (list): a list of events (dictionaries) that conflict with the given start_time and end_time.
        If no events conflict, event_list is an empty list.
    """
    try:
        # Authenticate and build the service
        creds = get_cal_creds(tool_context.state["email"])
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

            # Create time_min and time_max with proper timezone handling
            time_min = (start_dt_localized - datetime.timedelta(days=1)).isoformat()
            time_max = (end_dt_localized + datetime.timedelta(days=1)).isoformat()

        except Exception as e:
            print(f"Error handling timezone: {e}.  Using UTC.") # Fallback
            # For UTC fallback, ensure we don't double-append timezone info
            time_min = (start_dt - datetime.timedelta(days=1)).isoformat()
            time_max = (end_dt + datetime.timedelta(days=1)).isoformat()
            
            # Only append 'Z' if the datetime doesn't already have timezone info
            if time_min.endswith('+00:00'):
                time_min = time_min.replace('+00:00', 'Z')
            elif not time_min.endswith('Z') and not ('+' in time_min or '-' in time_min[-6:]):
                time_min += 'Z'
                
            if time_max.endswith('+00:00'):
                time_max = time_max.replace('+00:00', 'Z')
            elif not time_max.endswith('Z') and not ('+' in time_max or '-' in time_max[-6:]):
                time_max += 'Z'


        # --- Fetch Events ---
        logging.info(f"Fetching events with timeMin: {time_min}, timeMax: {time_max}")
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

def get_user_profile(tool_context):
  """
  Reads user data from a JSON file.

  Args:
      filepath (str, optional): The path to the JSON file.

  Returns:
      dict: A dictionaries, which includes first name, last name, email, time zone, and preferences.
            Returns an empty list if the file doesn't exist or is invalid JSON.
  """
  logging.info("Getting user profile")
  filepath = "./calendar_agent/user_info.json"
  today = get_today()
  try:
      with open(filepath, 'r') as f:
          data = json.load(f)
          tool_context.state["first_name"] = data["first_name"]
          tool_context.state["last_name"] = data["last_name"]
          tool_context.state["email"] = data["email"]
          tool_context.state["time_zone"] = data["time_zone"]
          tool_context.state["double_book"] = data["double_book"]
          tool_context.state["today"] = today
          logging.info(tool_context)
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

def create_event_with_details(
        tool_context: ToolContext,
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
    start_time (str): the start date and time of the event (ISO 8601 format, e.g., "2024-03-15T09:00:00-08:00").
    end_time (str): the end date and time of the event (ISO 8601 format).
    title (str): The title of the event.
    description (str, optional): The description of the event. Defaults to "".
    location (str, optional): The location of the event. Defaults to "".
    attendees (list, optional): The list of attendees. Can be empty. Ex. ["johndoe@gmail.com","taylorsmith@gmail.com"]

  Return:
    success (bool): True if successfully created event, False if not.
  """

  creds = get_cal_creds(tool_context.state["email"])

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

      event = service.events().insert(calendarId=tool_context["email"], body=event).execute()
      print(f"Event created: {event.get('htmlLink')}")
      return True

  except HttpError as error:
      print(f'An error occurred: {error}')
      return False
  except Exception as e:
      print(f"Error creating event: {e}")
      return False

def create_calendar_event(
        start_time: str,
        end_time: str,
        title: str,
        tool_context: ToolContext) -> bool:
  """
  Description: Create a Google Calendar event.

  Args:
    start_time (str): the start date and time of the event (ISO 8601 format, e.g., "2024-03-15T09:00:00-08:00").
    end_time (str): the end date and time of the event (ISO 8601 format).
    title (str): The title of the event.

  Return:
    success (bool): True if successfully created event, False if not.

  Example:
  create_calendar_event(
      start_time='2025-23-02T12:00:00',
      end_time='2025-23-02T12:30:00',
      title='Test Event') -> True
  """

  creds = get_cal_creds(tool_context.state["email"])


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

def get_today():
    """
    Description: Gets today's date.

    Args:
      tool_context (ToolContext)

    Returns:
      today (str): today's date in '%Y-%m-%dT%H:%M:%S%z' format

    """
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    return now

def external_user_check_cal(
        external_user: str,
        start_time: str,
        end_time: str,
        tool_context: ToolContext):
    """
    Description:
      This function is used to check external user's calendar events.
      It first looks up the mapping of user to agent engine endpoint using user_to_cal_agent.json.
      Then we communicate with the agent at the agent engine endpoint to check the user's calendar.

    Args:
      external_user (str): this is the calendar invitee's email address
      start_time (str): the start date and time of the event (ISO 8601 format, e.g., "2025-03-06T13:00:00-05:00").
      end_time (str): the end date and time of the event (ISO 8601 format).

    Returns:
      event_list (list): a list of events (dictionaries) that conflict with the given start_time and end_time.
        If no events conflict, event_list is an empty list.
        If it failed, we return a list with -1.
    """

    MAPPING_FILE_PATH = "./calendar_agent/user_to_cal_agent.json"
    logging.info(f"Starting calendar check for user='{external_user}' between {start_time} and {end_time}")

    # 1. Load Mapping
    user_to_agent_map = None
    try:
        # Log before file access
        logging.info(f"Attempting to load user-to-agent mapping from: {MAPPING_FILE_PATH}")
        with open(MAPPING_FILE_PATH, 'r') as f:
            user_to_agent_map = json.load(f)
        logging.info(f"Successfully loaded mapping file. Found {len(user_to_agent_map)} entries.")
    except FileNotFoundError:
        logging.error(f"Mapping file not found at: {MAPPING_FILE_PATH}")
        logging.info(f"Returning empty list due to missing mapping file.")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from mapping file {MAPPING_FILE_PATH}: {e}")
        logging.info(f"Returning empty list due to corrupted mapping file.")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred reading mapping file {MAPPING_FILE_PATH}: {e}", exc_info=True) # Add traceback
        logging.info(f"Returning empty list due to unexpected file reading error.")
        return []

    # 2. Find Endpoint
    agent_endpoint = user_to_agent_map.get(external_user)
    if not agent_endpoint:
        logging.warning(f"No agent engine endpoint found for user='{external_user}' in {MAPPING_FILE_PATH}")
        logging.info(f"Returning empty list because user was not found in mapping.")
        return [-1]
    logging.info(f"Found agent endpoint for user='{external_user}': {agent_endpoint}")

    # 3. Get Agent Object
    external_user_agent = agent_engines.get(agent_endpoint)
    if not external_user_agent:
        logging.error(f"Agent engine object not found in 'agent_engines' for endpoint='{agent_endpoint}' (user='{external_user}')")
        logging.info(f"Returning failure indicator [-1] because agent object could not be retrieved.")
        return [-1] # Indicate failure since we found the user but couldn't get the agent
    logging.info(f"Successfully retrieved agent object for endpoint='{agent_endpoint}'")

     # 4. Call the agent to check the calendar.
     #    --- Added specific exception handling for NotFound ---

     # Get session
    user_id = tool_context.state["email"]
    session = external_user_agent.create_session(user_id=user_id)
    session_id = session["id"]

    response = []
    query_input = f"EXTERNAL_CAL_REQUEST: start_time:{start_time}, end_time: {end_time}"
    try:
        logging.info(f"Querying agent for user='{external_user}' via endpoint '{agent_endpoint}' with input: {query_input}")
        for event in external_user_agent.stream_query(user_id=user_id,
                                                      session_id=session_id,
                                                      message=query_input):
            response.append(event)
            logging.info(f"Event Stream {external_user}: {event}")

        logging.info(f"Raw response received from agent for user='{external_user}': {response}")

    # --- Specific handling for Google Cloud Resource Not Found ---
    except google_exceptions.NotFound as e:
        logging.error(
            f"Google Cloud Resource Not Found (404) encountered querying agent for user='{external_user}' "
            f"using endpoint='{agent_endpoint}'. This likely means the underlying Reasoning Engine "
            f"(e.g., '{e.message.split(' ')[1]}') is deleted, invalid, or inaccessible with current credentials.",
            exc_info=False # Keep traceback minimal for this specific, known error type unless needed
        )
        # Log the original error detail if helpful for debugging the specific resource path
        logging.error(f"Original NotFound error detail: {e}")
        logging.warning(f"Returning failure indicator [-1] for user='{external_user}' due to resource not found.")
        return [-1] # Indicate failure

    # --- General exception handling ---
    except Exception as e:
        # Catch any other exception during the agent query
        logging.error(f"An unexpected error occurred querying the agent for user='{external_user}' at endpoint='{agent_endpoint}': {e}", exc_info=True) # Log traceback
        logging.warning(f"Returning failure indicator [-1] for user='{external_user}' due to unexpected agent query error.")
        return [-1] # Indicate failure

    # 5. Process and Return Response
    # Check if response is considered empty/invalid based on expected format
    # Assuming an empty list [] is a valid 'no conflicts' response,
    # but None or "" indicates a failure from the agent's perspective.
    if response is None or response == []: # Adjust this check based on actual agent failure modes
        logging.warning(f"Agent query for user='{external_user}' returned an empty/invalid response (None or empty string).")
        logging.info(f"Returning failure indicator [-1].")
        return [-1]
    else:
        # Assuming response is the list of events on success
        try:
            response_len = len(response) if isinstance(response, list) else 'N/A (not a list)'
            logging.info(f"Agent query for user='{external_user}' successful. Response type: {type(response)}, Length: {response_len}.")
            logging.info(f"Returning response for user='{external_user}'.")
            return response
        except Exception as e: # Catch errors during length check etc. just in case
            logging.error(f"Error processing successful agent response for user='{external_user}': {e}", exc_info=True)
            logging.info(f"Returning failure indicator [-1] due to response processing error.")
            return [-1]

def create_multi_cal_event(
    start_time: str,
    end_time: str,
    title: str,
    invite_list: list,
    tool_context: ToolContext,
):
    """
    Description:
      Create google calendar event with multiple people.

      This function assumes the check calendars has already been preformed.
    Args:
      start_time (str): the start data and time of the event (ISO 8601 format, e.g., "2024-03-15T09:00:00-08:00").
      end_time (str): the end data and time of the event (ISO 8601 format).
      title (str): The title of the event.
      invite_list (list): list of people invited to the event.

    Return:
      success (bool): True if successfully created event, False if not.
    """
    logging.info(f"Attempting to create event '{title}' on calendar '{tool_context.state["email"]}'")
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    # --- 1. Load Service Account Credentials ---
    creds = get_cal_creds(tool_context.state["email"])

    # Double check if credentials loaded - should be caught above, but good practice
    if not creds:
        logging.error("ERROR: Service account credentials could not be loaded (creds object is None).")
        return False

    # --- 2. Build Google Calendar Service Client ---
    try:
        service = build('calendar', 'v3', credentials=creds)
        logging.info("Google Calendar API service client created successfully.")
    except Exception as e:
        logging.error(f"ERROR: Building Google Calendar service client: {e}")
        return False

    # --- 3. Prepare Event Data ---
    try:
        # Validate time format and order using datetime
        # Note: datetime.fromisoformat handles timezone offsets including 'Z'
        start_datetime = datetime.datetime.fromisoformat(start_time)
        end_datetime = datetime.datetime.fromisoformat(end_time)

        if start_datetime >= end_datetime:
            logging.error(f"ERROR: Start time ({start_time}) must be before end time ({end_time}).")
            return False # Return False as per requirement

    except ValueError:
        logging.error(f"ERROR: Invalid ISO 8601 format for start_time ('{start_time}') or end_time ('{end_time}').")
        return False

    # Format attendees list for the API
    attendees = []
    if invite_list and isinstance(invite_list, list):
        for email in invite_list:
            if isinstance(email, str) and '@' in email: # Basic validation
                attendees.append({'email': email})
            else:
                logging.warning(f"Skipping invalid invitee item: {email}")
    else:
         logging.info("No valid invitees provided in invite_list.")

    # Add creator email to invite
    attendees.append({'email': tool_context.state["email"]})

    print(attendees)

    # Construct the event body
    # The timezone for the event is taken directly from the ISO 8601 dateTime strings
    event_body = {
        'summary': title,
        'start': {
            'dateTime': start_time,
            # 'timeZone': 'America/New_York' # Explicit timezone (optional if dateTime has offset)
        },
        'end': {
            'dateTime': end_time,
            # 'timeZone': 'America/New_York' # Explicit timezone (optional if dateTime has offset)
        },
        'attendees': attendees,
        # You can add more details like description, location, conference data etc.
        # 'description': 'This is a meeting description.',
        # 'location': 'Conference Room A',
        #  'reminders': { # Example: Add default reminders
        #     'useDefault': False,
        #     'overrides': [
        #         {'method': 'popup', 'minutes': 15},
        #     ],
        # },
    }

    # --- 4. Insert Event via API ---
    try:
        logging.info(f"Sending request to create event: {title}")
        created_event = service.events().insert(
            calendarId=tool_context.state["email"],
            body=event_body,
            sendUpdates='none' # Send notifications to attendees ('all', 'externalOnly', 'none')
            # sendNotifications=True is deprecated but still works; sendUpdates is preferred
        ).execute()

        logging.info(f"Event created successfully. ID: {created_event.get('id')}, Link: {created_event.get('htmlLink')}")
        return True # Indicate success

    except HttpError as error:
        # Try to get more details from the error response
        error_details = "(No specific error details found in response)"
        try:
            content = json.loads(error.content.decode('utf-8'))
            error_details = content.get('error', {}).get('message', error_details)
        except:
            # Fallback if content is not JSON or doesn't have expected structure
             error_details = f"Raw Response: {error.content.decode('utf-8')[:500]}..." # Log first 500 chars

        logging.error(f"ERROR: An API error occurred creating the event: {error.resp.status} - {error_details}")
        return False # Indicate failure
    except Exception as e:
        # Catch any other unexpected exceptions during API call or processing
        logging.error(f"ERROR: An unexpected error occurred creating the event: {e}")
        return False # Indicate failure
    return

def test_create_cal():
  now = datetime.datetime.now(datetime.timezone.utc).isoformat()
  one_hour_later = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()


  #  Create an event on the service account's primary calendar (if it has one)
  create_calendar_event(
      start_time=now,
      end_time=one_hour_later,
      title='Test Event from Service Account (Primary)',
      description='This is a test event created by a Python script using a service account.',
      location='My Desk',
      tool_context={"state":{"email":"admin@lukasgeiger.altostrat.com","time_zone":"America/New_York"}}
  )

def test_check_cal():
    conflict_start = "2025-03-07T13:00:00"
    conflict_end = "2025-03-07T13:30:00"

    check_cal(
      start_time=conflict_start,
      end_time=conflict_end,
      tool_context={"state":{"email":"admin@lukasgeiger.altostrat.com","time_zone":"America/New_York"}}
  )

def test_create_multi_cal():
    try:
      from zoneinfo import ZoneInfo # Requires Python 3.9+ and tzdata package (`pip install tzdata`)
      ny_tz = ZoneInfo("America/New_York")
      now_ny = datetime.datetime.now(ny_tz)

      # Schedule for tomorrow 2 PM - 3 PM New York time
      start_event_dt = now_ny.replace(hour=14, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
      end_event_dt = start_event_dt + datetime.timedelta(hours=1)

      start_iso = start_event_dt.isoformat()
      end_iso = end_event_dt.isoformat()

      print(f"Scheduling event from {start_iso} to {end_iso}")

      event_title = "Project Sync Meeting (Created via API)"
      invitees = ["geiger.ljo@lukasgeiger.altostrat.com"] # Add valid emails for testing

      # Call the function - using default 'primary' calendar ID
      success = create_multi_cal_event(
          start_time=start_iso,
          end_time=end_iso,
          title=event_title,
          invite_list=invitees,
          tool_context={"state":{"email":"admin@lukasgeiger.altostrat.com","time_zone":"America/New_York"}},
      )

      if success:
          print("\nSUCCESS: Event creation process completed successfully.")
      else:
          print("\nFAILURE: Event creation process failed. Check logs for details.")

    except ImportError:
      print("\nNOTE: 'zoneinfo' (Python 3.9+) or 'tzdata' package not available.")
      print("Cannot generate dynamic timezone-aware timestamps for example.")
      print("Please manually provide valid ISO 8601 strings for start_time and end_time if running this example.")
    except Exception as e:
      print(f"\nAn error occurred during the example run setup: {e}")
