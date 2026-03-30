#!/bin/bash
set -e

ADK_ENV="${ADK_ENV:-/Users/lukasgeiger/Desktop/VertexGenAISamples/adk2.0-alpha}"

if [ -f "$ADK_ENV/bin/activate" ]; then
    echo "Activating ADK 2.0 Environment from $ADK_ENV..."
    source "$ADK_ENV/bin/activate"
fi

echo "=========================================================="
echo " Starting FastMCP Server on port 8003..."
echo "=========================================================="

python mcp_server.py
