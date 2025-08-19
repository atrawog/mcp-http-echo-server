#!/usr/bin/env python3
"""Debug FastMCP tool registration."""

import asyncio
from fastmcp import FastMCP, Context

# Create FastMCP instance
mcp = FastMCP(
    name="debug-test",
    version="1.0.0"
)

# Check all attributes
print("FastMCP attributes:")
for attr in dir(mcp):
    if not attr.startswith('_'):
        print(f"  {attr}: {type(getattr(mcp, attr))}")

print("\nChecking for tool-related attributes:")
for attr in dir(mcp):
    if 'tool' in attr.lower():
        val = getattr(mcp, attr)
        print(f"  {attr}: {type(val)}")
        if hasattr(val, '__dict__'):
            print(f"    -> {val.__dict__}")

# Register a tool
@mcp.tool
async def test_tool(ctx: Context, message: str) -> str:
    """Test tool."""
    return f"Test: {message}"

print("\nAfter registration:")
# Check for server
if hasattr(mcp, 'server'):
    print(f"  mcp.server: {type(mcp.server)}")
    if hasattr(mcp.server, '_tools'):
        print(f"  mcp.server._tools: {mcp.server._tools}")
    if hasattr(mcp.server, 'list_tools'):
        print(f"  mcp.server.list_tools: {mcp.server.list_tools}")
        
# Try to list tools
if hasattr(mcp, 'list_tools'):
    tools = asyncio.run(mcp.list_tools())
    print(f"  Tools via list_tools: {tools}")

# Check internal server
if hasattr(mcp, '_server'):
    print(f"  mcp._server: {type(mcp._server)}")
    if hasattr(mcp._server, '_tools'):
        print(f"  mcp._server._tools: {mcp._server._tools}")

# Look for app or router
if hasattr(mcp, 'app'):
    print(f"  mcp.app: {type(mcp.app)}")
if hasattr(mcp, '_app'):
    print(f"  mcp._app: {type(mcp._app)}")
if hasattr(mcp, 'router'):
    print(f"  mcp.router: {type(mcp.router)}")
if hasattr(mcp, '_router'):
    print(f"  mcp._router: {type(mcp._router)}")