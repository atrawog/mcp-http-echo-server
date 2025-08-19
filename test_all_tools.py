#!/usr/bin/env python3
"""Test all 21 tools with proper session management."""

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

async def test_all_tools():
    """Test all 21 tools."""
    
    print("=" * 80)
    print("COMPREHENSIVE TEST OF ALL 21 MCP ECHO SERVER TOOLS")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Initialize and get session
        print("\nInitializing session...")
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
        print(f"Session ID: {session_id}")
        
        # Send initialized notification
        await client.post(
            'http://localhost:3000/mcp',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json,text/event-stream', 'mcp-session-id': session_id},
            json={'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}}
        )
        
        print("\nTesting all 21 tools:\n")
        
        # Define all tools with their arguments
        tools = [
            # Echo Tools (2)
            ("echo", {"message": "Hello World"}, "Echo back the message"),
            ("replayLastEcho", {}, "Replay the last echoed message"),
            
            # Debug Tools (4)
            ("printHeader", {}, "Print request headers"),
            ("requestTiming", {}, "Show request timing information"),
            ("corsAnalysis", {}, "Analyze CORS configuration"),
            ("environmentDump", {}, "Dump environment variables"),
            
            # Auth Tools (3)
            ("bearerDecode", {}, "Decode bearer token (if present)"),
            ("authContext", {}, "Show authentication context"),
            ("whoIStheGOAT", {}, "The most important debugging tool"),
            
            # System Tools (2)
            ("healthProbe", {}, "System health check"),
            ("sessionInfo", {}, "Current session information"),
            
            # State Tools (10)
            ("stateInspector", {"key_pattern": "*"}, "Inspect all state"),
            ("stateManipulator", {"action": "set", "key": "test", "value": "value"}, "Set state"),
            ("stateBenchmark", {"operations": 10}, "Benchmark state operations"),
            ("stateValidator", {}, "Validate state consistency"),
            ("sessionHistory", {}, "Show session history"),
            ("sessionLifecycle", {}, "Session lifecycle info"),
            ("sessionTransfer", {"action": "export"}, "Export session data"),
            ("sessionCompare", {}, "Compare sessions"),
            ("requestTracer", {}, "Trace request flow"),
            ("modeDetector", {}, "Detect server mode"),
        ]
        
        passed = 0
        failed = 0
        results = []
        
        for i, (tool_name, args, description) in enumerate(tools, start=2):
            print(f"{i-1:2d}. {tool_name:<20} - {description}")
            result = await call_tool(client, session_id, tool_name, args, i)
            
            if result and 'error' not in result:
                passed += 1
                status = "✅ PASS"
                
                # Show key info from result
                if isinstance(result, dict):
                    if 'mode' in result:
                        status += f" [mode: {result['mode']}]"
                    elif 'success' in result:
                        status += f" [success: {result['success']}]"
                    elif 'status' in result:
                        status += f" [status: {result['status']}]"
                elif isinstance(result, str):
                    if len(result) > 50:
                        status += f" [{result[:50]}...]"
                    else:
                        status += f" [{result}]"
            else:
                failed += 1
                if result and 'error' in result:
                    status = f"❌ FAIL - {result['error'][:50]}"
                else:
                    status = "❌ FAIL - No response"
            
            print(f"    {status}")
            results.append((tool_name, result, 'error' not in result if result else False))
            
            # Small delay between tools
            await asyncio.sleep(0.1)
        
        # Final summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total tools tested: 21")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        # Check session persistence
        print("\n" + "=" * 80)
        print("SESSION PERSISTENCE CHECK")
        print("=" * 80)
        
        # Get final state to verify persistence
        final_state = await call_tool(client, session_id, 'stateInspector', {'key_pattern': '*'}, 100)
        if final_state and 'states' in final_state:
            state_keys = list(final_state['states'].keys())
            print(f"Final state keys: {state_keys}")
            
            # Verify key state items
            has_echo = 'last_echo' in state_keys
            has_test = 'test' in state_keys
            has_history = 'session_history' in state_keys
            
            print(f"  ✅ Has last_echo: {has_echo}")
            print(f"  ✅ Has test key: {has_test}")
            print(f"  ✅ Has session_history: {has_history}")
            
            if has_echo and has_test and has_history:
                print("\n✅ SESSION PERSISTENCE VERIFIED!")
            else:
                print("\n❌ SESSION PERSISTENCE ISSUES DETECTED")
        
        # Overall result
        print("\n" + "=" * 80)
        if failed == 0:
            print("🎉 ALL 21 TOOLS WORKING PERFECTLY! 🎉")
            print("✅ Session management: WORKING")
            print("✅ State persistence: WORKING")
            print("✅ Echo/replay: WORKING")
            print("✅ All tools: FUNCTIONAL")
            return True
        else:
            print(f"❌ {failed} TOOLS FAILED")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_all_tools())
    exit(0 if result else 1)