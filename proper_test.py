#!/usr/bin/env python3
"""Proper test with correct JSON escaping."""

import subprocess
import json
import time

def test_single_tool(tool_name, args):
    """Test a single tool properly."""
    
    # Properly escape the arguments
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
        if not session_id:
            print('ERROR: No session ID')
            return
            
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
                        else:
                            print('RESPONSE:', data['result']['content'][0]['text'])
                    elif 'error' in data:
                        print('PROTOCOL ERROR:', data['error'])
                except Exception as e:
                    pass

try:
    asyncio.run(test())
except Exception as e:
    print('EXCEPTION:', e)
"'''
    
    # Fixed JSON in args
    cmd = cmd.replace('{args}', args_str)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.stdout else f"STDERR: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"EXCEPTION: {e}"

print("=" * 80)
print("ACTUAL WORKING STATUS OF EACH TOOL")
print("=" * 80)

# Test each tool with proper arguments
tools = [
    ("echo", {"message": "Hello test"}),
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

working = []
broken = []

for tool_name, args in tools:
    result = test_single_tool(tool_name, args)
    
    if "RESPONSE:" in result:
        working.append(tool_name)
        status = "✅ WORKING"
    elif "ERROR:" in result:
        if "No Authorization header found" in result or "AUTHENTICATION REQUIRED" in result:
            working.append(tool_name)
            status = "✅ WORKING (auth error is expected)"
        else:
            broken.append(tool_name)
            status = "❌ ERROR"
    else:
        broken.append(tool_name)
        status = "❌ FAILED"
    
    print(f"\n{tool_name}: {status}")
    if "❌" in status:
        print(f"  Details: {result[:200]}")

print("\n" + "=" * 80)
print(f"SUMMARY: {len(working)}/21 tools working, {len(broken)} broken")
print("=" * 80)
print("\nWorking tools:", working)
print("\nBroken tools:", broken)