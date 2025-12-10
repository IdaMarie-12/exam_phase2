"""
Phase 1 to Phase 2 Bridge
==========================

This module allows Phase 1's procedural interface to use Phase 2's OOP engine
without modifying Phase 1's original code.

It acts as a transparent wrapper that:
1. Accepts Phase 1 state dicts
2. Converts them to Phase 2 objects internally
3. Runs Phase 2's simulation engine
4. Converts results back to Phase 1 state dicts

This enables the teacher's dispatch_ui.py to work with both Phase 1 and Phase 2
simply by importing from this bridge instead of sim_mod.

Usage:
------
In dispatch_ui.py (if allowed to change it slightly):
    from phase1.phase2_bridge import init_state, simulate_step
    
Otherwise, replace imports in phase1/__init__.py or create a wrapper script.
"""

from typing import Tuple, Dict, Any, List
import sys
from pathlib import Path

# Add parent directory to path to import phase2
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from phase2.adapter import create_phase2_backend

# Get Phase 2's backend functions
_phase2_backend = create_phase2_backend()


def init_state(drivers: List[dict], requests: List[dict], horizon: int, 
               timeout: int = 10, req_rate: float = 3, width: int = 50, 
               height: int = 30) -> dict:
    """
    Initialize simulation using Phase 2 engine while maintaining Phase 1 interface.
    
    Args:
        drivers: List of driver dicts (from Phase 1 format)
        requests: List of request dicts (from Phase 1 format)
        horizon: Simulation duration in ticks
        timeout: Request timeout in ticks
        req_rate: Request generation rate
        width: Map width
        height: Map height
    
    Returns:
        State dict compatible with Phase 1's simulate_step()
    """
    # Convert Phase 1 driver format to Phase 2 format
    drivers_phase2 = []
    for d in drivers:
        drivers_phase2.append({
            "id": d.get("id"),
            "x": d.get("x", 0),
            "y": d.get("y", 0),
            "speed": d.get("speed", 1.5),
        })
    
    # Convert Phase 1 request format to Phase 2 format
    requests_phase2 = []
    for r in requests:
        requests_phase2.append({
            "id": r.get("id"),
            "px": r.get("pickup", {}).get("x") if isinstance(r.get("pickup"), dict) else r.get("px", 0),
            "py": r.get("pickup", {}).get("y") if isinstance(r.get("pickup"), dict) else r.get("py", 0),
            "dx": r.get("dropoff", {}).get("x") if isinstance(r.get("dropoff"), dict) else r.get("dx", 0),
            "dy": r.get("dropoff", {}).get("y") if isinstance(r.get("dropoff"), dict) else r.get("dy", 0),
            "creation_time": r.get("creation_time", r.get("t", 0)),
        })
    
    # Call Phase 2's init_state
    state = _phase2_backend["init_state"](
        drivers_phase2, requests_phase2, timeout, req_rate, width, height
    )
    
    # Augment state with Phase 1 compatibility fields
    state["horizon"] = horizon
    state["printed_summary"] = False
    state["sum_wait"] = 0.0
    state["total_served_for_avg"] = 0
    state["served_waits"] = []
    
    return state


def simulate_step(state: dict) -> Tuple[dict, dict]:
    """
    Run one simulation step using Phase 2 engine while maintaining Phase 1 interface.
    
    Args:
        state: State dict from init_state()
    
    Returns:
        Tuple of (updated_state, metrics_dict) for Phase 1 compatibility
    """
    # Call Phase 2's simulate_step
    updated_state, metrics = _phase2_backend["simulate_step"](state)
    
    # Convert metrics to Phase 1 format if needed
    phase1_metrics = {
        "served": metrics.get("served", 0),
        "expired": metrics.get("expired", 0),
        "avg_wait": metrics.get("avg_wait", 0.0),
    }
    
    return updated_state, phase1_metrics
