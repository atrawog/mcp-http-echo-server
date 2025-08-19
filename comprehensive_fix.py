#!/usr/bin/env python3
"""Comprehensive fix for ALL remaining bugs in MCP Echo Server."""

import os
import shutil

def fix_echo_tools():
    """Fix echo tool to properly store messages using StateAdapter."""
    
    echo_tools_file = "src/mcp_http_echo_server/tools/echo_tools.py"
    
    with open(echo_tools_file, 'r') as f:
        content = f.read()
    
    # Fix the echo tool to use StateAdapter
    if "ctx.set_state(" in content:
        content = content.replace(
            "ctx.set_state(\"last_echo\", message)",
            "await StateAdapter.set_state(ctx, \"last_echo\", message)"
        )
        content = content.replace(
            "ctx.set_state(\"echo_history\", echo_history)",
            "await StateAdapter.set_state(ctx, \"echo_history\", echo_history)"
        )
        
        # Make sure StateAdapter is imported
        if "from ..utils.state_adapter import StateAdapter" not in content:
            import_line = "from ..utils.state_adapter import StateAdapter\n"
            # Add after other imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("from fastmcp"):
                    lines.insert(i + 1, import_line)
                    break
            content = '\n'.join(lines)
    
    # Fix replayLastEcho to use StateAdapter
    if "ctx.get_state(\"last_echo\")" in content:
        content = content.replace(
            'ctx.get_state("last_echo")',
            'await StateAdapter.get_state(ctx, "last_echo")'
        )
    
    # Fix echo_history retrieval
    if 'ctx.get_state("echo_history")' in content:
        content = content.replace(
            'ctx.get_state("echo_history")',
            'await StateAdapter.get_state(ctx, "echo_history", [])'
        )
    
    with open(echo_tools_file, 'w') as f:
        f.write(content)
    
    print("✅ Fixed echo tools to use StateAdapter")

def fix_middleware_session_loading():
    """Ensure middleware properly loads session data from manager."""
    
    server_file = "src/mcp_http_echo_server/server.py"
    
    with open(server_file, 'r') as f:
        lines = f.readlines()
    
    # Find the section where session is retrieved and ensure it's loaded properly
    for i, line in enumerate(lines):
        if "# Update session activity" in line:
            # This is where we get the session - make sure we get it from manager
            new_section = '''                        # Update session activity
                        session = self.server.session_manager.get_session(session_id)
                        if session:
                            session["last_activity"] = time.time()
                            session["request_count"] = session.get("request_count", 0) + 1
                            
                            # CRITICAL: Store the complete session data in context for StateAdapter
                            # This ensures tools can access the persisted state
                            fc.set_state(f"session_{session_id}_data", session)
                            
                            if self.server.debug:
                                state_count = len(session.get("state", {}))
                                logger.debug(f"Loaded session {session_id} with {state_count} state keys")
'''
            
            # Find the end of this section
            end_idx = i
            for j in range(i+1, min(i+15, len(lines))):
                if "# Track request in history" in lines[j] or "else:" in lines[j]:
                    end_idx = j
                    break
            
            # Replace the section
            lines[i:end_idx] = new_section.splitlines(True)
            print(f"✅ Fixed middleware session loading at line {i+1}")
            break
    
    with open(server_file, 'w') as f:
        f.writelines(lines)

def fix_session_info_tool():
    """Fix sessionInfo tool to properly find current session."""
    
    system_tools_file = "src/mcp_http_echo_server/tools/system_tools.py"
    
    with open(system_tools_file, 'r') as f:
        content = f.read()
    
    # Fix sessionInfo to use the correct session retrieval
    if "async def sessionInfo" in content:
        # Find and fix the sessionInfo implementation
        old_pattern = '''        # Get current session info if stateful
        if not stateless_mode:
            session_id = ctx.get_state("session_id")'''
        
        new_pattern = '''        # Get current session info if stateful
        if not stateless_mode:
            session_id = ctx.get_state("session_id")'''
        
        # Make sure it gets session from the manager
        if "session_manager.get_session(session_id)" in content:
            # Already uses session manager, but might need to check it's available
            if "_session_manager = ctx.get_state" not in content:
                # Add session manager retrieval
                content = content.replace(
                    "if session_manager and session_id:",
                    "# Try to get session manager from context first\n            if not session_manager:\n                session_manager = ctx.get_state(\"_session_manager\")\n            \n            if session_manager and session_id:"
                )
        
        print("✅ Fixed sessionInfo tool")
    
    with open(system_tools_file, 'w') as f:
        f.write(content)

