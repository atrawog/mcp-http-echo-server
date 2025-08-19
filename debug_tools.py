#!/usr/bin/env python3
"""Debug tool registration issue."""

import asyncio
from fastmcp import FastMCP, Context

# Create FastMCP instance
mcp = FastMCP(
    name="debug-test",
    version="1.0.0"
)

# Test 1: Register tool directly
@mcp.tool
async def direct_tool(ctx: Context, message: str) -> str:
    """Direct tool registration."""
    return f"Direct: {message}"

# Test 2: Register tool in function
def register_nested_tools(mcp_instance: FastMCP):
    """Register tools inside a function."""
    
    @mcp_instance.tool
    async def nested_tool(ctx: Context, message: str) -> str:
        """Nested tool registration."""
        return f"Nested: {message}"
    
    print(f"After nested registration: {len(mcp_instance._tools) if hasattr(mcp_instance, '_tools') else 'No _tools attr'}")

# Register nested tool
register_nested_tools(mcp)

# Check what tools are registered
print(f"Registered tools: {mcp._tools.keys() if hasattr(mcp, '_tools') else 'No _tools attribute'}")
print(f"Total tools: {len(mcp._tools) if hasattr(mcp, '_tools') else 0}")

# Try to access server tools
if hasattr(mcp, 'server') and hasattr(mcp.server, '_tools'):
    print(f"Server tools: {mcp.server._tools.keys()}")
elif hasattr(mcp, '_server') and hasattr(mcp._server, '_tools'):
    print(f"Server tools: {mcp._server._tools.keys()}")
else:
    print("No server tools found")