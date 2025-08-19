#!/usr/bin/env python3
"""Test each tool individually to see actual responses."""

import json
import httpx
import asyncio

BASE_URL = "http://localhost:3000/mcp"

async def init_session():
    """Initialize a session."""
    async with httpx.AsyncClient() as client:
        init_response = await client.post(
            BASE_URL,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "clientInfo": {
                        "name": "test",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
        )
        
        session_id = init_response.headers.get("mcp-session-id")
        
        # Send initialized notification
        await client.post(
            BASE_URL,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream",
                "mcp-session-id": session_id
            },
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
        )
        
        return session_id

async def call_tool(tool_name, arguments, session_id):
    """Call a tool and return the full response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            BASE_URL,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream",
                "mcp-session-id": session_id
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 2
            }
        )
        
        # Parse SSE response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                return data

async def test_tools():
    """Test tools individually."""
    session_id = await init_session()
    print(f"Session: {session_id}\n")
    print("=" * 80)
    
    # Test tools that are showing errors
    tools_to_test = [
        ("healthProbe", {}),
        ("sessionInfo", {}),
        ("echo", {"message": "Test message"}),
        ("replayLastEcho", {}),
        ("bearerDecode", {}),
        ("authContext", {}),
        ("whoIStheGOAT", {}),
        ("environmentDump", {}),
    ]
    
    for tool_name, args in tools_to_test:
        print(f"\nTesting: {tool_name}")
        print("-" * 40)
        
        result = await call_tool(tool_name, args, session_id)
        
        # Check for error
        if result and "result" in result:
            if result["result"].get("isError"):
                print(f"ERROR: {result['result']['content'][0]['text']}")
            else:
                content = result["result"]["content"][0]["text"]
                # Truncate long responses
                if len(content) > 200:
                    print(f"Response: {content[:200]}...")
                else:
                    print(f"Response: {content}")
        else:
            print(f"Unexpected response: {result}")

asyncio.run(test_tools())
