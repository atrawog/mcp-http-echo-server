#!/usr/bin/env python3
"""ACTUAL test of each tool with real output."""

import json
import subprocess
import time

def run_docker_test(tool_name, args_json="{}"):
    """Run a test in the Docker container and return actual output."""
    
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
        
        # Wait for init
        await asyncio.sleep(0.1)
        
        session_id = init_response.headers.get('mcp-session-id')
        if not session_id:
            print('ERROR: No session ID returned')
            return
            
        # Send initialized notification
        await client.post(
            BASE_URL,
            headers={{'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id}},
            json={{'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {{}}}}
        )
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Call the tool
        response = await client.post(
            BASE_URL,
            headers={{'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id}},
            json={{'jsonrpc': '2.0', 'method': 'tools/call', 
                  'params': {{'name': '{tool_name}', 'arguments': {args_json}}}, 
                  'id': 2}}
        )
        
        # Parse SSE response
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if 'result' in data:
                        if data['result'].get('isError'):
                            print(f'ERROR: {{data[\\"result\\"][\\"content\\"][0][\\"text\\"]}}')
                        else:
                            content = data['result']['content'][0]['text']
                            print(f'SUCCESS: {{content}}')
                    elif 'error' in data:
                        print(f'ERROR: {{data[\\"error\\"]}}')
                except Exception as e:
                    print(f'PARSE ERROR: {{e}} - Line: {{line}}')

asyncio.run(test())
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.stdout else f"STDERR: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"EXCEPTION: {e}"

# Test each tool
print("=" * 80)
print("ACTUAL TOOL TEST RESULTS")
print("=" * 80)

tools = [
    ("echo", {"message": "Test message"}),
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
    ("stateInspector", {}),
    ("stateManipulator", {"action": "set", "key": "test_key", "value": "test_value"}),
    ("stateBenchmark", {"operations": 10}),
    ("stateValidator", {}),
    ("sessionHistory", {}),
    ("sessionLifecycle", {}),
    ("sessionTransfer", {"action": "export"}),
    ("sessionCompare", {}),
    ("requestTracer", {}),
    ("modeDetector", {}),
]

for tool_name, args in tools:
    print(f"\n{tool_name}:")
    print("-" * 40)
    result = run_docker_test(tool_name, json.dumps(args))
    if result.startswith("SUCCESS:"):
        # Try to parse and format JSON if possible
        try:
            content = result[8:].strip()
            parsed = json.loads(content)
            print(json.dumps(parsed, indent=2)[:500])
        except:
            print(result[:500])
    else:
        print(result[:500])
    time.sleep(0.2)  # Small delay between tests

print("\n" + "=" * 80)
print("END OF ACTUAL TESTS")
print("=" * 80)