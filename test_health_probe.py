#!/usr/bin/env python3
"""Test healthProbe tool directly."""

import json
import time
import httpx
import asyncio

BASE_URL = "http://localhost:3000/mcp"

async def test_health_probe():
    """Test the healthProbe tool."""
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
                        "name": "test-client",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                },
                "id": 1
            }
        )
        
        session_id = init_response.headers.get("mcp-session-id")
        print(f"Session ID: {session_id}")
        
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
        
        # Parse response
        text = response.text
        for line in text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(json.dumps(data, indent=2))
                return data

asyncio.run(test_health_probe())
