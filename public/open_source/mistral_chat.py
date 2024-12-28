# Doesn't work yet...

import dataclasses
import json
from typing import Callable, Tuple

import gradio as gr
import requests
from google.cloud import aiplatform
import google.auth.transport.requests

MAX_TOKENS = 512

SERVER_TYPE_VLLM = "vllm"
SERVER_TYPE_HEXLLM = "hex-llm"
SERVER_TYPE_TGI = "tgi"
SERVER_TYPES = [
    SERVER_TYPE_VLLM,
    SERVER_TYPE_HEXLLM,
    SERVER_TYPE_TGI,
]


@dataclasses.dataclass
class Endpoint:
    display_name: str
    location: str
    resource_name: str
    server_type: str


PLAYGROUND_ENDPOINTS = []

@dataclasses.dataclass
class DeployConfig:
    display_name: str
    model_name: str
    func: Callable[[str], tuple[aiplatform.Model, aiplatform.Endpoint]]

def getToken():
    creds, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token

def get_server_type(endpoint: aiplatform.Endpoint) -> str | None:
    """Returns the model server type or None if not recognizable."""
    models = endpoint.list_models()
    models: list[aiplatform.Model] = [aiplatform.Model(m.model) for m in models]
    for server_type in SERVER_TYPES:
        if any(server_type in model.container_spec.image_uri for model in models):
            return server_type
    return None


def format_payload(messages: list[dict[str, str]]) -> dict[str, str]:
    return {
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "stream": True,
    }


def list_endpoints() -> list[tuple[str, str]]:
    """Returns all valid prediction endpoints for in the project and region."""
    endpoints = [
        endpoint
        for endpoint in aiplatform.Endpoint.list(order_by="create_time desc")
        if endpoint.traffic_split and get_server_type(endpoint)
    ]
    endpoints = [(e.display_name, e.resource_name) for e in endpoints]
    endpoints.extend((e.display_name, e.resource_name) for e in PLAYGROUND_ENDPOINTS)
    return endpoints


class StreamingClient:
    """A wrapper for a streaming client."""

    endpoint: Endpoint | None = None

    def set_endpoint(self, endpoint: str):
        """Sets the prediction endpoint."""
        playground_endpoint = [
            e for e in PLAYGROUND_ENDPOINTS if e.resource_name == endpoint
        ]
        if not playground_endpoint:
            vertex_endpoint = aiplatform.Endpoint(endpoint)
            server_type = get_server_type(vertex_endpoint)
            self.endpoint = Endpoint(
                display_name=vertex_endpoint.display_name,
                location=vertex_endpoint.location,
                resource_name=endpoint,
                server_type=server_type,
            )
        else:
            self.endpoint = playground_endpoint[0]
        print(
            "Selected endpoint:",
            self.endpoint.resource_name,
            "Server:",
            self.endpoint.server_type,
        )

    def predict(self, message: str, chat_history: list[tuple[str, str]]):
        if not self.endpoint:
            raise gr.Error("Select an endpoint first.")

        url = f"https://{self.endpoint.location}-aiplatform.googleapis.com/v1beta1/{self.endpoint.resource_name}/chat/completions"
        messages = []
        for u, a in chat_history:
            messages.append({"role": "user", "content": u})
            messages.append({"role": "assistant", "content": a})
        messages.append({"role": "user", "content": message})
        payload = format_payload(messages)
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {getToken()}"},
            json=payload,
            stream=True,
        )
        if not response.ok:
            raise gr.Error(response)
        prediction = ""
        for chunk in response.iter_lines(chunk_size=8192, decode_unicode=False):
            if chunk:
                chunk = chunk.decode("utf-8").removeprefix("data:").strip()
                if chunk == "[DONE]":
                    break
                data = json.loads(chunk)
                if type(data) is not dict or "error" in data:
                    raise gr.Error(data)
                delta = data["choices"][0]["delta"].get("content")
                if delta:
                    prediction += delta
                    yield prediction


streaming_client = StreamingClient()


def create_endpoint_selector():
    """Creates a dropdown list of prediction endpoints."""

    with gr.Row():
        endpoints_dropdown = gr.Dropdown(
            list_endpoints(),
            label="Endpoint",
            scale=1,
            info="Only TGI, vLLM, and HexLLM endpoints deployed after August 20, 2024 with a new container image support chat completions and streaming features. "
            + "If you are not sure, you can deploy a demo endpoint directly from below. ",
        )
        endpoints_dropdown.input(
            streaming_client.set_endpoint, inputs=[endpoints_dropdown], outputs=[]
        )
        refresh_btn = gr.Button("Refresh", scale=0)
        refresh_btn.click(
            lambda: gr.Dropdown(choices=list_endpoints()),
            inputs=[],
            outputs=[endpoints_dropdown],
        )




with gr.Blocks(title="Vertex Model Garden Chat", fill_height=True) as demo:
    create_endpoint_selector()
    gr.ChatInterface(streaming_client.predict)


show_debug_logs = True  # @param {type: "boolean"}
demo.queue()
demo.launch(share=True, inline=False, debug=show_debug_logs, show_error=True)
