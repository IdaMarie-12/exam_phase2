from ..request import RequestStatus, WAITING, ASSIGNED, PICKED, EXPIRED
from ..offer import Offer


# ====================================================================
# SIMULATION HELPER METHODS (from DeliverySimulation class)
# ====================================================================

def gen_requests(simulation):
    """
    Generate new requests using Poisson stochasticity.

    Process:
        1. Call request_generator.maybe_generate(current_time)
        2. Add generated requests to simulation.requests list

    Performance: O(R) where R = requests generated in this tick
    """
    new_reqs = simulation.request_generator.maybe_generate(simulation.time)
    if new_reqs:
        simulation.requests.extend(new_reqs)


def expire_requests(simulation):
    """
    Mark old waiting requests as expired if they exceed timeout.

    Logic:
        For each request in WAITING status:
            if (current_time - creation_time) > timeout:
                call request.mark_expired(time)
                increment expired_count

    Performance: O(R) where R = all requests
    """
    for r in simulation.requests:
        if r.status == WAITING and (simulation.time - r.creation_time) > simulation.timeout:
            r.mark_expired(simulation.time)
            simulation.expired_count += 1


def get_proposals(simulation):
    """
    Ask dispatch policy for driver-request pairs.

    Interface:
        Calls dispatch_policy.assign(drivers, requests, time)

    Returns:
        List of (driver, request) tuples

    Performance: O(D*R) worst case, depending on policy
    """
    return simulation.dispatch_policy.assign(simulation.drivers, simulation.requests, simulation.time)


def collect_offers(simulation, proposals):
    """
    Convert proposals to offers, applying driver behaviour acceptance logic.

    Process:
        For each (driver, request) proposal:
            1. Skip if request not in WAITING status
            2. Create Offer object (with travel_time, reward)
            3. Query driver.behaviour.decide() for acceptance
            4. If accepted: add to offers list

    Performance: O(P) where P = len(proposals)
    """
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
    """
    Resolve multiple offers for same request (nearest driver wins).

    Conflict Case:
        If two drivers offer same request:
        - Calculate distance for each offer
        - Nearest driver (L2 norm) gets the assignment
        - Other offer is dropped

    Algorithm:
        1. Group offers by request ID
        2. For each request with multiple offers:
           - Sort by distance to request.pickup location
           - Keep only nearest
        3. Return final (driver, request) pairs

    Performance: O(O*log(O)) where O = len(offers)
    """
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
    """
    Finalize driver-request assignments and update statuses.

    Process:
        For each (driver, request) assignment:
            1. Check both available (request WAITING, driver IDLE)
            2. Call driver.assign_request(request, time)

    Performance: O(A) where A = len(assignments)
    """
    for o in final:
        if o.request.status == WAITING and o.driver.status == "IDLE":
            o.driver.assign_request(o.request, simulation.time)


def move_drivers(simulation):
    """
    Move all active drivers toward their destinations.

    Process:
        For each driver with active assignment:
            1. Check if status is TO_PICKUP or TO_DROPOFF
            2. Move toward target at driver.speed (constant velocity)
            3. Check arrival detection (distance < EPSILON)
            4. If arrived: trigger pickup or dropoff event

    Performance: O(D) where D = drivers with assignments
    """
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
    """
    Handle pickup event: customer enters vehicle.

    Logic:
        - Call driver.complete_pickup(current_time)
        - Driver state updated internally
        - Next destination becomes dropoff

    Performance: O(1)
    """
    driver.complete_pickup(simulation.time)


def handle_dropoff(simulation, driver):
    """
    Handle dropoff event: request completed, driver becomes idle.

    Logic:
        1. Call driver.complete_dropoff(current_time)
        2. Extract earnings from driver.history
        3. Record earnings by behaviour type
        4. Calculate and update wait time statistics
        5. Increment served_count

    Performance: O(1)
    """
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
    """
    Apply behaviour mutations if mutation rule is configured.

    Process:
        If mutation_rule is not None:
            For each driver:
                mutation_rule.maybe_mutate(driver, current_time)
                May modify driver.behaviour based on performance

    Performance: O(D) where D = number of drivers
    """
    for d in simulation.drivers:
        simulation.mutation_rule.maybe_mutate(d, simulation.time)


# ====================================================================
# ADAPTER HELPERS (for phase2/adapter.py)
# ====================================================================

def sim_to_state_dict(simulation):
    """
    Convert DeliverySimulation to GUI-compatible state dict.
    
    Used by adapter.py to translate OOP objects to procedural interface.
    
    Args:
        simulation: DeliverySimulation instance
        
    Returns:
        Dict with keys: t, drivers, pending, served, expired
    """
    snap = simulation.get_snapshot()
    
    # Convert driver snapshots to GUI format
    drivers = []
    for driver_snap in snap['drivers']:
        drivers.append({
            'id': driver_snap['id'],
            'x': driver_snap['x'],
            'y': driver_snap['y'],
            'status': driver_snap['status'],
        })
    
    # Convert request snapshots to GUI format
    pending = []
    
    # Pickups (WAITING/ASSIGNED)
    for pickup_snap in snap['pickups']:
        pending.append({
            'id': pickup_snap['id'],
            'px': pickup_snap['x'],
            'py': pickup_snap['y'],
            'status': 'waiting',
        })
    
    # Dropoffs (PICKED)
    for dropoff_snap in snap['dropoffs']:
        pending.append({
            'id': dropoff_snap['id'],
            'dx': dropoff_snap['x'],
            'dy': dropoff_snap['y'],
            'status': 'picked',
        })
    
    return {
        't': snap['time'],
        'drivers': drivers,
        'pending': pending,
        'served': snap['statistics']['served'],
        'expired': snap['statistics']['expired'],
    }


def get_adapter_metrics(simulation):
    """
    Extract metrics dict for GUI display.
    
    Args:
        simulation: DeliverySimulation instance
        
    Returns:
        Dict with keys: served, expired, avg_wait
    """
    return {
        'served': simulation.served_count,
        'expired': simulation.expired_count,
        'avg_wait': simulation.avg_wait,
    }

# ====================================================================
# ADAPTER HELPER FUNCTIONS (for state conversion)
# ====================================================================

def sim_to_state_dict(simulation):
    """
    Convert OOP DeliverySimulation to procedural state dict.
    
    Used by adapter to translate simulation state for GUI compatibility.
    
    Args:
        simulation: DeliverySimulation instance
        
    Returns:
        dict with keys:
            - "t": current time
            - "drivers": list of driver dicts with x, y, status
            - "pending": list of request dicts
            - "served": count of completed deliveries
            - "expired": count of expired requests
            - "avg_wait": average wait time
    
    Performance: O(D + R) where D = drivers, R = requests
    """
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
                "status": r.status,
                "t": r.creation_time,
            }
            for r in simulation.requests
        ],
        "served": simulation.served_count,
        "expired": simulation.expired_count,
        "avg_wait": simulation.avg_wait,
    }


def get_adapter_metrics(simulation):
    """
    Extract metrics dict from simulation for GUI display.
    
    Used by adapter to provide metrics for reporting.
    
    Args:
        simulation: DeliverySimulation instance
        
    Returns:
        dict with keys:
            - "served": completed deliveries
            - "expired": timed-out requests
            - "avg_wait": average wait time (rounded to 2 decimals)
    
    Performance: O(1)
    """
    return {
        "served": simulation.served_count,
        "expired": simulation.expired_count,
        "avg_wait": round(simulation.avg_wait, 2),
    }


