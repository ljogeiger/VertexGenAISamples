#!/bin/bash
# Registers an A2A agent with Gemini Enterprise using the A2A API REST interface

# Ensure script halts on unhandled errors
set -e

# Configuration variables
PROJECT_ID=${GCP_PROJECT_ID:-"sandbox-aiml"}
APP_ID=${APP_ID:-"calendar-a2a_1753717882831"}
ENDPOINT_LOCATION=${ENDPOINT_LOCATION:-"global"} # 'us', 'eu', or 'global'
LOCATION=${LOCATION:-"global"} # 'us', 'eu', or 'global'

AGENT_NAME="calendar-a2a-agent"
AGENT_DISPLAY_NAME="Calendar A2A Agent - April 2026"
AGENT_DESCRIPTION="A2A Agent that manages your calendar."

# IMPORTANT: You must update this URL with the actual Cloud Run URL output from deploy_a2a_server.sh
AGENT_URL="https://a2a-calendar-backend-ypnjpxxv7q-uc.a.run.app"

echo "Registering A2A Agent with Gemini Enterprise..."
echo "Project ID: $PROJECT_ID"
echo "App ID: $APP_ID"
echo "Agent URL: $AGENT_URL"

# Execute the curl command to register the agent
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents" \
  -d '{
    "name": "'"${AGENT_NAME}"'",
    "displayName": "'"${AGENT_DISPLAY_NAME}"'",
    "description": "'"${AGENT_DESCRIPTION}"'",
    "a2aAgentDefinition": {
      "jsonAgentCard": "{\"protocolVersion\":\"0.3.0\",\"name\":\"'"${AGENT_NAME}"'\",\"description\":\"'"${AGENT_DESCRIPTION}"'\",\"url\":\"'"${AGENT_URL}"'\",\"version\":\"1.0.0\",\"defaultInputModes\":[\"text\"],\"defaultOutputModes\":[\"text\"],\"capabilities\":{\"streaming\":false},\"skills\":[{\"id\":\"calendar_agent\",\"name\":\"Calendar Agent\",\"description\":\"Helps manage and schedule calendar events.\",\"tags\":[\"calendar\",\"scheduling\",\"events\"],\"examples\":[\"schedule a meeting\",\"find free time\",\"create event\"]}]}"
    }
  }'

echo -e "\n\nRegistration request completed."
