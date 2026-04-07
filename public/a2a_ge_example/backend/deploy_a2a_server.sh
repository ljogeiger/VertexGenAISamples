#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
if [ -z "${GCP_PROJECT_ID}" ]; then
  GCP_PROJECT_ID="$(gcloud config get-value project)"
fi

if [ -z "${GCP_PROJECT_ID}" ]; then
  echo "Error: Google Cloud project ID is not set."
  echo "Please set the GCP_PROJECT_ID environment variable or run 'gcloud config set project YOUR_PROJECT_ID'"
  exit 1
fi

REGION="us-central1"
SERVICE_NAME="a2a-calendar-backend"

# --- Deployment ---
echo "Deploying service [${SERVICE_NAME}] to Cloud Run in project [${GCP_PROJECT_ID}]..."

cd "$(dirname "$0")"

SERVICE_ACCOUNT="lukasgeiger-calendar-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Deploys the service using the source code in the current directory.
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --platform "managed" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 9998 \
  --service-account="${SERVICE_ACCOUNT}" \
  --update-secrets=\
ALLOYDB_USER=alloy_db_user:latest,\
ALLOYDB_PASS=alloy_db_pass:latest \
  --set-env-vars=\
"GOOGLE_CLOUD_PROJECT=${GCP_PROJECT_ID}",\
"GOOGLE_CLOUD_LOCATION=${REGION}",\
"ALLOYDB_INSTANCE=primary-instance",\
"ALLOYDB_NAME=postgres",\
"ALLOYDB_REGION=${REGION}",\
"ALLOYDB_CLUSTER=a2a-taskstate"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform "managed" --region "${REGION}" --format="value(status.url)")

echo " "
echo "✅ Deployment successful!"
echo "✅ Backend Service URL: ${SERVICE_URL}"
echo " "
echo "To register this agent to Gemini Enterprise, run './register_agent.sh'."
echo "Before registering, update your AGENT_URL in register_agent.sh to be: ${SERVICE_URL}/api/a2a"
