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
    """Initialize the simulation with drivers, requests, and configuration parameters."""
    if _phase2_backend is None:
        raise RuntimeError(
            "Phase 2 backend not initialized. Check import errors above."
        )
    
    return _phase2_backend["init_state"](
        drivers_data=drivers,
        requests_data=requests,
        timeout=timeout,
        req_rate=req_rate,
        width=width,
        height=height,
    )


def simulate_step(state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Advance simulation by one tick."""
    if _phase2_backend is None:
        raise RuntimeError(
            "Phase 2 backend not initialized. Check import errors above."
        )
    
    return _phase2_backend["simulate_step"](state)
