
import httpx
from flask import Flask, render_template, request, redirect, session, url_for
import os
import uuid
import asyncio
import json
import logging

from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, AgentCard

app = Flask(__name__)
app.secret_key = os.urandom(24)

A2A_SERVER_URL = "http://127.0.0.1:9998"

logging.basicConfig(level=logging.INFO)

async def get_agent_card():
    """Fetches the agent card from the server."""
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(f"{A2A_SERVER_URL}/.well-known/agent.json")
        response.raise_for_status()
        return AgentCard(**response.json())

async def handle_request(user_input, session_data):
    """This function contains all the async logic."""
    logging.info("--- Starting handle_request ---")
    history = session_data.get('history', [])
    contextId = session_data.get('contextId')

    try:
        logging.info(f"Fetching agent card from: {A2A_SERVER_URL}/.well-known/agent.json")
        agent_card = await get_agent_card()
        # Override the agent_card's internal URL so the client doesn't try to route to the backend's dummy default "example.com"
        agent_card.url = A2A_SERVER_URL
        logging.info(f"Successfully fetched agent card. RPC URL: {agent_card.url}")

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            a2a_client = A2AClient(httpx_client=http_client, agent_card=agent_card)

            message_params = {
                'message': {
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': user_input}],
                    'messageId': uuid.uuid4().hex,
                }
            }
            if contextId:
                message_params['message']['contextId'] = contextId

            send_request = SendMessageRequest(
                id=str(uuid.uuid4()), params=MessageSendParams(**message_params)
            )
            
            logging.info(f"Sending message to: {agent_card.url}")
            response = await a2a_client.send_message(send_request)
            logging.info(f"Received response: {response.model_dump_json(indent=2)}")

            new_contextId = response.root.result.contextId
            new_taskId = response.root.result.id
            agent_response_text = ""
            
            # The A2AStarletteApplication natively returns a Task object even for synchronous completions.
            if getattr(response.root.result, 'history', None) and len(response.root.result.history) > 0:
                last_message = response.root.result.history[-1]
                if last_message.parts:
                    part_data = last_message.parts[0].model_dump()
                    agent_response_text = part_data.get('text', str(part_data))

            history.append({"role": "agent", "text": agent_response_text})
            return {"history": history, "contextId": new_contextId, "taskId": new_taskId}

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTPStatusError: {e.response.status_code} - {e.response.text}", exc_info=True)
        history.append({"role": "agent", "text": f"Error: {e.response.text}"})
        return {"history": history}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        history.append({"role": "agent", "text": f"An unexpected error occurred: {e}"})
        return {"history": history}

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'history' not in session:
        session['history'] = []
        session['contextId'] = None
        session['taskId'] = None

    if request.method == 'POST':
        user_input = request.form['query']
        session['history'].append({"role": "user", "text": user_input})

        # Run the async logic and get the result
        result = asyncio.run(handle_request(user_input, dict(session)))

        # Update the session with the new data
        session['history'] = result.get('history', session['history'])
        session['contextId'] = result.get('contextId', session['contextId'])
        session['taskId'] = result.get('taskId', session['taskId'])

        return redirect(url_for('index'))

    return render_template('index.html', history=session['history'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
