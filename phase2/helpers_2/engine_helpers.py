"""
Engine Helper Functions - 9-Step Orchestration and State Conversion

This module implements the 9-step simulation loop that powers DeliverySimulation.tick().
Each function represents one step in the discrete-time event orchestration.

COMPLEXITY ANALYSIS (Big O Notation)
====================================

Big O describes how an algorithm scales with input size:

    O(1)     - Constant: Same time regardless of input (e.g., accessing dict key)
    O(log N) - Logarithmic: Scales with log of N (e.g., binary search)
    O(N)     - Linear: Scales proportionally with N (e.g., loop through all items)
    O(N log N)- Linearithmic: N * log(N), common in sorting
    O(N²)    - Quadratic: Scales with N squared (nested loops)
    O(D*R)   - Special: D=drivers, R=requests (product of two variables)

Example: If you have 10 drivers and 100 requests:
    O(D)     → 10 operations
    O(R)     → 100 operations
    O(D*R)   → 1000 operations
    O(D*R*log(D*R)) → 10 * 100 * log(1000) ≈ 10,000 operations


METHODS USED IN HELPERS
=======================

1. ITERATION (for loops)
   - Loop through all items: for item in items → O(N)
   - Nested loops: for x in list1: for y in list2 → O(N²) or O(D*R)
   - Example: collect_offers() loops through proposals → O(P) where P=proposals

2. SORTING
   - sort() uses Timsort (O(N log N) worst case)
   - Python's built-in sort is stable and efficient
   - Example: resolve_conflicts() sorts offers per request → O(O log O)

3. DICTIONARY/DEFAULTDICT
   - Insert, lookup, delete: O(1) average case
   - Useful for grouping items by key: defaultdict(list)
   - Example: resolve_conflicts() groups offers by request ID → O(1) grouping + O(N log N) sorting

4. LIST OPERATIONS
   - append(): O(1) amortized
   - extend(): O(M) where M is items to add
   - access by index: O(1)
   - Example: gen_requests() uses extend() → O(R) for R new requests

5. FILTERING
   - List comprehensions or if statements: O(N) to scan through
   - Example: collect_offers() filters proposals: for d, r in proposals → O(P)

6. CONDITIONAL CHECKS
   - if statements: O(1) per check
   - isinstance(), type() comparison: O(1)
   - Example: collect_offers() type-checks proposals → O(1) per check, O(P) total


9-STEP ORCHESTRATION BREAKDOWN
===============================

Step 1: gen_requests()           - O(R) where R = new requests generated
Step 2: expire_requests()        - O(R) where R = total requests in system
Step 3: get_proposals()          - O(D*R) or O(D*R*log(D*R)) depending on policy
Step 4: collect_offers()         - O(P) where P = proposals (at most D*R)
Step 5: resolve_conflicts()      - O(O log O) where O = accepted offers
Step 6: assign_requests()        - O(A) where A = finalized assignments
Step 7: move_drivers()           - O(D) where D = active drivers
        + handle_pickup()        - O(1) per driver
        + handle_dropoff()       - O(1) per driver
Step 8: mutate_drivers()         - O(D) or O(D*M) where M = mutation cost
Step 9: time increment           - O(1)

Total per tick: O(D*R*log(D*R) + D + R)
With typical params (D~10, R~100): ~10,000 operations per tick


WHEN TO USE WHICH METHOD
========================

Use O(N) loops when:        You need to check every item exactly once
Use O(N²) loops when:       You need all pairs or nested checking
Use dictionaries when:      You need fast lookups or grouping by key
Use sorting when:           You need items in specific order (O(N log N))
Use filtering when:         You need a subset of items (O(N) to scan)
Use constants when:         Operation is always the same cost regardless of input

"""

from ..request import Request, WAITING, ASSIGNED, PICKED, EXPIRED
from ..offer import Offer
from ..point import Point
from ..driver import Driver
from ..behaviours import LazyBehaviour, GreedyDistanceBehaviour, EarningsMaxBehaviour
import random


# ====================================================================
# DICT <-> OBJECT CONVERSION HELPERS (for adapter)
# ====================================================================

