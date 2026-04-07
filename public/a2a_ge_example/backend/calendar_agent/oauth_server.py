
import flask
import google_auth_oauthlib.flow
import os
import json
import sqlalchemy
import asyncio
from . import agent_tools

app = flask.Flask(__name__)

# --- OAuth 2.0 Configuration ---
# Scopes define the level of access the application is requesting.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]

# This information is loaded from environment variables, which are securely
# set by the Cloud Run deployment script (from Secret Manager).
CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")

# This is the client configuration in the format google-auth-oauthlib expects.
CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [
            # This will be dynamically set later, but a placeholder is good practice.
            "https://placeholder.a.run.app/oauth2/callback"
        ]
    }
}

async def save_token_to_db(user_id: str, credentials, engine: sqlalchemy.ext.asyncio.engine.AsyncEngine):
    """Saves a user's token to the AlloyDB database."""
    async with engine.connect() as conn:
        await conn.execute(
            sqlalchemy.text("INSERT INTO oauth_tokens (user_id, access_token, refresh_token, expires_at) VALUES (:user_id, :access_token, :refresh_token, :expires_at) ON CONFLICT (user_id) DO UPDATE SET access_token = :access_token, refresh_token = :refresh_token, expires_at = :expires_at"),
            {"user_id": user_id, "access_token": credentials.token, "refresh_token": credentials.refresh_token, "expires_at": credentials.expiry},
        )

@app.route('/oauth2/authorize')
def authorize():
    """Starts the OAuth 2.0 authorization flow."""
    if not CLIENT_ID or not CLIENT_SECRET:
        return "Error: OAuth client ID or secret is not configured.", 500

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    flask.session['state'] = state

    return flask.redirect(authorization_url)

@app.route('/oauth2/callback')
def oauth2callback():
    """Handles the OAuth 2.0 callback after the user grants consent."""
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    
    # TODO: Get the user_id from the session or some other secure mechanism
    user_id = "test_user"
    asyncio.run(save_token_to_db(user_id, credentials, agent_tools.engine))

    return "Authentication successful! You can close this window."

if __name__ == '__main__':
    # This server is intended to be run by the main a2a_server_calendar_agent.py
    # and not directly. For local testing, you would need to set the
    # OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET environment variables.
    if not CLIENT_ID or not CLIENT_SECRET:
        print("FATAL: OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET environment variables must be set.")
    else:
        app.run(port=8080, debug=True)
