#!/usr/bin/env python3
"""Fix the state persistence issue by using SessionManager for storage."""

def generate_fixed_state_adapter():
    return '''"""State adapter for dual-mode (stateful/stateless) operation."""

import logging
from typing import Any, Optional
from fastmcp import Context

logger = logging.getLogger(__name__)


class StateAdapter:
    """Adapts state operations for both stateful and stateless modes."""
    
    @staticmethod
    async def get_state(
        ctx: Context,
        key: str,
        default: Any = None
    ) -> Any:
        """Get state with appropriate scoping for current mode.
        
        Args:
            ctx: FastMCP context
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        stateless_mode = ctx.get_state("stateless_mode")
        is_stateless = stateless_mode if stateless_mode is not None else False
        
        if is_stateless:
            # In stateless mode, use request-scoped state only
            result = ctx.get_state(f"request_{key}")
            return result if result is not None else default
        else:
            # In stateful mode, use session storage via session manager
            session_id = ctx.get_state("session_id")
            if not session_id:
                logger.warning(f"No session ID available for stateful key: {key}")
                return default
            
            # Get the session data from context (stored by middleware)
            session_data = ctx.get_state(f"session_{session_id}_data")
            if session_data and "state" in session_data:
                return session_data["state"].get(key, default)
            
            # Fallback to context state if session data not available
            result = ctx.get_state(f"session_{session_id}_{key}")
            return result if result is not None else default
    
    @staticmethod
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
            # In stateful mode, store in session via session manager
            session_id = ctx.get_state("session_id")
            if not session_id:
                logger.warning(f"No session ID available for stateful key: {key}")
                # Fall back to request scope
                ctx.set_state(f"request_{key}", value)
            else:
                # Get the session data from context (stored by middleware)
                session_data = ctx.get_state(f"session_{session_id}_data")
                if session_data:
                    # Store in the session's state dict
                    if "state" not in session_data:
                        session_data["state"] = {}
                    session_data["state"][key] = value
                    # Update the context reference
                    ctx.set_state(f"session_{session_id}_data", session_data)
                else:
                    # Fallback to context state
                    ctx.set_state(f"session_{session_id}_{key}", value)
    
    @staticmethod
    async def delete_state(
        ctx: Context,
        key: str
    ) -> bool:
        """Delete state with appropriate scoping for current mode.
        
        Args:
            ctx: FastMCP context
            key: State key
            
        Returns:
            True if deleted, False if not found
        """
        stateless_mode = ctx.get_state("stateless_mode")
        is_stateless = stateless_mode if stateless_mode is not None else False
        
        if is_stateless:
            # In stateless mode, delete from request scope
            full_key = f"request_{key}"
            if ctx.get_state(full_key) is not None:
                ctx.set_state(full_key, None)
                return True
            return False
        else:
            # In stateful mode, delete from session storage
            session_id = ctx.get_state("session_id")
            if not session_id:
                logger.warning(f"No session ID available for stateful key: {key}")
                return False
            
            # Get the session data from context
            session_data = ctx.get_state(f"session_{session_id}_data")
            if session_data and "state" in session_data and key in session_data["state"]:
                del session_data["state"][key]
                ctx.set_state(f"session_{session_id}_data", session_data)
                return True
            
            # Fallback to context state
            full_key = f"session_{session_id}_{key}"
            if ctx.get_state(full_key) is not None:
                ctx.set_state(full_key, None)
                return True
            return False
    
    @staticmethod
    async def get_state_for_session(
        ctx: Context,
        session_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get state for a specific session (stateful mode only).
        
        Args:
            ctx: FastMCP context
            session_id: Target session ID
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        stateless_mode = ctx.get_state("stateless_mode")
        if stateless_mode:
            logger.warning("get_state_for_session called in stateless mode")
            return default
        
        # Get the session data from context
        session_data = ctx.get_state(f"session_{session_id}_data")
        if session_data and "state" in session_data:
            return session_data["state"].get(key, default)
        
        # Fallback to context state
        result = ctx.get_state(f"session_{session_id}_{key}")
        return result if result is not None else default
    
    @staticmethod
    async def set_state_for_session(
        ctx: Context,
        session_id: str,
        key: str,
        value: Any
    ) -> None:
        """Set state for a specific session (stateful mode only).
        
        Args:
            ctx: FastMCP context
            session_id: Target session ID
            key: State key
            value: State value
        """
        stateless_mode = ctx.get_state("stateless_mode")
        if stateless_mode:
            logger.warning("set_state_for_session called in stateless mode")
            return
        
        # Get the session data from context
        session_data = ctx.get_state(f"session_{session_id}_data")
        if session_data:
            if "state" not in session_data:
                session_data["state"] = {}
            session_data["state"][key] = value
            ctx.set_state(f"session_{session_id}_data", session_data)
        else:
            # Fallback to context state
            ctx.set_state(f"session_{session_id}_{key}", value)
    
    @staticmethod
    def list_state_keys(
        ctx: Context,
        pattern: Optional[str] = None
    ) -> list[str]:
        """List all state keys matching pattern.
        
        Args:
            ctx: FastMCP context
            pattern: Optional pattern to filter keys
            
        Returns:
            List of matching state keys
        """
        stateless_mode = ctx.get_state("stateless_mode")
        is_stateless = stateless_mode if stateless_mode is not None else False
        
        if is_stateless:
            # In stateless mode, we can't easily list keys
            logger.warning("list_state_keys is not fully implemented for stateless mode")
            return []
        else:
            # In stateful mode, get keys from session storage
            session_id = ctx.get_state("session_id")
            if not session_id:
                return []
            
            session_data = ctx.get_state(f"session_{session_id}_data")
            if session_data and "state" in session_data:
                keys = list(session_data["state"].keys())
                if pattern and pattern != "*":
                    # Simple pattern matching
                    import re
                    regex = pattern.replace("*", ".*")
                    keys = [k for k in keys if re.match(f"^{regex}$", k)]
                return keys
            return []
    
    @staticmethod
    async def clear_session_state(
        ctx: Context,
        session_id: Optional[str] = None
    ) -> int:
        """Clear all state for a session.
        
        Args:
            ctx: FastMCP context
            session_id: Session ID to clear (uses current if None)
            
        Returns:
            Number of keys cleared
        """
        stateless_mode = ctx.get_state("stateless_mode")
        if stateless_mode:
            logger.warning("clear_session_state called in stateless mode")
            return 0
        
        if not session_id:
            session_id = ctx.get_state("session_id")
        
        if not session_id:
            logger.warning("No session ID available for clearing state")
            return 0
        
        session_data = ctx.get_state(f"session_{session_id}_data")
        if session_data and "state" in session_data:
            count = len(session_data["state"])
            session_data["state"] = {}
            ctx.set_state(f"session_{session_id}_data", session_data)
            return count
        return 0
    
    @staticmethod
    def get_scope_prefix(ctx: Context) -> str:
        """Get the current state scope prefix.
        
        Args:
            ctx: FastMCP context
            
        Returns:
            Scope prefix string
        """
        stateless_mode = ctx.get_state("stateless_mode")
        is_stateless = stateless_mode if stateless_mode is not None else False
        
        if is_stateless:
            return "request_"
        else:
            session_id = ctx.get_state("session_id")
            if session_id:
                return f"session_{session_id}_"
            else:
                return "request_"  # Fallback to request scope
'''

if __name__ == "__main__":
    print("Generating fixed StateAdapter...")
    
    # Write the fixed state adapter
    with open("src/mcp_http_echo_server/utils/state_adapter.py", "w") as f:
        f.write(generate_fixed_state_adapter())
    
    print("✅ Fixed StateAdapter to use session storage for persistence")
    print("\nThe fix:")
    print("- State is now stored in session_data['state'] dictionary")
    print("- This persists in the SessionManager between requests")
    print("- The session_data is passed via context by the middleware")