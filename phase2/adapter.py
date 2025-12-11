# ====================================================================
# Phase 2 Adapter: Bridges OOP simulation to GUI's procedural calls
# ====================================================================

from __future__ import annotations
from typing import Any, Callable, Dict, List, Tuple, Optional

# Import shared I/O functions from Phase 1 (avoids code duplication)
from phase1.io_mod import load_drivers, load_requests, generate_drivers

# Phase 2 OOP components
from .generator import RequestGenerator
from .policies import GlobalGreedyPolicy
from .mutation import HybridMutation
from .simulation import DeliverySimulation

# Helper functions for dict <-> object conversion and state extraction
from .helpers_2.engine_helpers import (
    sim_to_state_dict,           # Simulation -> GUI state dict
    get_adapter_metrics,         # Simulation -> metrics dict
    create_driver_from_dict,     # Driver dict -> Driver object
    create_request_from_dict,    # Request dict -> Request object
    request_to_dict,             # Request object -> dict
    get_plot_data_from_state,    # State dict -> plot tuples
)
from .helpers_2.metrics_helpers import SimulationTimeSeries


# ====================================================================
# Module-level simulation state
# ====================================================================

_simulation: DeliverySimulation | None = None
_time_series: SimulationTimeSeries | None = None  # Track metrics for post-simulation reporting


# ====================================================================
# Adapter functions (called by GUI)
# ====================================================================

# load_drivers, load_requests, generate_drivers are imported from phase1.io_mod

# generate_requests uses Phase 2's RequestGenerator (creates Request objects)
def generate_requests(start_t: int, out_list: List[dict], 
                      req_rate: float, width: int, height: int) -> None:
    """Generate stochastic requests (Poisson-like) and append to out_list."""
    gen = RequestGenerator(rate=req_rate, width=width, height=height)
    new_requests = gen.maybe_generate(start_t)
    
    for req in new_requests:
        out_list.append(request_to_dict(req))


def init_state(drivers_data: List[dict], requests_data: List[dict],
               timeout: int, req_rate: float, width: int, height: int) -> dict:
    """Build DeliverySimulation from procedural driver/request dicts."""
    global _simulation
    
    # Convert dicts to OOP objects using helpers
    drivers = [create_driver_from_dict(d, idx) for idx, d in enumerate(drivers_data)]
    requests = [create_request_from_dict(r) for r in requests_data]
    
    # Create dispatch policy (determines how requests are assigned to drivers)
    policy = GlobalGreedyPolicy()
    
    # Create mutation rule (allows drivers to change behaviour based on performance)
    mutation_rule = HybridMutation(window=5, low_threshold=3.0, high_threshold=10.0)
    
    # Create request generator
    # If CSV requests provided → don't generate new ones (rate=0)
    # If no CSV requests → generate dynamically using req_rate
    effective_rate = 0 if len(requests_data) > 0 else req_rate
    generator = RequestGenerator(rate=effective_rate, width=width, height=height)
    
    # Create the main simulation object
    _simulation = DeliverySimulation(
        drivers=drivers,
        dispatch_policy=policy,
        request_generator=generator,
        mutation_rule=mutation_rule,
        timeout=timeout,
    )
    
    # Pre-add loaded requests to the simulation
    _simulation.requests.extend(requests)
    
    # Initialize time-series tracking for post-simulation reporting
    global _time_series
    _time_series = SimulationTimeSeries()
    
    # Return initial state dict using helper
    return sim_to_state_dict(_simulation)


def simulate_step(state: dict) -> Tuple[dict, dict]:
    """Advance one tick, record metrics, and return (state_dict, metrics)."""
    global _simulation, _time_series
    
    # If _simulation is None, attempt to recover by checking if state has been initialized
    if _simulation is None:
        # Check if we have a valid state dict (should have 't', 'drivers', 'pending' keys)
        if not state or "drivers" not in state:
            raise RuntimeError(
                "Simulation not initialized. Call init_state() first. "
                "State dict is missing required keys: 't', 'drivers', 'pending'."
            )
        # State exists but simulation object was lost - this shouldn't happen in normal flow
        # but we can't recover without the actual simulation objects
        raise RuntimeError(
            "Simulation not initialized. Call init_state() first. "
            "The simulation context was lost (possible module reload)."
        )
    
    # Run one simulation tick (executes 9-step orchestration in engine_helpers)
    _simulation.tick()
    
    # Record metrics for post-simulation reporting (time-series tracking)
    if _time_series is not None:
        _time_series.record_tick(_simulation)
    
    # Convert OOP state back to dicts for GUI consumption
    updated_state = sim_to_state_dict(_simulation)
    metrics = get_adapter_metrics(_simulation)
    
    return updated_state, metrics


# ====================================================================
# Assignment-aligned wrapper functions
# ====================================================================

def init_simulation(drivers_data: List[dict], requests_data: List[dict],
                    timeout: int, req_rate: float, width: int, height: int) -> None:
    """Assignment wrapper: initialize the DeliverySimulation (delegates to init_state)."""
    init_state(drivers_data, requests_data, timeout, req_rate, width, height)


def step_simulation() -> Tuple[int, dict]:
    """Assignment wrapper: advance one tick and return (time, metrics)."""
    if _simulation is None:
        raise RuntimeError("Simulation not initialized. Call init_simulation() first.")

    # Reuse existing simulate_step; we ignore the returned state here and surface time+metrics
    state_dict = sim_to_state_dict(_simulation)
    updated_state, metrics = simulate_step(state_dict)
    return int(updated_state.get("t", 0)), metrics


def get_plot_data():
    """Assignment wrapper: return plot-ready tuples (drivers, pickups, dropoffs, arrows)."""
    if _simulation is None:
        raise RuntimeError("Simulation not initialized. Call init_simulation() first.")

    state = sim_to_state_dict(_simulation)
    return get_plot_data_from_state(state)


# ====================================================================
# Post-simulation reporting functions
# ====================================================================

def get_simulation() -> Optional[DeliverySimulation]:
    """Return the live DeliverySimulation or None if not initialized."""
    return _simulation


def get_time_series() -> Optional[SimulationTimeSeries]:
    """Return the recorded SimulationTimeSeries (or None if not started)."""
    return _time_series


# ====================================================================
# Backend factory (exposes 6 functions to GUI via sim_mod)
# ====================================================================

def create_phase2_backend() -> Dict[str, Callable]:
    """Return the 6-function backend dict the GUI expects."""
    return {
        "load_drivers": load_drivers,
        "load_requests": load_requests,
        "generate_drivers": generate_drivers,
        "generate_requests": generate_requests,
        "init_state": init_state,
        "simulate_step": simulate_step,
    }

