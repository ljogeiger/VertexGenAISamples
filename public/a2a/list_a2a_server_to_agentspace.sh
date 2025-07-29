curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" https://discoveryengine.googleapis.com/v1alpha/projects/305610648548/locations/global/collections/default_collection/engines/calendar-a2a_1753717882831/assistants/default_assistant/agents -d '
{
  "name": "Calendar Agent",
  "displayName": "A2A Calendar Agent",
  "description": "Create calendar events",
  "a2aAgentDefinition": {
     "jsonAgentCard": "{\"provider\": {\"url\": \"https://sample-a2a-agent-305610648548.us-central1.run.app\"},\"name\": \"Calendar Agent\",\"description\": \"A smart agent for managing calendar events and scheduling.\"}"
     }
}'