#!/usr/bin/env python3
"""Show actual output from each tool to verify they work."""

import subprocess
import json

def test_tool_with_output(tool_name, args):
    """Test a tool and show actual output."""
    
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
        print(f'Session ID: {{session_id}}')
        
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
        
        print(f'Response status: {{response.status_code}}')
        print(f'Response headers: {{dict(response.headers)}}')
        print('Response body:')
        
        # Parse response
        for line in response.text.split('\\\\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if 'result' in data:
                        if data['result'].get('isError'):
                            print(f'ERROR: {{data[\\"result\\"][\\"content\\"][0][\\"text\\"]}}')
                        else:
                            content = data['result']['content'][0]['text']
                            try:
                                parsed = json.loads(content)
                                print(json.dumps(parsed, indent=2))
                            except:
                                print(content)
                    elif 'error' in data:
                        print(f'PROTOCOL ERROR: {{data[\\"error\\"]}}')
                except Exception as e:
                    pass

asyncio.run(test())
"'''
    
    cmd = cmd.replace('{args}', args_str)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout if result.stdout else f"STDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"EXCEPTION: {e}"

# Test specific tools to show they're actually working
print("=" * 80)
print("VERIFYING ACTUAL OUTPUT FROM KEY TOOLS")
print("=" * 80)

critical_tools = [
    ("echo", {"message": "This is a test message"}),
    ("healthProbe", {}),
    ("sessionInfo", {}),
    ("stateManipulator", {"action": "set", "key": "test_key", "value": "test_value"}),
    ("sessionTransfer", {"action": "export"}),
]

for tool_name, args in critical_tools:
    print(f"\n{'='*60}")
    print(f"Tool: {tool_name}")
    print(f"Args: {args}")
    print("="*60)
    result = test_tool_with_output(tool_name, args)
    print(result)
    print()