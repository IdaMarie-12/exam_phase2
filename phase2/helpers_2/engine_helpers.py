from __future__ import annotations
from typing import Any, Optional

from ..request import Request, WAITING, ASSIGNED, PICKED, EXPIRED
from ..offer import Offer
from ..point import Point
from ..driver import Driver
from ..behaviours import LazyBehaviour, GreedyDistanceBehaviour, EarningsMaxBehaviour
from ..mutation import GREEDY_MAX_DISTANCE, EARNINGS_MIN_REWARD_PER_TIME, LAZY_IDLE_TICKS_NEEDED
import random


# ====================================================================
# DICT <-> OBJECT CONVERSION HELPERS (for adapter)
# ====================================================================
"""Bidirectional conversion between dict and domain objects for adapter communication.
Enables serialization of drivers, requests, and state for GUI transmission and deserialization
from CSV/JSON sources. Handles validation and default values during conversion.
"""

def _assign_random_behaviour() -> "DriverBehaviour":
    """Randomly assigns one of three driver behaviour strategies."""
    choice = random.choice(["greedy", "earnings", "lazy"])
    
    if choice == "greedy":
        return GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
    elif choice == "earnings":
        return EarningsMaxBehaviour(min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME)
    else:  # choice == "lazy"
        return LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)


def create_driver_from_dict(d_dict: dict, idx: int = 0) -> "Driver":
    """Converts driver dict to Driver object with random behaviour assignment."""
    return Driver(
        id=d_dict.get("id", idx),
        position=Point(d_dict["x"], d_dict["y"]),
        speed=d_dict.get("speed", 1.5),
        behaviour=_assign_random_behaviour(),
    )


def create_request_from_dict(r_dict: dict) -> "Request":
    """Converts request dict to Request object, handling creation time variants."""
    creation_time = r_dict.get("creation_time", r_dict.get("t", 0))
    return Request(
        id=r_dict["id"],
        pickup=Point(r_dict["px"], r_dict["py"]),
        dropoff=Point(r_dict["dx"], r_dict["dy"]),
        creation_time=creation_time,
    )


def request_to_dict(req: "Request") -> dict:
    """Converts Request object to JSON-serializable dict for GUI transmission."""
    return {
        "id": req.id,
        "px": req.pickup.x,
        "py": req.pickup.y,
        "dx": req.dropoff.x,
        "dy": req.dropoff.y,
        "creation_time": req.creation_time,
    }


# ====================================================================
# ADAPTER VISUALIZATION HELPERS (for GUI display)
# ====================================================================
"""Transforms simulation state into visualization-ready coordinate tuples.
Extracts driver positions, pickup/dropoff locations, and request status for rendering on the map.
Handles state serialization and coordinate extraction for real-time GUI updates.
"""

def get_plot_data_from_state(state: dict):
    """Extracts plotting coordinates from state dict for visualization."""
    drivers = state.get("drivers", [])
    pending = state.get("pending", [])

    drivers_xy = [(float(d.get("x", 0.0)), float(d.get("y", 0.0))) for d in drivers]
    pickup_xy = []
    dropoff_xy = []

    for r in pending:
        status = r.get("status", "").upper()
        if status in ("WAITING", "ASSIGNED"):
            pickup_xy.append((float(r["px"]), float(r["py"])))
        elif status == "PICKED":
            dropoff_xy.append((float(r["dx"]), float(r["dy"])))

    dir_quiver = []
    return drivers_xy, pickup_xy, dropoff_xy, dir_quiver


# ====================================================================
# SIMULATION HELPER METHODS (from DeliverySimulation class)
# ====================================================================
"""Orchestration helpers for the 9-phase delivery tick cycle.
Implements request generation, expiration, proposal dispatch, offer collection, conflict resolution,
assignment, driver movement, and behaviour mutation across all drivers and requests.
"""

def gen_requests(simulation):
    """Generates new requests from generator and CSV sources, injecting on schedule."""
    # First, check if there are pre-loaded CSV requests waiting to arrive
    if hasattr(simulation, '_all_csv_requests') and hasattr(simulation, '_csv_requests_index'):
        csv_idx = simulation._csv_requests_index
        while csv_idx < len(simulation._all_csv_requests):
            req = simulation._all_csv_requests[csv_idx]
            if req.creation_time <= simulation.time:
                # Request has arrived, add it
                simulation.requests.append(req)
                csv_idx += 1
            else:
                # Requests are ordered by creation_time, so we can stop here
                break
        simulation._csv_requests_index = csv_idx
    
    # Then, generate stochastic requests via the generator
    new_reqs = simulation.request_generator.maybe_generate(simulation.time)
    if new_reqs:
        simulation.requests.extend(new_reqs)


