"""
Phase 2 UI Launcher
===================

This script launches the GUI with Phase 2's simulation engine while maintaining
compatibility with the teacher's dispatch_ui.py.

Since we cannot modify dispatch_ui.py, this launcher:
1. Imports the backend from phase1.phase2_bridge (which uses Phase 2 internally)
2. Passes it to the GUI's run_app function

The teacher can run this instead of python dispatch_ui.py to use Phase 2.

Usage:
    python run_phase2_ui.py
"""

from phase1.phase2_bridge import init_state, simulate_step
from phase1 import io_mod, helpers_1  # Keep using Phase 1's I/O helpers
from gui._engine import run_app


if __name__ == "__main__":
    # Create backend using Phase 1's I/O but Phase 2's simulation engine
    backend = {
        "load_drivers": io_mod.load_drivers,
        "load_requests": io_mod.load_requests,
        "generate_drivers": io_mod.generate_drivers,
        "generate_requests": io_mod.generate_requests,
        "init_state": init_state,  # Uses Phase 2 engine internally
        "simulate_step": simulate_step,  # Uses Phase 2 engine internally
    }
    
    run_app(backend)
