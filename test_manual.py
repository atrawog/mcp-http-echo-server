#!/usr/bin/env python3
"""Manually test specific tools to show they work correctly."""

import json
import httpx
import asyncio

BASE_URL = "http://localhost:3000/mcp"

async def call_tool(tool_name, arguments, session_id):
    """Call a tool and return the response."""
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
        text = response.text
        for line in text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if "result" in data and "content" in data["result"]:
                    return data["result"]["content"][0]["text"]
        return None

async def test_tools():
    """Test a few tools manually."""
    # Initialize session
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
                        "name": "manual-test",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                },
                "id": 1
            }
        )
        
        session_id = init_response.headers.get("mcp-session-id")
        print(f"Session: {session_id[:8]}...")
        print("=" * 60)
        
        # Test echo tool
        print("\n1. Echo Tool:")
        result = await call_tool("echo", {"message": "Testing the echo server!"}, session_id)
        print(f"   {result}")
        
        # Test replayLastEcho
        print("\n2. Replay Last Echo:")
        result = await call_tool("replayLastEcho", {}, session_id)
        print(f"   {result[:100]}...")
        
        # Test whoIStheGOAT
        print("\n3. Who is the GOAT:")
        result = await call_tool("whoIStheGOAT", {}, session_id)
        print(f"   {result[:200]}...")
        
        # Test modeDetector
        print("\n4. Mode Detector:")
        result = await call_tool("modeDetector", {}, session_id)
        result_json = json.loads(result)
        print(f"   Mode: {result_json['detected_mode']}")
        print(f"   Confidence: {result_json['confidence']}")
        print(f"   Docker: {result_json['environment']['docker']}")
        
        # Test authContext (OAuth)
        print("\n5. Auth Context (OAuth tool):")
        result = await call_tool("authContext", {}, session_id)
        result_json = json.loads(result)
        print(f"   Mode: {result_json['mode']}")
        print(f"   Bearer Token: {result_json['bearer_token']}")
        print(f"   OAuth Headers: Present={result_json['oauth_headers'].get('present', False)}")
        
        # Test healthProbe
        print("\n6. Health Probe:")
        result = await call_tool("healthProbe", {}, session_id)
        if result.startswith("{"):
            result_json = json.loads(result)
            print(f"   Status: {result_json['status']}")
            print(f"   Server: {result_json['server']['name']} v{result_json['server']['version']}")
            print(f"   Mode: {result_json['server']['mode']}")
            print(f"   Tools: {result_json['tools']['total']} total")
        else:
            print(f"   {result[:100]}...")

asyncio.run(test_tools())
