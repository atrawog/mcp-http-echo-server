#!/usr/bin/env python3
"""Test MCP Echo Server via HTTPS proxy at echo.atratest.org"""

import json
import httpx
import asyncio
import ssl
import sys

# Configuration
BASE_URL = "https://echo.atratest.org/mcp"
PROTOCOL_VERSION = "2025-06-18"

# Create SSL context that doesn't verify certificates (for development)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def send_mcp_request(client, method, params, request_id, session_id=None):
    """Send an MCP request and parse the SSE response."""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json,text/event-stream'
    }
    
    if session_id:
        headers['mcp-session-id'] = session_id
    
    response = await client.post(
        BASE_URL,
        headers=headers,
        json={
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': request_id
        }
    )
    
    # Parse SSE response
    for line in response.text.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                return data
            except:
                pass
    
    return None

async def call_tool(client, session_id, tool_name, args, request_id):
    """Call a tool with the given session ID."""
    data = await send_mcp_request(
        client,
        'tools/call',
        {'name': tool_name, 'arguments': args},
        request_id,
        session_id
    )
    
    if not data:
        return {'error': 'No response'}
    
    if 'error' in data:
        return {'error': data['error']}
    
    if 'result' in data:
        result = data['result']
        if result.get('isError'):
            return {'error': result['content'][0]['text']}
        else:
            try:
                # Try to parse as JSON
                return json.loads(result['content'][0]['text'])
            except:
                # Return as string if not JSON
                return result['content'][0]['text']
    
    return {'error': 'Unknown response format'}

async def test_echo_server():
    """Test the MCP Echo Server via HTTPS proxy."""
    
    print("=" * 80)
    print("TESTING MCP ECHO SERVER VIA HTTPS PROXY")
    print(f"URL: {BASE_URL}")
    print("=" * 80)
    
    # Use custom SSL context that doesn't verify certificates
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        # Step 1: Initialize session
        print("\n1. Initializing MCP session...")
        init_data = await send_mcp_request(
            client,
            'initialize',
            {
                'protocolVersion': PROTOCOL_VERSION,
                'clientInfo': {'name': 'echo-test', 'version': '1.0.0'}
            },
            1
        )
        
        if not init_data:
            print("   ❌ FAILED: No response from server")
            return False
        
        if 'error' in init_data:
            print(f"   ❌ FAILED: {init_data['error']}")
            return False
        
        # Get session ID from response headers (if available)
        session_id = None
        if 'result' in init_data:
            print(f"   ✅ SUCCESS: Protocol {init_data['result'].get('protocolVersion', 'unknown')}")
            # Session ID might be in headers, we'll get it from the next request
        
        # For now, we'll create a session ID manually
        import uuid
        session_id = str(uuid.uuid4())
        print(f"   Session ID: {session_id}")
        
        # Step 2: Send initialized notification
        print("\n2. Sending initialized notification...")
        await send_mcp_request(
            client,
            'notifications/initialized',
            {},
            None,  # Notifications don't have IDs
            session_id
        )
        print("   ✅ Notification sent")
        
        # Step 3: Test echo tool
        print("\n3. Testing echo tool...")
        echo_result = await call_tool(
            client,
            session_id,
            'echo',
            {'message': 'Hello from HTTPS test!'},
            2
        )
        
        if 'error' in echo_result:
            print(f"   ❌ FAILED: {echo_result['error']}")
            echo_success = False
        else:
            print(f"   ✅ SUCCESS: {echo_result}")
            echo_success = 'Hello from HTTPS test!' in str(echo_result)
        
        # Step 4: Test state manipulation
        print("\n4. Testing state manipulation...")
        state_result = await call_tool(
            client,
            session_id,
            'stateManipulator',
            {'action': 'set', 'key': 'https_test', 'value': 'working'},
            3
        )
        
        if 'error' in state_result:
            print(f"   ❌ FAILED: {state_result['error']}")
            state_success = False
        else:
            state_success = state_result.get('success', False)
            if state_success:
                print(f"   ✅ SUCCESS: State set successfully")
            else:
                print(f"   ❌ FAILED: {state_result}")
        
        # Step 5: Test replay echo
        print("\n5. Testing replay last echo...")
        replay_result = await call_tool(
            client,
            session_id,
            'replayLastEcho',
            {},
            4
        )
        
        if 'error' in replay_result:
            print(f"   ❌ FAILED: {replay_result['error']}")
            replay_success = False
        else:
            replay_success = 'Hello from HTTPS test!' in str(replay_result)
            if replay_success:
                print(f"   ✅ SUCCESS: Replay working")
            else:
                print(f"   ❌ FAILED: {replay_result}")
        
        # Step 6: Test state inspection
        print("\n6. Testing state inspection...")
        inspect_result = await call_tool(
            client,
            session_id,
            'stateInspector',
            {'key_pattern': '*'},
            5
        )
        
        if 'error' in inspect_result:
            print(f"   ❌ FAILED: {inspect_result['error']}")
            inspect_success = False
        else:
            states = inspect_result.get('states', {})
            has_test_key = 'https_test' in states
            has_echo = 'last_echo' in states
            inspect_success = has_test_key and has_echo
            
            if inspect_success:
                print(f"   ✅ SUCCESS: Found {len(states)} state keys")
                print(f"      - https_test: {states.get('https_test', {}).get('value')}")
                print(f"      - last_echo: {states.get('last_echo', {}).get('value')}")
            else:
                print(f"   ❌ FAILED: Missing expected state keys")
                print(f"      Found keys: {list(states.keys())}")
        
        # Step 7: Test session info
        print("\n7. Testing session info...")
        session_result = await call_tool(
            client,
            session_id,
            'sessionInfo',
            {},
            6
        )
        
        if 'error' in session_result:
            print(f"   ❌ FAILED: {session_result['error']}")
            session_success = False
        else:
            session_success = 'current_session' in session_result
            if session_success:
                mode = session_result.get('mode', 'unknown')
                print(f"   ✅ SUCCESS: Session found (mode: {mode})")
            else:
                print(f"   ❌ FAILED: {session_result}")
        
        # Step 8: Test health probe
        print("\n8. Testing health probe...")
        health_result = await call_tool(
            client,
            session_id,
            'healthProbe',
            {},
            7
        )
        
        if 'error' in health_result:
            print(f"   ❌ FAILED: {health_result['error']}")
            health_success = False
        else:
            status = health_result.get('status', 'unknown')
            health_success = status == 'healthy'
            if health_success:
                print(f"   ✅ SUCCESS: Server is {status}")
            else:
                print(f"   ❌ FAILED: Server status is {status}")
        
        # Final results
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        
        all_tests = [
            ('Echo', echo_success),
            ('State Set', state_success),
            ('Replay Echo', replay_success),
            ('State Inspect', inspect_success),
            ('Session Info', session_success),
            ('Health Probe', health_success)
        ]
        
        passed = sum(1 for _, success in all_tests if success)
        failed = len(all_tests) - passed
        
        for test_name, success in all_tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:20} {status}")
        
        print("\n" + "-" * 40)
        print(f"Total: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            print("✅ HTTPS proxy working")
            print("✅ MCP server responding")
            print("✅ Session management working")
            print("✅ State persistence working")
            return True
        else:
            print(f"\n❌ {failed} TESTS FAILED")
            return False

async def main():
    """Main entry point."""
    try:
        success = await test_echo_server()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())