def expire_requests(simulation):
    """Marks waiting requests as expired if they exceed the timeout."""
    for r in simulation.requests:
        if r.status == WAITING and (simulation.time - r.creation_time) >= simulation.timeout:
            r.mark_expired(simulation.time)
            simulation.expired_count += 1


def get_proposals(simulation):
    """Retrieves dispatch policy recommendations for driver-request pairings."""
    return simulation.dispatch_policy.assign(simulation.drivers, simulation.requests, simulation.time)


def collect_offers(simulation, proposals):
    """Converts proposals to offers and filters via driver behaviour logic."""
    if not isinstance(proposals, list):
        raise TypeError(f"proposals must be list, got {type(proposals).__name__}")
    
    from collections import defaultdict
    EPSILON = 1e-3
    MIN_SPEED = 1e-6
    
    offers = []
    for d, r in proposals:
        if r.status != WAITING:
            continue
        travel_time = d.position.distance_to(r.pickup) / max(d.speed, MIN_SPEED)
        reward = r.pickup.distance_to(r.dropoff)
        off = Offer(d, r, travel_time, reward, created_at=simulation.time, 
                   policy_name=type(simulation.dispatch_policy).__name__)
        # Record ALL offers created (not just accepted ones)
        simulation.offer_history.append(off)
        
        if d.behaviour and d.behaviour.decide(d, off, simulation.time):
            offers.append(off)
    return offers


def resolve_conflicts(simulation, offers):
    """Resolves conflicts by selecting the closest driver per request."""
    if not isinstance(offers, list):
        raise TypeError(f"offers must be list, got {type(offers).__name__}")
    
    from collections import defaultdict
    grouped = defaultdict(list)
    for o in offers:
        grouped[o.request.id].append(o)
    final = []
    for same_req in grouped.values():
        # Sort by distance (ascending - closest first)
        same_req.sort(key=lambda o: o.pickup_distance())
        final.append(same_req[0])
    return final


def assign_requests(simulation, final):
    """Assigns resolved offers to idle drivers."""
    for o in final:
        if o.request.status == WAITING and o.driver.status == "IDLE":
            o.driver.assign_request(o.request, simulation.time)


def move_drivers(simulation):
    """Advances active drivers toward targets and handles arrivals."""
    EPSILON = 1e-3
    
    for d in simulation.drivers:
        if d.status not in ("TO_PICKUP", "TO_DROPOFF"):
            continue
        d.step(1.0)
        tgt = d.target_point()
        if not tgt or d.position.distance_to(tgt) >= EPSILON:
            continue
        if d.status == "TO_PICKUP":
            handle_pickup(simulation, d)
        else:
            handle_dropoff(simulation, d)


def handle_pickup(simulation, driver):
    """Completes the pickup phase and transitions to dropoff."""
    driver.complete_pickup(simulation.time)


def handle_dropoff(simulation, driver):
    """Completes delivery and records metrics."""
    driver.complete_dropoff(simulation.time)
    last = driver.history[-1]
    beh = type(driver.behaviour).__name__ if driver.behaviour else "None"
    simulation.earnings_by_behaviour[beh].append(last.get("fare", 0.0))
    wait = last["time"] - last.get("start_time", last["time"])
    simulation._wait_samples.append(wait)
    n = len(simulation._wait_samples)
    simulation.avg_wait += (wait - simulation.avg_wait) / n
    simulation.served_count += 1


def mutate_drivers(simulation):
    """Applies mutation rule to each driver for behaviour adaptation."""
    if simulation.mutation_rule is not None and not hasattr(simulation.mutation_rule, 'maybe_mutate'):
        raise TypeError(f"mutation_rule must have maybe_mutate() method, got {type(simulation.mutation_rule).__name__}")
    
    if simulation.mutation_rule is None:
        return
    
    for d in simulation.drivers:
        simulation.mutation_rule.maybe_mutate(d, simulation.time)


# ====================================================================
# ADAPTER HELPER FUNCTIONS (for state conversion)
# ====================================================================

def sim_to_state_dict(simulation):
    """Convert simulation to GUI state dict. O(D+R)."""
    snap = simulation.get_snapshot()
    
    return {
        "t": snap["time"],
        "drivers": snap["drivers"],
        "pending": [
            {
                "id": r.id,
                "px": r.pickup.x,
                "py": r.pickup.y,
                "dx": r.dropoff.x,
                "dy": r.dropoff.y,
                "status": r.status.lower(),
                "t": r.creation_time,
            }
            for r in simulation.requests
        ],
        "served": simulation.served_count,
        "expired": simulation.expired_count,
        "avg_wait": simulation.avg_wait,
    }


def get_adapter_metrics(simulation):
    """Extract metrics dict (served, expired, avg_wait) for GUI. O(1)."""
    return {
        "served": simulation.served_count,
        "expired": simulation.expired_count,
        "avg_wait": round(simulation.avg_wait, 2),
    }


