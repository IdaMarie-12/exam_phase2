"""
Phase 2 Adapter: Bridges the OOP simulation to the GUI’s procedural calls.

What it does
------------
* Translates between Phase 2 classes (DeliverySimulation, Driver, Request, etc.)
    and the dict-based interface that the GUI expects.
* Exposes the six Phase 1-style functions the GUI currently calls, plus
    assignment-aligned wrappers (init_simulation, step_simulation, get_plot_data).
* Maintains module-level simulation and metrics so the GUI can step and render.

Key functions exposed to the GUI
--------------------------------
1) load_drivers(path) -> list[dict]
2) load_requests(path) -> list[dict]
3) generate_drivers(n, width, height) -> list[dict]
4) generate_requests(start_t, out_list, req_rate, width, height) -> None
5) init_state(drivers, requests, timeout, req_rate, width, height) -> dict
6) simulate_step(state) -> (dict, dict)

Assignment wrappers
-------------------
* init_simulation(...) -> None (delegates to init_state)
* step_simulation() -> (time, metrics) (delegates to simulate_step)
* get_plot_data() -> plotting tuples derived from current state

State/metrics helpers
---------------------
* sim_to_state_dict converts the OOP sim to a dict for the GUI
* get_adapter_metrics extracts served/expired/avg_wait from the sim
* SimulationTimeSeries records metrics over time for post-run reporting
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

def load_drivers(path: str) -> List[Dict[str, float]]:
    """Load drivers from CSV into dicts (id, x, y, speed).

    Expected columns: id,x,y,speed. Missing speed defaults to 1.5.
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


def load_requests(path: str) -> List[Dict[str, float]]:
    """Load requests from CSV into dicts (id, px, py, dx, dy, creation_time).

    Accepts either explicit creation_time or defaults it to 0.
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
    """Generate n random driver dicts within [0,width]x[0,height]."""
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
    """Generate stochastic requests (Poisson-like) and append to out_list.

    Uses RequestGenerator(rate=req_rate, width=width, height=height) at start_t.
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
    """Build DeliverySimulation from procedural driver/request dicts.

    Converts dicts to Driver/Request objects, wires policy/mutation/generator,
    seeds the simulation, starts time-series tracking, and returns the GUI state dict.
    """
    global _simulation
    
    # Create OOP Driver objects
    drivers = []
    for idx, d_dict in enumerate(drivers_data):
        driver = Driver(
            id=d_dict.get("id", idx),  # Use index as id if not provided (CSV case)
            position=Point(d_dict["x"], d_dict["y"]),
            speed=d_dict.get("speed", 1.5),
            behaviour=LazyBehaviour(idle_ticks_needed=3),
        )
        drivers.append(driver)
    
    # Create OOP Request objects
    requests = []
    for r_dict in requests_data:
        # Handle both Phase 1 format (t) and Phase 2 format (creation_time)
        creation_time = r_dict.get("creation_time", r_dict.get("t", 0))
        request = Request(
            id=r_dict["id"],
            pickup=Point(r_dict["px"], r_dict["py"]),
            dropoff=Point(r_dict["dx"], r_dict["dy"]),
            creation_time=creation_time,
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
    """Advance one tick, record metrics, and return (state_dict, metrics)."""
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
    drivers = state.get("drivers", [])
    pending = state.get("pending", [])

    drivers_xy = [(float(d.get("x", 0.0)), float(d.get("y", 0.0))) for d in drivers]
    pickup_xy = []
    dropoff_xy = []

    for r in pending:
        status = r.get("status")
        if status in ("WAITING", "ASSIGNED"):
            pickup_xy.append((float(r["px"]), float(r["py"])))
        elif status == "PICKED":
            dropoff_xy.append((float(r["dx"]), float(r["dy"])))

    dir_quiver: List[Tuple[float, float, float, float]] = []
    return drivers_xy, pickup_xy, dropoff_xy, dir_quiver


# ====================================================================
# Adapter factory function
# ====================================================================

# ====================================================================
# Post-simulation reporting functions
# ====================================================================

def get_simulation() -> Optional[DeliverySimulation]:
    """Return the live DeliverySimulation or None if not initialized."""
    return _simulation


def get_time_series() -> Optional[SimulationTimeSeries]:
    """Return the recorded SimulationTimeSeries (or None if not started)."""
    return _time_series


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

