"""
Phase 1 Simulation Module - Adapter for Phase 2

This module provides the interface expected by the GUI (dispatch_ui.py)
and delegates to Phase 2's advanced OOP simulation engine.
"""

import os
from sys import path as syspath

# Module-level state
_phase2_backend = None

# Initialize Phase 2 backend
try:
    phase2_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2')
    if phase2_path not in syspath:
        syspath.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from phase2 import adapter as phase2_adapter
    _phase2_backend = phase2_adapter.create_phase2_backend()
except ImportError as e:
    raise ImportError(f"Phase 2 engine is required but could not be imported: {e}")


def init_state(drivers, requests, timeout: int = 10, req_rate: float = 3, width: int = 50, height: int = 30):
    """Initialize simulation using Phase 2 engine.
    
    Args:
        drivers: List of driver dictionaries
        requests: List of request dictionaries
        timeout: Request timeout in ticks
        req_rate: Request generation rate
        width: Map width
        height: Map height
        
    Returns:
        State dictionary for simulation
    """
    if _phase2_backend is None:
        raise RuntimeError("Phase 2 backend not initialized")
    
    return _phase2_backend["init_state"](drivers, requests, timeout, req_rate, width, height)


def simulate_step(state):
    """Advance simulation by one tick using Phase 2 engine.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Tuple of (updated_state, metrics_dict)
    """
    # yooo 
    if _phase2_backend is None:
        raise RuntimeError("Phase 2 backend not initialized")
    
    return _phase2_backend["simulate_step"](state)
