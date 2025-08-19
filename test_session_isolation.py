#!/usr/bin/env python3
"""Test that sessions are properly isolated from each other."""

import json
import httpx
import asyncio

async def create_session(client):
    """Create a new session and return the session ID."""
    init_response = await client.post(
        'http://localhost:3000/mcp',
        headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream'},
        json={
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {'protocolVersion': '2025-06-18', 'clientInfo': {'name': 'test', 'version': '1.0.0'}},
            'id': 1
        }
    )
    
    session_id = init_response.headers.get('mcp-session-id')
    
    # Send initialized notification
    await client.post(
        'http://localhost:3000/mcp',
        headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
        json={'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}}
    )
    
    return session_id

async def call_tool(client, session_id, tool_name, args, request_id):
    """Call a tool with the given session ID."""
    response = await client.post(
        'http://localhost:3000/mcp',
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/event-stream',
            'mcp-session-id': session_id
        },
        json={
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {'name': tool_name, 'arguments': args},
            'id': request_id
        }
    )
    
    # Parse response
    for line in response.text.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'result' in data:
                    if data['result'].get('isError'):
                        return {'error': data['result']['content'][0]['text']}
                    else:
                        try:
                            return json.loads(data['result']['content'][0]['text'])
                        except:
                            return data['result']['content'][0]['text']
            except:
                pass
    return None

async def test_session_isolation():
    """Test that sessions are properly isolated."""
    
    print("=" * 60)
    print("TESTING SESSION ISOLATION")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Create two separate sessions
        print("\n1. Creating Session A...")
        session_a = await create_session(client)
        print(f"   Session A ID: {session_a}")
        
        print("\n2. Creating Session B...")
        session_b = await create_session(client)
        print(f"   Session B ID: {session_b}")
        
        # Echo different messages in each session
        print("\n3. Echo 'Hello from A' in Session A...")
        result = await call_tool(client, session_a, 'echo', {'message': 'Hello from A'}, 3)
        print(f"   Result: {result}")
        
        print("\n4. Echo 'Hello from B' in Session B...")
        result = await call_tool(client, session_b, 'echo', {'message': 'Hello from B'}, 4)
        print(f"   Result: {result}")
        
        # Set different state in each session
        print("\n5. Set state key='color' value='red' in Session A...")
        result = await call_tool(client, session_a, 'stateManipulator', 
                                {'action': 'set', 'key': 'color', 'value': 'red'}, 5)
        print(f"   Result: {result}")
        
        print("\n6. Set state key='color' value='blue' in Session B...")
        result = await call_tool(client, session_b, 'stateManipulator', 
                                {'action': 'set', 'key': 'color', 'value': 'blue'}, 6)
        print(f"   Result: {result}")
        
        # Now verify isolation - replay echo in each session
        print("\n7. Replay echo in Session A (should be 'Hello from A')...")
        result = await call_tool(client, session_a, 'replayLastEcho', {}, 7)
        print(f"   Result: {result}")
        session_a_replay_correct = result and 'Hello from A' in str(result)
        
        print("\n8. Replay echo in Session B (should be 'Hello from B')...")
        result = await call_tool(client, session_b, 'replayLastEcho', {}, 8)
        print(f"   Result: {result}")
        session_b_replay_correct = result and 'Hello from B' in str(result)
        
        # Verify state isolation
        print("\n9. Check state in Session A (color should be 'red')...")
        result = await call_tool(client, session_a, 'stateInspector', {'key_pattern': 'color'}, 9)
        print(f"   Result: {result}")
        session_a_color = result.get('states', {}).get('color', {}).get('value') if result else None
        session_a_state_correct = session_a_color == 'red'
        
        print("\n10. Check state in Session B (color should be 'blue')...")
        result = await call_tool(client, session_b, 'stateInspector', {'key_pattern': 'color'}, 10)
        print(f"   Result: {result}")
        session_b_color = result.get('states', {}).get('color', {}).get('value') if result else None
        session_b_state_correct = session_b_color == 'blue'
        
        # Results
        print("\n" + "=" * 60)
        print("ISOLATION TEST RESULTS")
        print("=" * 60)
        print(f"✅ Session A replay correct: {session_a_replay_correct}")
        print(f"✅ Session B replay correct: {session_b_replay_correct}")
        print(f"✅ Session A state correct (red): {session_a_state_correct}")
        print(f"✅ Session B state correct (blue): {session_b_state_correct}")
        
        all_isolated = all([session_a_replay_correct, session_b_replay_correct,
                           session_a_state_correct, session_b_state_correct])
        
        if all_isolated:
            print("\n🎉 PERFECT ISOLATION! Sessions are completely isolated! 🎉")
        else:
            print("\n❌ ISOLATION FAILURE! Sessions are bleeding state!")
        
        return all_isolated

if __name__ == "__main__":
    result = asyncio.run(test_session_isolation())
    exit(0 if result else 1)