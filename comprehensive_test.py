#!/usr/bin/env python3
"""Comprehensive test of all MCP Echo Server functionality."""

import subprocess
import json
import time

def test_tool(tool_name, args):
    """Test a single tool and return result."""
    args_str = json.dumps(args).replace('"', '\\"')
    
    cmd = f'''docker exec mcp-echo-server python -c "
import json
import httpx
import asyncio

async def test():
    BASE_URL = 'http://localhost:3000/mcp'
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Initialize
        init_response = await client.post(
            BASE_URL,
            headers={{'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream'}},
            json={{'jsonrpc': '2.0', 'method': 'initialize', 
                  'params': {{'protocolVersion': '2025-06-18', 'clientInfo': {{'name': 'test', 'version': '1.0.0'}}}}, 
                  'id': 1}}
        )
        
        session_id = init_response.headers.get('mcp-session-id')
        
        # Send initialized notification
        await client.post(
            BASE_URL,
            headers={{'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id}},
            json={{'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {{}}}}
        )
        
        await asyncio.sleep(0.1)
        
        # Call the tool
        response = await client.post(
            BASE_URL,
            headers={{'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id}},
            json={{'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {{'name': '{tool_name}', 'arguments': {args}}}, 
                  'id': 2}}
        )
        
        # Parse response
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if 'result' in data:
                        if data['result'].get('isError'):
                            print('ERROR:', data['result']['content'][0]['text'])
                            return False
                        else:
                            print('SUCCESS')
                            return True
                except Exception as e:
                    pass
        
        print('NO_RESPONSE')
        return False

result = asyncio.run(test())
print('RESULT:', result)
"'''
    
    cmd = cmd.replace('{args}', args_str)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = result.stdout.strip()
        return "SUCCESS" in output and "RESULT: True" in output
    except:
        return False

def test_session_persistence():
    """Test that sessions persist and state is maintained."""
    
    cmd = '''docker exec mcp-echo-server python -c "
import json
import httpx
import asyncio

async def test():
    BASE_URL = 'http://localhost:3000/mcp'
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Initialize
        init_response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream'},
            json={'jsonrpc': '2.0', 'method': 'initialize', 
                  'params': {'protocolVersion': '2025-06-18', 'clientInfo': {'name': 'test', 'version': '1.0.0'}}, 
                  'id': 1}
        )
        
        session_id = init_response.headers.get('mcp-session-id')
        print(f'Session ID: {session_id}')
        
        # Send initialized notification
        await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}}
        )
        
        # Test 1: Echo a message
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'echo', 'arguments': {'message': 'Test message'}}, 
                  'id': 2}
        )
        echo_worked = False
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    if 'Test message' in data['result']['content'][0]['text']:
                        echo_worked = True
        print(f'Echo worked: {echo_worked}')
        
        # Test 2: Replay the echo
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'replayLastEcho', 'arguments': {}}, 
                  'id': 3}
        )
        replay_worked = False
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    text = data['result']['content'][0]['text']
                    if 'Test message' in text and 'Replaying' in text:
                        replay_worked = True
        print(f'Replay worked: {replay_worked}')
        
        # Test 3: Set state
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'stateManipulator', 'arguments': {'action': 'set', 'key': 'test_key', 'value': 'test_value'}}, 
                  'id': 4}
        )
        state_set = False
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    if parsed.get('success'):
                        state_set = True
        print(f'State set: {state_set}')
        
        # Test 4: Inspect state
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'stateInspector', 'arguments': {'key_pattern': '*'}}, 
                  'id': 5}
        )
        state_found = False
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    if 'test_key' in parsed.get('states', {}):
                        state_found = True
        print(f'State found: {state_found}')
        
        # Test 5: Check session info
        response = await client.post(
            BASE_URL,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {'name': 'sessionInfo', 'arguments': {}}, 
                  'id': 6}
        )
        session_found = False
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data and not data['result'].get('isError'):
                    parsed = json.loads(data['result']['content'][0]['text'])
                    if 'current_session' in parsed:
                        curr = parsed['current_session']
                        if 'session_id' in curr and session_id in curr['session_id']:
                            session_found = True
        print(f'Session found: {session_found}')
        
        return echo_worked and replay_worked and state_set and state_found and session_found

result = asyncio.run(test())
print(f'ALL_TESTS_PASSED: {result}')
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        print("Session Persistence Test Output:")
        print(output)
        return "ALL_TESTS_PASSED: True" in output
    except Exception as e:
        print(f"Session test error: {e}")
        return False

print("=" * 80)
print("COMPREHENSIVE MCP ECHO SERVER TEST")
print("=" * 80)

# Test 1: Session persistence and state management
print("\n1. Testing Session Persistence and State Management...")
session_test_passed = test_session_persistence()
print(f"   Result: {'✅ PASSED' if session_test_passed else '❌ FAILED'}")

# Test 2: Test all individual tools
print("\n2. Testing All 21 Tools...")
tools = [
    ("echo", {"message": "Hello World"}),
    ("replayLastEcho", {}),
    ("printHeader", {}),
    ("bearerDecode", {}),
    ("authContext", {}),
    ("whoIStheGOAT", {}),
    ("requestTiming", {}),
    ("corsAnalysis", {}),
    ("environmentDump", {}),
    ("healthProbe", {}),
    ("sessionInfo", {}),
    ("stateInspector", {"key_pattern": "*"}),
    ("stateManipulator", {"action": "set", "key": "test", "value": "value"}),
    ("stateBenchmark", {"operations": 10}),
    ("stateValidator", {}),
    ("sessionHistory", {}),
    ("sessionLifecycle", {}),
    ("sessionTransfer", {"action": "export"}),
    ("sessionCompare", {}),
    ("requestTracer", {}),
    ("modeDetector", {}),
]

passed = 0
failed = 0

for tool_name, args in tools:
    result = test_tool(tool_name, args)
    if result:
        print(f"   ✅ {tool_name}")
        passed += 1
    else:
        print(f"   ❌ {tool_name}")
        failed += 1
    time.sleep(0.1)

print(f"\n   Tools Summary: {passed}/21 passed, {failed} failed")

# Final summary
print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)

all_passed = session_test_passed and failed == 0

if all_passed:
    print("🎉 ALL TESTS PASSED! 🎉")
    print("✅ Session management working")
    print("✅ Echo/replay working")
    print("✅ State persistence working")
    print("✅ All 21 tools functional")
else:
    print("❌ SOME TESTS FAILED")
    if not session_test_passed:
        print("❌ Session persistence issues")
    if failed > 0:
        print(f"❌ {failed} tools not working")

print("=" * 80)