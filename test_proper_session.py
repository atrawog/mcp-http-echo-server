#!/usr/bin/env python3
"""Proper test that maintains session across all tool calls."""

import json
import httpx
import asyncio

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
                            # Try to parse as JSON
                            return json.loads(data['result']['content'][0]['text'])
                        except:
                            # Return as string if not JSON
                            return data['result']['content'][0]['text']
            except Exception as e:
                pass
    return None

async def test_complete_workflow():
    """Test complete workflow with proper session handling."""
    
    print("=" * 60)
    print("TESTING COMPLETE WORKFLOW WITH PROPER SESSION")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Initialize and get session
        print("\n1. Initialize session...")
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
        print(f"   Session ID: {session_id}")
        
        # Send initialized notification
        await client.post(
            'http://localhost:3000/mcp',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}}
        )
        
        # Test 1: Echo a message
        print("\n2. Echo a message...")
        result = await call_tool(client, session_id, 'echo', {'message': 'Hello World!'}, 2)
        print(f"   Result: {result}")
        echo_worked = result and 'Hello World!' in str(result)
        
        # Test 2: Set custom state
        print("\n3. Set custom state...")
        result = await call_tool(client, session_id, 'stateManipulator', 
                                {'action': 'set', 'key': 'test_key', 'value': 'test_value'}, 3)
        print(f"   Result: {result}")
        state_set = result and result.get('success')
        
        # Test 3: Inspect state (should find both last_echo and test_key)
        print("\n4. Inspect all state...")
        result = await call_tool(client, session_id, 'stateInspector', {'key_pattern': '*'}, 4)
        print(f"   Result states: {list(result.get('states', {}).keys()) if result else 'None'}")
        has_echo = result and 'last_echo' in result.get('states', {})
        has_test_key = result and 'test_key' in result.get('states', {})
        
        # Test 4: Replay the echo
        print("\n5. Replay last echo...")
        result = await call_tool(client, session_id, 'replayLastEcho', {}, 5)
        print(f"   Result: {result}")
        replay_worked = result and 'Hello World!' in str(result) and 'REPLAY' in str(result)
        
        # Test 5: Check session info
        print("\n6. Check session info...")
        result = await call_tool(client, session_id, 'sessionInfo', {}, 6)
        print(f"   Result: {result}")
        session_found = result and 'current_session' in result and 'session_id' in str(result.get('current_session', {}))
        
        # Test 6: Check session history
        print("\n7. Check session history...")
        result = await call_tool(client, session_id, 'sessionHistory', {}, 7)
        print(f"   Total events: {result.get('total_events', 0) if result else 0}")
        has_history = result and result.get('total_events', 0) > 0
        
        # Results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"✅ Echo worked: {echo_worked}")
        print(f"✅ State set: {state_set}")
        print(f"✅ State has echo: {has_echo}")
        print(f"✅ State has test_key: {has_test_key}")
        print(f"✅ Replay worked: {replay_worked}")
        print(f"✅ Session found: {session_found}")
        print(f"✅ Has history: {has_history}")
        
        all_passed = all([echo_worked, state_set, has_echo, has_test_key, 
                         replay_worked, session_found, has_history])
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print("\n❌ SOME TESTS FAILED")
        
        return all_passed

if __name__ == "__main__":
    result = asyncio.run(test_complete_workflow())
    exit(0 if result else 1)
