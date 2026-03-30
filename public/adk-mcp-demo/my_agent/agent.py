from google.adk.events.event import Event
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

# Define a factory that receives the ADK tool_context whenever a tool is called.
# It returns the actual progress handler that FastMCP calls (which only takes progress, total, message).
def get_progress_callback(tool_name, callback_context, **kwargs):
    async def handle_tool_progress(progress, total, message):
        # 1. Update session state for persistence
        update_data = {
            'progress': progress,
            'message': message,
            'total': total
        }
        callback_context.state['tool_update'] = update_data

        # 2. Manually enqueue a partial event for REAL-TIME streaming to frontend
        # 'state' kwarg in Event constructor maps to actions.state_delta
        event = Event(state={'tool_update': update_data}, partial=True)

        # Use the underlying invocation context to reach the Runner's event queue
        if hasattr(callback_context, '_invocation_context'):
             await callback_context._invocation_context.enqueue_event(event)

        print(f"[{tool_name} Progress] {message} ({int(progress*100)}%)")
    return handle_tool_progress

# Point the MC PToolset to the MCP Server running on port 8003
toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="http://localhost:8003/mcp"),
    progress_callback=get_progress_callback
)

# Initialize the Gemini agent, equipped with our orchestrating toolset
root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="my_agent",
    tools=[toolset],
    description="I am a specialized agent that connects to remote tools and streams their progress live."
)
