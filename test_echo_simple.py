#!/usr/bin/env python3
"""Simple test of echo tool."""

import json
import httpx
import asyncio

BASE_URL = "http://localhost:3000/mcp"

async def test_echo():
    """Test echo tool."""
    async with httpx.AsyncClient() as client:
        # Initialize session
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
        print(f"Session: {session_id}")
        
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
        
        # Call echo tool
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
                    "name": "echo",
                    "arguments": {"message": "Hello MCP Server!"}
                },
                "id": 2
            }
        )
        
        print(f"\nRaw response:\n{response.text}")
        
        # Parse SSE response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"\nParsed JSON:\n{json.dumps(data, indent=2)}")
                
                if "result" in data and "content" in data["result"]:
                    text = data["result"]["content"][0]["text"]
                    print(f"\nEcho response: {text}")

asyncio.run(test_echo())
