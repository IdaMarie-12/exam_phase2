"""
Phase 1 Simulation Module - Adapter for Phase 2

Provides the interface expected by the GUI (dispatch_ui.py) and delegates
all simulation logic to Phase 2's OOP engine.
"""

from typing import Any, Dict, List, Tuple

# Initialize Phase 2 backend
try:
    from phase2 import adapter as phase2_adapter
    _phase2_backend = phase2_adapter.create_phase2_backend()
except ImportError as e:
    raise ImportError(f"Phase 2 engine required: {e}")


def init_state(
    drivers: List[Dict[str, Any]], 
    requests: List[Dict[str, Any]], 
    timeout: int = 10, 
    req_rate: float = 3, 
    width: int = 50, 
    height: int = 30
) -> Dict[str, Any]:
    """Initialize simulation with drivers, requests, and config.
    
    Args:
        drivers: List of driver dicts with x, y positions.
        requests: List of request dicts with t, px, py, dx, dy.
        timeout: Request timeout in ticks.
        req_rate: Expected requests per tick (Poisson rate).
        width: Grid width.
        height: Grid height.
        
    Returns:
        State dict ready for simulate_step().
    """
    if _phase2_backend is None:
        raise RuntimeError(
            "Phase 2 backend not initialized. Check import errors above."
        )
    
    return _phase2_backend["init_state"](
        drivers=drivers,
        requests=requests,
        timeout=timeout,
        req_rate=req_rate,
        width=width,
        height=height,
    )


def simulate_step(state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Advance simulation by one tick.
    
    Args:
        state: Current state dict from init_state() or previous simulate_step().
        
    Returns:
        (updated_state, metrics) where metrics has served, expired, avg_wait, etc.
    """
    if _phase2_backend is None:
        raise RuntimeError(
            "Phase 2 backend not initialized. Check import errors above."
        )
    
    return _phase2_backend["simulate_step"](state)
