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
SERVICE_NAME="a2a-frontend-client"

# --- Deployment ---
echo "Deploying service [${SERVICE_NAME}] to Cloud Run..."

# Change to the script's directory to ensure correct context for --source
cd "$(dirname "$0")" && \

# Deploy the service using the source code in the current directory.
# Cloud Build will automatically build and push the image, then deploy it.
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --platform "managed" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --service-account "a2a-client-account@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --port 5000

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform "managed" --region "${REGION}" --format="value(status.url)")

echo " "
echo "✅ Deployment successful!"
echo "✅ Frontend Service URL: ${SERVICE_URL}"