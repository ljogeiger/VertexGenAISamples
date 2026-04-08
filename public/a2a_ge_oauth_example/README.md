# A2A Calendar Agent (Gemini Enterprise Example)

This repository contains an end-to-end example of building, running, and deploying an Agent Development Kit (ADK) 1.x based Agent integrated deeply with **Gemini Enterprise**.

This `a2a_ge_oauth_example` builds on previous examples by completely dropping Service Account impersonation in production, and instead correctly implementing **OAuth 2.0 Context Propagation** using Gemini Enterprise's native Discovery Engine Authorization configurations.

## Directory Structure
```text
a2a_ge_oauth_example/
├── backend/                                  # ADK JSON-RPC Backend Server
│   ├── calendar_agent/                       # Core Agent Definition & Tools
│   │   ├── agent.py                          # Agent configuration
│   │   ├── agent_tools.py                    # Calendar API logic correctly consuming OAuth tokens
│   │   └── user_info.json                    # Hydration config for user preferences
│   ├── a2a_server_calendar_agent.py          # Starlette Server containing the runtime AgentCard
│   ├── deploy_a2a_server.sh                  # Cloud Run deployment script
│   ├── create_oauth_auth.sh                  # Helper script to create Discovery Engine OAuth resources
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
- **Authentication:** Pure OAuth 2.0 delegated access! The agent parses `Authorization: Bearer <token>` passed down from Genesis Enterprise to authenticate to Google Calendar as the end-user!
- **State Management:** AlloyDB serves as the `DatabaseTaskStore` preserving tasks across runs without needing to hold authentication secrets.
- **Event Loop & Latency:** Tool executions utilize `nest_asyncio` locally to gracefully synchronize Google Client API database bindings seamlessly within the core Starlette thread loop.

Note that we will leverage GE as the frontend to avoid having to create a custom UI and service with Oauth for this example.

---

## 1. Cloud Deployment

### Step A: Deploy Backend to Cloud Run
Because the credentials process is handled cleanly by Gemini Enterprise at runtime, you can immediately deploy the ADK server code directly to Cloud Run:
```bash
cd backend

# Execute deployment
chmod +x ./deploy_a2a_server.sh
./deploy_a2a_server.sh
```

### Step B: Generate the OAuth Client Configuration
1. Open up Google Cloud Console -> **APIs & Services** > **Credentials**.
2. Select **OAuth client ID** -> **Web application**.
3. Under **Authorized redirect URIs**, add `https://vertexaisearch.cloud.google.com/oauth-redirect`.
4. Grab your newly generated Client ID and Client Secret.

### Step C: Register the Application inside Discovery Engine
You must bind those OAuth Settings into the Gemini framework so its UI displays the consent screen.
1. Export your properties and run the creation script:
```bash
export OAUTH_CLIENT_ID="<your_client_id_here>"
export OAUTH_CLIENT_SECRET="<your_client_secret_here>"

chmod +x ./create_oauth_auth.sh
./create_oauth_auth.sh
```
2. The script will echo an `AUTH_ID` like: `projects/YOUR_PROJECT_ID/locations/global/authorizations/calendar-oauth-auth-X`. Keep this copied!

### Step D: Register the Agent with Gemini Enterprise
Now connect your live Cloud Run instance to Gemini, pointing it directly at the OAuth configuration.
1. Make sure `backend/a2a_server_calendar_agent.py` accurately defines the target scopes in its `AgentCard` `security` configuration. (By default this covers `.calendar` and `.events`).
2. Inside `register_agent.sh`, make sure `AGENT_URL` is set to the Cloud Run URL URL you generated in Step A.
3. Update `AUTH_ID` inside `register_agent.sh` to the literal `projects/../authorizations/calendar-oauth-auth-X` string generated in *Step C*.
4. Execute the registration:
```bash
chmod +x ./register_agent.sh
./register_agent.sh
```
 Gemini Enterprise will instantly register the Agent!

---

## 2. Local Development

For isolated local testing directly pushing payloads to `--port 9998` without invoking the true UI:
Because Gemini Enterprise isn't passing a Bearer Token to you locally, `agent_tools.py` will defensively fallback to using standard "Application Default Credentials" (ADC).

```bash
# Force fallback ADC for local un-credentialed calendar interactions
gcloud auth application-default login

# Start server
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python a2a_server_calendar_agent.py
```
