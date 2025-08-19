#!/usr/bin/env python3
"""Test session header handling."""

import httpx
import asyncio
import json

async def test():
    BASE_URL = 'http://localhost:3000/mcp'
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Initialize
        print("1. Initialize...")
        init_response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream'},
            json={'jsonrpc': '2.0', 'method': 'initialize', 
                  'params': {'protocolVersion': '2025-06-18', 'clientInfo': {'name': 'test', 'version': '1.0.0'}}, 
                  'id': 1}
        )
        
        print(f"   Response headers: {dict(init_response.headers)}")
        session_id_from_header = init_response.headers.get('mcp-session-id')
        session_id_from_header_caps = init_response.headers.get('Mcp-Session-Id')
        
        print(f"   mcp-session-id: {session_id_from_header}")
        print(f"   Mcp-Session-Id: {session_id_from_header_caps}")
        
        # Parse response to see if session ID is in body
        for line in init_response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if 'result' in data:
                        print(f"   Response body result: {data['result']}")
                        if 'sessionId' in data['result']:
                            print(f"   Session ID in body: {data['result']['sessionId']}")
                except:
                    pass
        
        # Send another request with the session ID
        print("\n2. Send request with session ID...")
        session_id = session_id_from_header or session_id_from_header_caps or "test-session"
        print(f"   Using session ID: {session_id}")
        
        response = await client.post(
            BASE_URL,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json,text/event-stream',
                'mcp-session-id': session_id
            },
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'sessionInfo', 'arguments': {}}, 
                  'id': 2}
        )
        
        print(f"   Response headers: {dict(response.headers)}")

asyncio.run(test())