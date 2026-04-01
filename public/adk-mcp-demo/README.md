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

### 3. The Custom Plumbing (`custom_backend.py`)

**Why `custom_backend.py`?**
The standard ADK 2.0 Dev UI (and typical `runner.run_async()` abstraction) filters out partial real-time events (like `stateDelta`) to keep the primary trace clean and high-level. To stream granular, real-time progress chunks to a browser, we needed a custom backend using FastAPI that exposes a raw SSE (Server-Sent Events) endpoint (`/chat`).

**Why the Custom Event Generator? ("Out-of-Band" Streaming)**
The ADK 2.0 Alpha `Runner` naturally sequences events as the internal agent graph executes—it waits for a node (like a tool) to finish before yielding its output. However, our manual `enqueue_event(..., partial=True)` calls push events *out-of-band*. "Out-of-band" means these events are injected directly into the active event queue from a separate process (the tool's progress callback) while the main thread is still physically blocked waiting for the tool to complete its overall execution. 

To ensure these out-of-band events immediately stream back to the UI concurrently while the tool is still running, we implemented a dual-queue architecture:
- **ProgressProxyPlugin**: A custom `BasePlugin` that intercepts the invocation start and injects a shared `asyncio.Queue` into the context, allowing the tool to emit events seamlessly.
- **Merged Generator (`event_generator()`)**: The FastAPI backend spins up two background tasks—one consuming natural events from `Runner.run_async()`, and one consuming manual tool events from the plugin's queue. It merges both queues into a single SSE stream. This guarantees that manual progress chunks aren't blocked by the tool's execution thread and are flushed sequentially with natural LLM chunks.

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

### 2. Start the Custom Backend
```bash
python custom_backend.py
```
(Running on port 8002)

### 3. Test the Progress
Open `http://localhost:8002` in your browser and type:
> "Test the process_data tool on 'input data'"

You will see the progress chunks appearing in the **Activity Log** in real-time!
