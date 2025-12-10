"""
Phase 2 Adapter: Bridges OOP backend with GUI's procedural interface.

This module translates between:
- Phase 2 OOP architecture (DeliverySimulation, Driver, Request, etc.)
- GUI's procedural interface (dict-based state, functional calls)

The adapter provides 6 functions expected by gui/_engine.py:
    1. load_drivers(path) -> List[dict]
    2. load_requests(path) -> List[dict]
    3. generate_drivers(n, width, height) -> List[dict]
    4. generate_requests(start_t, out_list, req_rate, width, height) -> None
    5. init_state(drivers, requests, timeout, req_rate, width, height) -> dict
    6. simulate_step(state) -> (dict, dict)

Architecture:
    - Module-level _simulation stores the OOP DeliverySimulation instance
    - Each function either works with dicts (load, generate) or manages OOP objects
    - State dicts use "t", "drivers", "pending" keys for GUI compatibility
    - Metrics dicts use "served", "expired", "avg_wait" keys for reporting
    - Reuses helper functions from engine_helpers for state conversion

Usage:
    from phase2.adapter import create_phase2_backend
    backend = create_phase2_backend()
    gui._engine.run_app(backend)
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Tuple, Optional
import csv
import random

from .point import Point
from .request import Request
from .driver import Driver
from .generator import RequestGenerator
from .policies import GlobalGreedy
from .behaviours import LazyBehaviour
from .mutation import PerformanceBasedMutation
from .simulation import DeliverySimulation
from .helpers_2.engine_helpers import sim_to_state_dict, get_adapter_metrics
from .helpers_2.metrics_helpers import SimulationTimeSeries


# ====================================================================
# Module-level simulation state
# ====================================================================

_simulation: DeliverySimulation | None = None
_time_series: SimulationTimeSeries | None = None  # Track metrics for post-simulation reporting


# ====================================================================
# Adapter functions (called by GUI)
# ====================================================================

def load_drivers(path: str) -> List[dict]:
    """
    Load drivers from CSV file.
    
    Expected CSV format:
        id,x,y,speed
        1,0.0,0.0,1.5
        2,10.0,10.0,1.5
    
    Args:
        path: Path to driver CSV file
        
    Returns:
        List of driver dicts with keys: id, x, y, speed
    """
    drivers = []
    try:
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                drivers.append({
                    "id": int(row["id"]),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "speed": float(row.get("speed", 1.5)),
                })
    except FileNotFoundError:
        print(f"Warning: Driver file not found: {path}")
    except Exception as e:
        print(f"Error loading drivers: {e}")
    
    return drivers


def load_requests(path: str) -> List[dict]:
    """
    Load requests from CSV file.
    
    Expected CSV format:
        id,px,py,dx,dy,creation_time
        1,5.0,5.0,10.0,10.0,0
        2,15.0,15.0,20.0,20.0,1
    
    Args:
        path: Path to request CSV file
        
    Returns:
        List of request dicts with keys: id, px, py, dx, dy, creation_time
    """
    requests = []
    try:
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                requests.append({
                    "id": int(row["id"]),
                    "px": float(row["px"]),
                    "py": float(row["py"]),
                    "dx": float(row["dx"]),
                    "dy": float(row["dy"]),
                    "creation_time": int(row.get("creation_time", 0)),
                })
    except FileNotFoundError:
        print(f"Warning: Request file not found: {path}")
    except Exception as e:
        print(f"Error loading requests: {e}")
    
    return requests


def generate_drivers(n: int, width: int, height: int) -> List[dict]:
    """
    Generate n random drivers within grid bounds.
    
    Args:
        n: Number of drivers to generate
        width: Map width
        height: Map height
        
    Returns:
        List of driver dicts with random positions
    """
    drivers = []
    for i in range(n):
        drivers.append({
            "id": i + 1,
            "x": random.uniform(0, width),
            "y": random.uniform(0, height),
            "speed": 1.5,
        })
    return drivers


def generate_requests(start_t: int, out_list: List[dict], 
                      req_rate: float, width: int, height: int) -> None:
    """
    Generate requests stochastically at given rate.
    
    Appends requests to out_list (Poisson-like generation).
    
    Args:
        start_t: Starting time (typically current simulation time)
        out_list: List to append generated requests to
        req_rate: Expected requests per tick (Poisson λ)
        width: Map width
        height: Map height
    """
    gen = RequestGenerator(rate=req_rate, width=width, height=height)
    new_requests = gen.maybe_generate(start_t)
    
    for req in new_requests:
        out_list.append({
            "id": req.id,
            "px": req.pickup.x,
            "py": req.pickup.y,
            "dx": req.dropoff.x,
            "dy": req.dropoff.y,
            "creation_time": req.creation_time,
        })


def init_state(drivers_data: List[dict], requests_data: List[dict],
               timeout: int, req_rate: float, width: int, height: int) -> dict:
    """
    Initialize the simulation with drivers and requests.
    
    Creates OOP objects from procedural data and initializes DeliverySimulation.
    
    Args:
        drivers_data: List of driver dicts from load_drivers or generate_drivers
        requests_data: List of request dicts from load_requests or generate_requests
        timeout: Request timeout in ticks
        req_rate: Request generation rate (Poisson λ)
        width: Map width
        height: Map height
        
    Returns:
        State dict ready for simulation
    """
    global _simulation
    
    # Create OOP Driver objects
    drivers = []
    for d_dict in drivers_data:
        driver = Driver(
            id=d_dict["id"],
            position=Point(d_dict["x"], d_dict["y"]),
            speed=d_dict.get("speed", 1.5),
            behaviour=LazyBehaviour(idle_ticks_needed=3, max_distance=5.0),
        )
        drivers.append(driver)
    
    # Create OOP Request objects
    requests = []
    for r_dict in requests_data:
        request = Request(
            id=r_dict["id"],
            pickup=Point(r_dict["px"], r_dict["py"]),
            dropoff=Point(r_dict["dx"], r_dict["dy"]),
            creation_time=r_dict.get("creation_time", 0),
        )
        requests.append(request)
    
    # Create policy and mutation rule
    policy = GlobalGreedy()
    mutation_rule = PerformanceBasedMutation(window=5, earnings_threshold=5.0)
    
    # Create request generator
    generator = RequestGenerator(rate=req_rate, width=width, height=height)
    
    # Create DeliverySimulation
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
    """
    Advance simulation by one tick.
    
    Args:
        state: Current state dict (updated by reference in _simulation)
        
    Returns:
        Tuple of (updated_state_dict, metrics_dict)
    """
    global _simulation, _time_series
    
    if _simulation is None:
        raise RuntimeError("Simulation not initialized. Call init_state() first.")
    
    # Run one simulation tick
    _simulation.tick()
    
    # Record metrics for post-simulation reporting
    if _time_series is not None:
        _time_series.record_tick(_simulation)
    
    # Convert to state dict and extract metrics using helpers
    updated_state = sim_to_state_dict(_simulation)
    metrics = get_adapter_metrics(_simulation)
    
    return updated_state, metrics


# ====================================================================
# Adapter factory function
# ====================================================================

# ====================================================================
# Post-simulation reporting functions
# ====================================================================

def get_simulation() -> Optional[DeliverySimulation]:
    """
    Get the completed simulation instance for post-simulation analysis.
    
    Returns:
        DeliverySimulation instance or None if not initialized
    """
    return _simulation


def get_time_series() -> Optional[SimulationTimeSeries]:
    """
    Get recorded time-series metrics for plotting.
    
    Returns:
        SimulationTimeSeries instance or None if not recorded
    """
    return _time_series


def create_phase2_backend() -> Dict[str, Callable]:
    """
    Create Phase 2 backend dict for GUI compatibility.
    
    Returns a dict with 6 functions expected by gui/_engine.py:
        - load_drivers
        - load_requests
        - generate_drivers
        - generate_requests
        - init_state
        - simulate_step
    
    Example:
        >>> backend = create_phase2_backend()
        >>> from gui._engine import run_app
        >>> run_app(backend)
    """
    return {
        "load_drivers": load_drivers,
        "load_requests": load_requests,
        "generate_drivers": generate_drivers,
        "generate_requests": generate_requests,
        "init_state": init_state,
        "simulate_step": simulate_step,
    }

