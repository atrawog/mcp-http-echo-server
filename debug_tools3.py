#!/usr/bin/env python3
"""Debug FastMCP tool registration - check after registration."""

import asyncio
from fastmcp import FastMCP, Context

# Create FastMCP instance
mcp = FastMCP(
    name="debug-test",
    version="1.0.0"
)

print("Before registration:")
print(f"  Tools in _tool_manager: {mcp._tool_manager._tools}")

# Register a tool directly
@mcp.tool
async def test_direct(ctx: Context, message: str) -> str:
    """Test direct tool."""
    return f"Direct: {message}"

print("\nAfter direct registration:")
print(f"  Tools in _tool_manager: {mcp._tool_manager._tools}")

# Register via function
def register_tools(mcp_instance):
    @mcp_instance.tool
    async def test_nested(ctx: Context, message: str) -> str:
        """Test nested tool."""
        return f"Nested: {message}"
    
    print(f"  Inside function - Tools: {mcp_instance._tool_manager._tools}")
    
register_tools(mcp)

print("\nAfter nested registration:")
print(f"  Tools in _tool_manager: {mcp._tool_manager._tools}")

# Try get_tools
print("\nUsing get_tools():")
tools = mcp.get_tools()
print(f"  Tools: {tools}")

# Check tool count method used in server.py
tool_count = len(mcp._tools) if hasattr(mcp, "_tools") else 0
print(f"\nTool count via mcp._tools: {tool_count}")

# Try the correct way
tool_count_correct = len(mcp._tool_manager._tools)
print(f"Tool count via mcp._tool_manager._tools: {tool_count_correct}")