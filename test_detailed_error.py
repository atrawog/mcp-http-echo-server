#!/usr/bin/env python3
"""Get detailed error from healthProbe."""

import json
import httpx
import asyncio

BASE_URL = "http://localhost:3000/mcp"

async def test_health():
    """Test healthProbe with detailed error info."""
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
        print(f"Session: {session_id}\n")
        
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
        
        # Call healthProbe
        print("Calling healthProbe...")
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
                    "name": "healthProbe",
                    "arguments": {}
                },
                "id": 2
            }
        )
        
        print(f"Raw response:\n{response.text}\n")
        
        # Parse SSE response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"Parsed JSON:\n{json.dumps(data, indent=2)}")

asyncio.run(test_health())