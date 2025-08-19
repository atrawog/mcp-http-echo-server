#!/usr/bin/env python3
"""Fix stateInspector to use the proper list_state_keys method."""

import os

# Read the current file
with open("src/mcp_http_echo_server/tools/state_tools.py", "r") as f:
    content = f.read()

# Find and replace the stateInspector implementation
old_section = '''        # Dynamically discover state keys
        # Try common keys and also check what's been set
        known_keys = [
            "last_echo", "echo_history", "session_history", "state_manipulations",
            "decoded_token", "goat_identified", "request_headers", "request_start_time",
            "request_id", "session_id", "request_errors", "request_breadcrumbs",
            "lifecycle_events", "benchmark_test", "test_key", "debug_test", "mykey"
        ]
        
        # Also try to find keys that have been dynamically created
        # Check for any keys that were set via stateManipulator
        manipulations = await StateAdapter.get_state(ctx, "state_manipulations", [])
        for manip in manipulations:
            if manip.get("action") == "set" and manip.get("key"):
                key = manip["key"]
                if key not in known_keys:
                    known_keys.append(key)
        
        total_size = 0
        state_count = 0
        
        for key in known_keys:
            # Check if key matches pattern
            if not match_pattern(key, key_pattern):
                continue
            
            value = await StateAdapter.get_state(ctx, key)
            if value is not None:
                state_count += 1'''

new_section = '''        # Use StateAdapter.list_state_keys to get all actual keys
        all_keys = StateAdapter.list_state_keys(ctx, key_pattern)
        
        # Also check known keys as fallback
        known_keys = [
            "last_echo", "echo_history", "session_history", "state_manipulations",
            "decoded_token", "goat_identified", "request_headers", "request_start_time",
            "request_id", "session_id", "request_errors", "request_breadcrumbs",
            "lifecycle_events", "benchmark_test", "test_key", "debug_test", "mykey"
        ]
        
        # Combine both lists
        keys_to_check = list(set(all_keys + known_keys))
        
        total_size = 0
        state_count = 0
        
        for key in keys_to_check:
            # Check if key matches pattern
            if not match_pattern(key, key_pattern):
                continue
            
            value = await StateAdapter.get_state(ctx, key)
            if value is not None:
                state_count += 1'''

content = content.replace(old_section, new_section)

# Write back
with open("src/mcp_http_echo_server/tools/state_tools.py", "w") as f:
    f.write(content)

print("✅ Fixed stateInspector to use StateAdapter.list_state_keys()")