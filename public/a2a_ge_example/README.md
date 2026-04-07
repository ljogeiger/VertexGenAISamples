# A2A Calendar Agent (Gemini Enterprise Example)

This repository contains an end-to-end example of building, running, and deploying an Agent Development Kit (ADK) 1.x based Agent. The agent natively acts against Google Calendar and AlloyDB, leverages Application Default Credentials (ADC), and can successfully be registered directly with **Gemini Enterprise** via A2A connection.

## Directory Structure
```text
a2a_ge_example/
├── backend/                                  # ADK JSON-RPC Backend Server
│   ├── calendar_agent/                       # Core Agent Definition & Tools
│   │   ├── agent.py                          # Agent configuration
│   │   ├── agent_tools.py                    # Calendar & DB Logic (check_cal, etc.)
│   │   └── user_info.json                    # Hydration config for user preferences
│   ├── a2a_server_calendar_agent.py          # Starlette Server entrypoint
│   ├── deploy_a2a_server.sh                  # Cloud Run deployment script
│   ├── register_agent.sh                     # Agent registry script for Gemini Enterprise
│   ├── requirements.txt                      # Backend dependencies
│   └── Dockerfile                            # Cloud Run configuration
└── frontend/                                 # Chat Client Interface
    ├── a2a_client.py                         # Client hitting the JSON-RPC backend directly
    ├── deploy_frontend.sh                    # Frontend deployment
    └── requirements.txt                      # Frontend dependencies
```

## Key Technologies & Decisions
- **Framework:** Agent Development Kit 1.x (ADK 1.x) JSON-RPC compliant
- **Authentication:** Application Default Credentials (ADC) using Service Account impersonation (no OAuth required)
- **Deployment:** Serverless via Cloud Run (Backend) mapped dynamically into Gemini Enterprise.
- **Event Loop & Latency:** Tool executions utilize `nest_asyncio` locally to gracefully synchronize Google Client API database bindings seamlessly within the core Starlette thread loop. 
- **Telemetry:** Built-in error payloads explicitly surface to the Gemini engine (`{"error": ...}`) for self-healing agent reasoning. *Note: OpenTelemetry is explicitly disabled (`OTEL_SDK_DISABLED=true`) locally to bypass context-var pollution.*

---

## 1. Local Development 

### Credentials Setup (Service Account Impersonation)
We use pure native Application Default Credentials to authenticate directly from your local terminal avoiding complex OAuth loopbacks. 
Ensure you have the `iam.serviceAccountTokenCreator` role on your agent's GCP Service Account.

```bash
# 1. Login with your user account
gcloud auth login

# 2. Impersonate the service account locally for the calendar API tools
gcloud auth application-default login --impersonate-service-account "YOUR_AGENT_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" --scopes="https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/cloud-platform"
```

### Running the Backend locally
Your backend exposes the A2A JSON-RPC interface natively on the default `0.0.0.0:9998` root base path (`/`).
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the backend interface locally
python a2a_server_calendar_agent.py
```

### Running the Frontend locally (Test Client)
In a separate terminal, test the local backend!
```bash
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the adk frontend to test agent interaction dynamically
python a2a_client.py
```

---

## 2. Cloud Deployment

### Deploy Backend to Cloud Run
The deployment leverages the exact identical Service Account configuration used locally to ensure environment parity! 
```bash
cd backend

# Execute deployment
chmod +x ./deploy_a2a_server.sh
./deploy_a2a_server.sh
```

### Register Agent with Gemini Enterprise
Once your Cloud Run endpoint is live, retrieve the dynamic `URL` output (e.g. `https://a2a-calendar-backend-xxxx.a.run.app`) and dynamically register your Agent Engine with Gemini Enterprise:
1. Validate `register_agent.sh` contains the updated Cloud Run `AGENT_URL`.
2. Disable streaming implicitly by setting `capabilities: {"streaming": false}` in the JSON payload of the bash script (Gemini Enterprise handles its own stream).
3. Execute the registration:
```bash
chmod +x ./register_agent.sh
./register_agent.sh
```
 Gemini Enterprise will instantly register the Agent!
