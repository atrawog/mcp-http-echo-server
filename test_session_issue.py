#!/usr/bin/env python3
"""Test to confirm the session persistence issue."""

import json
import httpx
import asyncio

async def test():
    BASE_URL = 'http://localhost:3000/mcp'
    
    print("=" * 60)
    print("TESTING SESSION PERSISTENCE ISSUE")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Initialize and get session ID
        print("\n1. Initialize to get session ID...")
        init_response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream'},
            json={'jsonrpc': '2.0', 'method': 'initialize', 
                  'params': {'protocolVersion': '2025-06-18', 'clientInfo': {'name': 'test', 'version': '1.0.0'}}, 
                  'id': 1}
        )
        
        session_id_from_header = init_response.headers.get('mcp-session-id')
        print(f"   Got session ID from header: {session_id_from_header}")
        
        # Step 2: Send request WITH that session ID to see if it exists
        print("\n2. Use sessionInfo to check if session exists...")
        response = await client.post(
            BASE_URL,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json,text/event-stream',
                'mcp-session-id': session_id_from_header  # Use the session ID we got
            },
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'sessionInfo', 'arguments': {}}, 
                  'id': 2}
        )
        
        # Parse response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data:
                    if data['result'].get('isError'):
                        print(f"   ERROR: {data['result']['content'][0]['text']}")
                    else:
                        parsed = json.loads(data['result']['content'][0]['text'])
                        if 'current_session' in parsed:
                            curr = parsed['current_session']
                            if 'error' in curr:
                                print(f"   ❌ SESSION NOT FOUND: {curr['error']}")
                                print("\n   This proves the session was never stored in session_manager!")
                            else:
                                print(f"   ✅ Session exists: {curr.get('session_id', '?')}")
                        
                        if 'server_statistics' in parsed:
                            stats = parsed['server_statistics']
                            print(f"   Total sessions in manager: {stats['total_active_sessions']}")
                            if stats['total_active_sessions'] == 0:
                                print("\n   ❌ CONFIRMED: Session manager has 0 sessions!")
                                print("   The session_id is returned but session not stored!")

asyncio.run(test())