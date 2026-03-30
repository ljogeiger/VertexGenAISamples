# ADK 2.0 Real-Time MCP Progress Streaming

This project demonstrates how to enable **real-time progress updates** from an external **MCP server** (via `FastMCP`) to an **ADK 2.0 agent** and visualize them in a custom frontend.

## The Problem: ADK Web vs. Real-Time Streaming
The standard `adk web` (ADK 2.0 Dev UI) is designed to show high-level agent traces. It typically only updates the UI when a node (like a tool) completes. It intentionally filters out granular `stateDelta` updates and partial event streams that occur *during* a tool execution to keep the trace clean. 

To see real-time progress (e.g., "Processing chunk 3/10"), we need to:
1.  **Emit manual events** during tool execution.
2.  **Bypass the standard Dev UI** filters using a custom frontend.

## How it was Implemented

### 1. The MCP Transport
We updated `mcp_server.py` to use the **Streamable HTTP** transport (2025-06-18 MCP specification). This allows the server to use `ctx.report_progress(progress, total, message)` which sends HTTP chunks back to the client.

### 2. The ADK Agent Integration (`my_agent/agent.py`)
- **McpToolset**: Configured with `StreamableHTTPConnectionParams` to connect to the MCP server.
- **ProgressCallback**: We implemented a `progress_callback` factory. When the MCP server reports progress, this callback is triggered.
- **Manual Event Enqueuing**: Inside the callback, we manually create an `Event` with the progress data and call `invocation_context.enqueue_event(event, partial=True)`. This pushes a "partial" update into the agent's event stream immediately, without waiting for the tool to finish.

### 3. The Custom Plumbing (`custom_frontend.py`)
The ADK 2.0 Alpha `Runner` doesn't automatically initialize the `event_queue` on the `InvocationContext` for manual `enqueue_event()` calls. We solved this with:
- **ProgressProxyPlugin**: A custom `BasePlugin` that intercepts the invocation start and injects a shared `asyncio.Queue` into the context.
- **Merged Generator**: The FastAPI backend concurrently consumes from both the natural `Runner.run_async()` generator and the manual `mcp_progress_queue`, merging them into a single SSE (Server-Sent Events) stream.

### 4. The Custom UI (`index.html`)
A vanilla JS frontend that:
- Connects to the `/chat` SSE endpoint.
- Listens for `stateDelta` JSON updates.
- Dynamically extracts the `tool_update` field and appends it to an activity log in real-time.

---

## How to Run

### 1. Start the MCP Server
```bash
./start_mcp.sh
```
(Running on port 8003 by default)

### 2. Start the Custom Frontend
```bash
/Users/lukasgeiger/Desktop/VertexGenAISamples/adk2.0-alpha/bin/python custom_frontend.py
```
(Running on port 8002)

### 3. Test the Progress
Open `http://localhost:8002` in your browser and type:
> "Test the process_data tool on 'input data'"

You will see the progress chunks appearing in the **Activity Log** in real-time!