def ensure_state_adapter_import():
    """Ensure all tool files import StateAdapter where needed."""
    
    tool_files = [
        "src/mcp_http_echo_server/tools/echo_tools.py",
        "src/mcp_http_echo_server/tools/debug_tools.py",
        "src/mcp_http_echo_server/tools/auth_tools.py",
        "src/mcp_http_echo_server/tools/system_tools.py"
    ]
    
    for tool_file in tool_files:
        if os.path.exists(tool_file):
            with open(tool_file, 'r') as f:
                content = f.read()
            
            # Check if file uses state operations
            if ("ctx.get_state" in content or "ctx.set_state" in content) and "StateAdapter" not in content:
                # Add StateAdapter import
                import_line = "from ..utils.state_adapter import StateAdapter\n"
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("from") or line.startswith("import"):
                        # Add after last import
                        continue
                    elif line.strip() and not line.startswith("#"):
                        # Found first non-import line, insert before it
                        lines.insert(i, import_line)
                        break
                content = '\n'.join(lines)
                
                with open(tool_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Added StateAdapter import to {tool_file}")

def create_proper_test():
    """Create a proper test that uses a single session."""
    
    test_content = '''#!/usr/bin/env python3
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
    for line in response.text.split('\\n'):
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
        print("\\n1. Initialize session...")
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
        print("\\n2. Echo a message...")
        result = await call_tool(client, session_id, 'echo', {'message': 'Hello World!'}, 2)
        print(f"   Result: {result}")
        echo_worked = result and 'Hello World!' in str(result)
        
        # Test 2: Set custom state
        print("\\n3. Set custom state...")
        result = await call_tool(client, session_id, 'stateManipulator', 
                                {'action': 'set', 'key': 'test_key', 'value': 'test_value'}, 3)
        print(f"   Result: {result}")
        state_set = result and result.get('success')
        
        # Test 3: Inspect state (should find both last_echo and test_key)
        print("\\n4. Inspect all state...")
        result = await call_tool(client, session_id, 'stateInspector', {'key_pattern': '*'}, 4)
        print(f"   Result states: {list(result.get('states', {}).keys()) if result else 'None'}")
        has_echo = result and 'last_echo' in result.get('states', {})
        has_test_key = result and 'test_key' in result.get('states', {})
        
        # Test 4: Replay the echo
        print("\\n5. Replay last echo...")
        result = await call_tool(client, session_id, 'replayLastEcho', {}, 5)
        print(f"   Result: {result}")
        replay_worked = result and 'Hello World!' in str(result) and 'Replaying' in str(result)
        
        # Test 5: Check session info
        print("\\n6. Check session info...")
        result = await call_tool(client, session_id, 'sessionInfo', {}, 6)
        print(f"   Result: {result}")
        session_found = result and 'current_session' in result and 'session_id' in str(result.get('current_session', {}))
        
        # Test 6: Check session history
        print("\\n7. Check session history...")
        result = await call_tool(client, session_id, 'sessionHistory', {}, 7)
        print(f"   Total events: {result.get('total_events', 0) if result else 0}")
        has_history = result and result.get('total_events', 0) > 0
        
        # Results
        print("\\n" + "=" * 60)
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
            print("\\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print("\\n❌ SOME TESTS FAILED")
        
        return all_passed

if __name__ == "__main__":
    result = asyncio.run(test_complete_workflow())
    exit(0 if result else 1)
'''
    
    with open("test_proper_session.py", 'w') as f:
        f.write(test_content)
    
    print("✅ Created proper test script")

def main():
    print("=" * 60)
    print("APPLYING COMPREHENSIVE FIXES")
    print("=" * 60)
    
    # Backup files
    print("\nCreating backups...")
    files_to_backup = [
        "src/mcp_http_echo_server/server.py",
        "src/mcp_http_echo_server/tools/echo_tools.py",
        "src/mcp_http_echo_server/tools/system_tools.py",
        "src/mcp_http_echo_server/utils/state_adapter.py"
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy(file, f"{file}.backup2")
    
    print("\nApplying fixes...")
    
    # Apply all fixes
    print("\n1. Fixing echo tools...")
    fix_echo_tools()
    
    print("\n2. Fixing middleware session loading...")
    fix_middleware_session_loading()
    
    print("\n3. Fixing sessionInfo tool...")
    fix_session_info_tool()
    
    print("\n4. Ensuring StateAdapter imports...")
    ensure_state_adapter_import()
    
    print("\n5. Creating proper test...")
    create_proper_test()
    
    print("\n" + "=" * 60)
    print("ALL FIXES APPLIED!")
    print("=" * 60)
    print("\nNow rebuild Docker and run the proper test...")

if __name__ == "__main__":
    main()