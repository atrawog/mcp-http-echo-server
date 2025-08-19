#!/usr/bin/env python3
"""Fix remaining ctx.get_state() issues with defaults."""

import re
import sys

def fix_file(filepath):
    """Fix ctx.get_state() calls in a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern 1: (ctx.get_state("key") if ctx.get_state("key") is not None else default)
    pattern1 = r'\(ctx\.get_state\("([^"]+)"\) if ctx\.get_state\("\1"\) is not None else ([^)]+)\)'
    
    def replacement1(match):
        key = match.group(1)
        default = match.group(2)
        return f'(ctx.get_state("{key}") or {default})'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: ctx.get_state("key") if ctx.get_state("key") is not None else default
    # This is for cases without parentheses
    pattern2 = r'ctx\.get_state\("([^"]+)"\) if ctx\.get_state\("\1"\) is not None else ([^\n,;)]+)'
    
    def replacement2(match):
        key = match.group(1)
        default = match.group(2)
        return f'(ctx.get_state("{key}") or {default})'
    
    content = re.sub(pattern2, replacement2, content)
    
    # Pattern 3: Fix ctx.get_state(f"session_{session_id}_data") patterns
    pattern3 = r'\(ctx\.get_state\(f"([^"]+)"\) if ctx\.get_state\(f"\1"\) is not None else ([^)]+)\)'
    
    def replacement3(match):
        key = match.group(1)
        default = match.group(2)
        return f'(ctx.get_state(f"{key}") or {default})'
    
    content = re.sub(pattern3, replacement3, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")
        return True
    return False

# Fix all tool files
import glob

tool_files = glob.glob('/home/atrawog/oauth-https-proxy/mcp-http-echo-server/src/mcp_http_echo_server/tools/*.py')

fixed_count = 0
for filepath in tool_files:
    if fix_file(filepath):
        fixed_count += 1

print(f"\nFixed {fixed_count} files")