import asyncio
from mcp.server.fastmcp import FastMCP, Context

# Create the MCP server
mcp = FastMCP("EventStreamer", port=8003)

@mcp.tool()
async def process_data(data: str, ctx: Context) -> str:
    """Mock long-running task that processes data and reports progress via SSE."""
    total_steps = 10
    for i in range(1, total_steps + 1):
        # Simulate an intensive processing step
        await asyncio.sleep(1)

        # Calculate percentage progress (0.0 to 1.0)
        progress = float(i) / total_steps
        message = f"Processing chunk {i}/{total_steps} of '{data}'..."

        # Emit progress event via MCP protocol context
        await ctx.report_progress(progress=progress, total=1.0, message=message)

    return f"Successfully processed: {data}"

if __name__ == "__main__":
    # Start the fastMCP server on a dedicated port using Streamable HTTP
    # The default port for ADK Web is 8000, so we use 8001 here
    mcp.run(transport='streamable-http')