def _assign_random_behaviour() -> "DriverBehaviour":
    """Randomly assign one of three driver behaviours.
    
    Pure function: only creates and returns a behaviour object without side effects.
    Does not store threshold data; behaviours use their defaults.
    Thresholds are only applied during simulation (mutation, decision-making).
    
    Returns:
        DriverBehaviour: One of GreedyDistanceBehaviour, EarningsMaxBehaviour, or LazyBehaviour
        chosen with equal probability (1/3 each).
        
    Example:
        >>> behaviour = _assign_random_behaviour()
        >>> type(behaviour).__name__ in ["GreedyDistanceBehaviour", "EarningsMaxBehaviour", "LazyBehaviour"]
        True
    """
    choice = random.choice(["greedy", "earnings", "lazy"])
    
    if choice == "greedy":
        return GreedyDistanceBehaviour()
    elif choice == "earnings":
        return EarningsMaxBehaviour()
    else:  # choice == "lazy"
        return LazyBehaviour()


def create_driver_from_dict(d_dict: dict, idx: int = 0) -> "Driver":
    """Convert a driver dict to a Driver object. O(1).
    
    Args:
        d_dict: Dict with keys 'x', 'y', optionally 'id', 'speed'.
        idx: Fallback id if 'id' not in dict.
    
    Returns:
        Driver object with randomly assigned behaviour.
    """
    return Driver(
        id=d_dict.get("id", idx),
        position=Point(d_dict["x"], d_dict["y"]),
        speed=d_dict.get("speed", 1.5),
        behaviour=_assign_random_behaviour(),
    )


def create_request_from_dict(r_dict: dict) -> "Request":
    """Convert a request dict to a Request object. O(1).
    
    Args:
        r_dict: Dict with keys 'id', 'px', 'py', 'dx', 'dy', 
                and optionally 'creation_time' or 't'.
    
    Returns:
        Request object.
    """
    creation_time = r_dict.get("creation_time", r_dict.get("t", 0))
    return Request(
        id=r_dict["id"],
        pickup=Point(r_dict["px"], r_dict["py"]),
        dropoff=Point(r_dict["dx"], r_dict["dy"]),
        creation_time=creation_time,
    )


def request_to_dict(req: "Request") -> dict:
    """Convert a Request object to a dict for GUI. O(1)."""
    return {
        "id": req.id,
        "px": req.pickup.x,
        "py": req.pickup.y,
        "dx": req.dropoff.x,
        "dy": req.dropoff.y,
        "creation_time": req.creation_time,
    }


def get_plot_data_from_state(state: dict):
    """Extract plot-ready tuples from state dict. O(D+R).
    
    Args:
        state: State dict with 'drivers' and 'pending' keys.
    
    Returns:
        (drivers_xy, pickup_xy, dropoff_xy, dir_quiver) tuples.
    """
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

def gen_requests(simulation):
    """Generate new requests via request_generator.maybe_generate(), and inject pre-loaded CSV requests. O(R)."""
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
    """Mark WAITING requests as EXPIRED if age > timeout. Increment expired_count. O(R)."""
    for r in simulation.requests:
        if r.status == WAITING and (simulation.time - r.creation_time) > simulation.timeout:
            r.mark_expired(simulation.time)
            simulation.expired_count += 1


def get_proposals(simulation):
    """Get driver-request pairs from dispatch_policy.assign(). O(D*R)."""
    return simulation.dispatch_policy.assign(simulation.drivers, simulation.requests, simulation.time)


def collect_offers(simulation, proposals):
    """Convert proposals to offers, apply behaviour.decide() logic. O(P)."""
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
        off = Offer(d, r, travel_time, reward)
        if d.behaviour and d.behaviour.decide(d, off, simulation.time):
            offers.append(off)
    return offers


def resolve_conflicts(simulation, offers):
    """Group offers by request, keep only nearest driver per request. O(O*log O)."""
    if not isinstance(offers, list):
        raise TypeError(f"offers must be list, got {type(offers).__name__}")
    
    from collections import defaultdict
    grouped = defaultdict(list)
    for o in offers:
        grouped[o.request.id].append(o)
    final = []
    for same_req in grouped.values():
        same_req.sort(key=lambda o: o.driver.position.distance_to(o.request.pickup))
        final.append(same_req[0])
    return final


def assign_requests(simulation, final):
    """Assign drivers to requests (if WAITING + IDLE). Call driver.assign_request(). O(A)."""
    for o in final:
        if o.request.status == WAITING and o.driver.status == "IDLE":
            o.driver.assign_request(o.request, simulation.time)


def move_drivers(simulation):
    """Move active drivers toward target. Detect arrivals (distance < EPSILON). O(D)."""
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
    """Mark request as picked up. Call driver.complete_pickup(). O(1)."""
    driver.complete_pickup(simulation.time)


def handle_dropoff(simulation, driver):
    """Complete delivery. Record earnings & wait time. Increment served_count. O(1)."""
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
    """Apply mutation_rule.maybe_mutate() to each driver. O(D)."""
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


