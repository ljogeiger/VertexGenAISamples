gcloud run deploy sample-a2a-agent \
    --port=9998 \
    --source=. \
    --allow-unauthenticated \
    --region="us-central1" \
    --project="sandbox-aiml" \
    --update-secrets=DB_USER=alloy_db_user:latest,DB_PASS=alloy_db_pass:latest \
    --service-account a2a-service-account \
    --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=true,\
GOOGLE_CLOUD_PROJECT="sandbox-aiml",\
GOOGLE_CLOUD_LOCATION="us-central1",\
APP_URL="https://sample-a2a-agent-305610648548.us-central1.run.app",\
USE_ALLOY_DB="True",\
DB_INSTANCE="projects/sandbox-aiml/locations/us-central1/clusters/a2a-taskstate/instances/primary-instance",\
DB_NAME="postgres"
