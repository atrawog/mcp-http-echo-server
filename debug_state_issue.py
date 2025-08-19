#!/usr/bin/env python3
"""Debug the state persistence issue in detail."""

import json
import httpx
import asyncio

async def test():
    BASE_URL = 'http://localhost:3000/mcp'
    
    print("=" * 60)
    print("DEBUGGING STATE PERSISTENCE ISSUE")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Initialize
        print("\n1. Initialize...")
        init_response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream'},
            json={'jsonrpc': '2.0', 'method': 'initialize', 
                  'params': {'protocolVersion': '2025-06-18', 'clientInfo': {'name': 'test', 'version': '1.0.0'}}, 
                  'id': 1}
        )
        
        session_id = init_response.headers.get('mcp-session-id')
        print(f"   Session ID: {session_id}")
        
        # Send initialized notification
        await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}}
        )
        
        # Step 2: Echo a message
        print("\n2. Echo a message...")
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'echo', 'arguments': {'message': 'Test message'}}, 
                  'id': 2}
        )
        
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    print(f"   Echo response: {data['result']['content'][0]['text'][:100]}")
        
        # Step 3: Check stateInspector to see what keys exist
        print("\n3. Inspect state to see what keys exist...")
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'stateInspector', 'arguments': {'key_pattern': '*'}}, 
                  'id': 3}
        )
        
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    print(f"   Mode: {parsed.get('mode')}")
                    print(f"   States found: {list(parsed.get('states', {}).keys())}")
                    if 'last_echo' in parsed.get('states', {}):
                        print(f"   last_echo value: {parsed['states']['last_echo']['value']}")
        
        # Step 4: Try replay
        print("\n4. Try to replay the echo...")
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'replayLastEcho', 'arguments': {}}, 
                  'id': 4}
        )
        
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data:
                    if data['result'].get('isError'):
                        print(f"   Replay ERROR: {data['result']['content'][0]['text']}")
                    else:
                        print(f"   Replay response: {data['result']['content'][0]['text'][:100]}")
        
        # Step 5: Set a custom state value
        print("\n5. Set a custom state value...")
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'stateManipulator', 'arguments': {'action': 'set', 'key': 'mykey', 'value': 'myvalue'}}, 
                  'id': 5}
        )
        
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    print(f"   Set state result: {parsed}")
        
        # Step 6: Try to get the state value back
        print("\n6. Inspect state again to see if mykey exists...")
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'stateInspector', 'arguments': {'key_pattern': 'mykey'}}, 
                  'id': 6}
        )
        
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    print(f"   States found: {list(parsed.get('states', {}).keys())}")
                    if 'mykey' in parsed.get('states', {}):
                        print(f"   ✅ mykey found with value: {parsed['states']['mykey']['value']}")
                    else:
                        print(f"   ❌ mykey NOT FOUND!")
        
        # Step 7: Check mode detector
        print("\n7. Check mode detector...")
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'modeDetector', 'arguments': {}}, 
                  'id': 7}
        )
        
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    print(f"   Detected mode: {parsed.get('detected_mode')}")
                    print(f"   Indicators: {parsed.get('indicators')}")

asyncio.run(test())