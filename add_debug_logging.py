#!/usr/bin/env python3
"""Add debug logging to understand the state persistence issue."""

import os

# Read the StateAdapter
with open("src/mcp_http_echo_server/utils/state_adapter.py", "r") as f:
    content = f.read()

# Add debug logging to set_state
old_set_state = '''    @staticmethod
    async def set_state(
        ctx: Context,
        key: str,
        value: Any
    ) -> None:
        """Set state with appropriate scoping for current mode.
        
        Args:
            ctx: FastMCP context
            key: State key
            value: State value
        """
        stateless_mode = ctx.get_state("stateless_mode")
        is_stateless = stateless_mode if stateless_mode is not None else False
        
        if is_stateless:
            # In stateless mode, store in request scope only
            ctx.set_state(f"request_{key}", value)
        else:
            # In stateful mode, store in session manager
            session_id = ctx.get_state("session_id")
            if not session_id:
                logger.warning(f"No session ID available for stateful key: {key}")
                # Fall back to request scope
                ctx.set_state(f"request_{key}", value)
            else:
                # Get session manager and update session directly
                session_manager = StateAdapter._get_session_manager(ctx)
                if session_manager:
                    session = session_manager.get_session(session_id)
                    if session:
                        if "state" not in session:
                            session["state"] = {}
                        session["state"][key] = value
                        # Also update context for current request
                        ctx.set_state(f"session_{session_id}_data", session)
                        return
                
                # Fallback: update context-stored session data
                session_data = ctx.get_state(f"session_{session_id}_data")
                if session_data:
                    if "state" not in session_data:
                        session_data["state"] = {}
                    session_data["state"][key] = value
                    ctx.set_state(f"session_{session_id}_data", session_data)
                else:
                    # Create new session data
                    session_data = {"state": {key: value}}
                    ctx.set_state(f"session_{session_id}_data", session_data)'''

new_set_state = '''    @staticmethod
    async def set_state(
        ctx: Context,
        key: str,
        value: Any
    ) -> None:
        """Set state with appropriate scoping for current mode.
        
        Args:
            ctx: FastMCP context
            key: State key
            value: State value
        """
        stateless_mode = ctx.get_state("stateless_mode")
        is_stateless = stateless_mode if stateless_mode is not None else False
        
        logger.info(f"[StateAdapter.set_state] key={key}, is_stateless={is_stateless}")
        
        if is_stateless:
            # In stateless mode, store in request scope only
            ctx.set_state(f"request_{key}", value)
            logger.info(f"[StateAdapter.set_state] Stored in request scope: request_{key}")
        else:
            # In stateful mode, store in session manager
            session_id = ctx.get_state("session_id")
            logger.info(f"[StateAdapter.set_state] session_id={session_id}")
            
            if not session_id:
                logger.warning(f"No session ID available for stateful key: {key}")
                # Fall back to request scope
                ctx.set_state(f"request_{key}", value)
            else:
                # Get session manager and update session directly
                session_manager = StateAdapter._get_session_manager(ctx)
                logger.info(f"[StateAdapter.set_state] session_manager={session_manager is not None}")
                
                if session_manager:
                    session = session_manager.get_session(session_id)
                    logger.info(f"[StateAdapter.set_state] session exists={session is not None}")
                    
                    if session:
                        if "state" not in session:
                            session["state"] = {}
                        session["state"][key] = value
                        logger.info(f"[StateAdapter.set_state] Stored in session manager: {key} -> {value}")
                        # Also update context for current request
                        ctx.set_state(f"session_{session_id}_data", session)
                        return
                
                # Fallback: update context-stored session data
                logger.info("[StateAdapter.set_state] Using fallback to context-stored session data")
                session_data = ctx.get_state(f"session_{session_id}_data")
                if session_data:
                    if "state" not in session_data:
                        session_data["state"] = {}
                    session_data["state"][key] = value
                    ctx.set_state(f"session_{session_id}_data", session_data)
                    logger.info(f"[StateAdapter.set_state] Updated context session data with {key}")
                else:
                    # Create new session data
                    session_data = {"state": {key: value}}
                    ctx.set_state(f"session_{session_id}_data", session_data)
                    logger.info(f"[StateAdapter.set_state] Created new session data with {key}")'''

content = content.replace(old_set_state, new_set_state)

# Write back
with open("src/mcp_http_echo_server/utils/state_adapter.py", "w") as f:
    f.write(content)

print("✅ Added debug logging to StateAdapter.set_state")

# Also update .env to enable debug logging
env_file = ".env"
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        env_content = f.read()
    
    if "MCP_ECHO_DEBUG" not in env_content:
        env_content += "\nMCP_ECHO_DEBUG=true\n"
    else:
        env_content = env_content.replace("MCP_ECHO_DEBUG=false", "MCP_ECHO_DEBUG=true")
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ Enabled debug mode in .env")