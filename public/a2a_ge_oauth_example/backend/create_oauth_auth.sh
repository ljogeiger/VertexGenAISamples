#!/bin/bash
# Reigsters an Authorization resource in Gemini Enterprise

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"sandbox-aiml"}
ENDPOINT_LOCATION=${ENDPOINT_LOCATION:-"global"}
LOCATION=${LOCATION:-"global"}
AUTH_ID="calendar-oauth-auth-7"

# You must set these values before running the script
OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID:-"YOUR_CLIENT_ID"}
OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET:-"YOUR_CLIENT_SECRET"}

if [ "$OAUTH_CLIENT_ID" == "YOUR_CLIENT_ID" ]; then
  echo "Error: Please set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET environment variables or update the script."
  exit 1
fi

# Scopes needed: Google Calendar + Google Calendar Events
# If your agent runs on Vertex AI Agent Engine, you might also need cloud-platform scope.
# Adding cloud-platform, calendar, calendar.events scopes properly URL encoded.
SCOPES="https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.events%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform"

OAUTH_AUTH_URI="https://accounts.google.com/o/oauth2/v2/auth?client_id=${OAUTH_CLIENT_ID}&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=${SCOPES}&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent"

OAUTH_TOKEN_URI="https://oauth2.googleapis.com/token"

echo "Creating Authorization Resource in Gemini Enterprise..."
echo "Project ID: $PROJECT_ID"
echo "Location: $LOCATION"
echo "Auth ID: $AUTH_ID"
echo "Client ID: $OAUTH_CLIENT_ID"
echo "Client Secret: $OAUTH_CLIENT_SECRET"



curl -X POST \
 -H "Authorization: Bearer $(gcloud auth print-access-token)" \
 -H "Content-Type: application/json" \
 -H "X-Goog-User-Project: ${PROJECT_ID}" \
 "https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/authorizations?authorizationId=${AUTH_ID}" \
 -d '{
   "name": "projects/'"${PROJECT_ID}"'/locations/'"${LOCATION}"'/authorizations/'"${AUTH_ID}"'",
   "serverSideOauth2": {
     "clientId": "'"${OAUTH_CLIENT_ID}"'",
     "clientSecret": "'"${OAUTH_CLIENT_SECRET}"'",
     "authorizationUri": "'"${OAUTH_AUTH_URI}"'",
     "tokenUri": "'"${OAUTH_TOKEN_URI}"'"
   }
}'

echo -e "\n\nAuthorization Resource Created. You can now use $AUTH_ID in your register_agent.sh config."
