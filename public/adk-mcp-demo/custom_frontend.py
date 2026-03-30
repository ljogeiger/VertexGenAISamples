import os
import json
import asyncio
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.plugins.base_plugin import BasePlugin
from google.genai.types import Content, Part

# Load the environment keys for Vertex AI explicitly
load_dotenv("my_agent/.env")

# Must import Root Agent directly
from my_agent.agent import root_agent

app = FastAPI()

with open("index.html", "r") as f:
    html_content = f.read()

class ProgressProxyPlugin(BasePlugin):
    """
    Custom plugin to inject a shared event_queue into the InvocationContext.
    This allows tools to use enqueue_event() even if the standard Runner
    doesn't natively initialize it.
    """
    def __init__(self, external_queue: asyncio.Queue):
        super().__init__(name="progress_proxy")
        self.external_queue = external_queue

    async def on_user_message_callback(self, invocation_context, user_message):
        # Attach the shared queue to the context so enqueue_event() works
        invocation_context.event_queue = self.external_queue
        return None

@app.get("/")
async def serve_frontend():
    """Serves the static index.html UI"""
    return HTMLResponse(html_content)

@app.get("/chat")
async def chat_sse(message: str):
    """
    Streams both natural ADK events and manual tool progress events via SSE.
    """
    async def event_generator():
        print(f"--- Starting ADK Generator for message: {message} ---")
        
        # This queue will receive manual events from tool-level enqueue_event()
        mcp_progress_queue = asyncio.Queue()
        # This queue will merge both natural ADK events and manual ones
        combined_queue = asyncio.Queue()
        
        runner = Runner(
            agent=root_agent,
            session_service=InMemorySessionService(),
            app_name="demo_app",
            auto_create_session=True,
            plugins=[ProgressProxyPlugin(mcp_progress_queue)]
        )

        async def produce_adk():
            """Producer task for natural ADK Runner events."""
            try:
                msg = Content(role="user", parts=[Part(text=message)])
                async for event in runner.run_async(user_id="demo_user", session_id="demo_sess", new_message=msg):
                    await combined_queue.put(event)
            except Exception as e:
                print(f"Runner Error: {e}")
            finally:
                # Signal that the main runner is done
                await combined_queue.put(None)

        async def produce_manual():
            """Producer task for manual enqueue_event() tool updates."""
            while True:
                try:
                    item = await mcp_progress_queue.get()
                    event, processed_signal = item
                    
                    print(f">>> Manual Progress Event captured")
                    await combined_queue.put(event)
                    
                    if processed_signal:
                        processed_signal.set()
                except Exception as e:
                    print(f"Manual Queue Error: {e}")
                    break

        # Start producers in the background
        adk_task = asyncio.create_task(produce_adk())
        manual_task = asyncio.create_task(produce_manual())

        try:
            while True:
                # Wait for the next event from either source
                event = await combined_queue.get()
                
                # Check for the completion sentinel from produce_adk
                if event is None:
                    break
                
                data = event.model_dump_json(by_alias=True)
                yield f"data: {data}\n\n"
        finally:
            # Cleanup background tasks
            adk_task.cancel()
            manual_task.cancel()
            print("--- ADK Generator Finished ---")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("Serving custom ADK UI at http://127.0.0.1:8002")
    uvicorn.run(app, host="127.0.0.1", port=8002)
