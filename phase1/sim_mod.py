from .helpers_1 import sim_helper as hf

"""
Phase 1 Simulation Module (Adapter for Phase 2)

This module bridges Phase 1's simulation interface with Phase 2's advanced engine.
It can work in two modes:
  1. Phase 1 Mode: Uses Phase 1's procedural simulation (original implementation)
  2. Phase 2 Mode: Delegates to Phase 2's OOP engine when available

The mode is determined automatically based on what's available in the environment.
"""

# Module-level flag and state for Phase 2 delegation
_USE_PHASE2 = False  # Disabled by default - use Phase 1
_phase2_adapter = None
_phase2_backend = None

try:
    # Try to import Phase 2 adapter (but don't use it by default)
    import os
    from sys import path as syspath
    phase2_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2')
    if phase2_path not in syspath:
        syspath.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from phase2 import adapter as phase2_adapter
    _phase2_backend = phase2_adapter.create_phase2_backend()
    # _USE_PHASE2 = True  # Uncomment this line to enable Phase 2
except ImportError:
    _USE_PHASE2 = False
    _phase2_adapter = None
    _phase2_backend = None


def init_state(drivers, requests, timeout: int = 10, req_rate: float = 3, width: int = 50, height: int = 30):
    """ Initialize and return the full simulation state dictionary.
    
    When Phase 2 is available, delegates to Phase 2's advanced engine.
    Otherwise, falls back to Phase 1's procedural simulation.
    """
    if _USE_PHASE2 and _phase2_backend:
        # Use Phase 2's advanced engine
        return _phase2_backend["init_state"](drivers, requests, timeout, req_rate, width, height)
    else:
        # Fall back to Phase 1's procedural simulation
        state = {
            "t": 0,  # Simulation time starts at 0
            "drivers": drivers,  # List of drivers dictionaries
            "pending": [],  # Requests currently being processed
            "future": requests,  # Requests scheduled for future steps
            "served": 0,  # Number of served requests
            "expired": 0,  # Number of expired requests
            "timeout": timeout,  # Max waiting time for requests before it expires
            "served_waits": [],  # List to track waiting time for served requests
            "req_rate": req_rate,  # The rate for generating new requests
            "width": width,  # Grid width
            "height": height,  # Grid height
            "printed_summary": False,
            "sum_wait": 0.0,
            "total_served_for_avg": 0,
        }
        return state


def simulate_step(state):
    """ Advance simulation by one tick.
    
    When Phase 2 is available, uses its advanced engine.
    Otherwise, falls back to Phase 1's procedural simulation.
    """
    if _USE_PHASE2 and _phase2_backend:
        # Use Phase 2's advanced engine
        return _phase2_backend["simulate_step"](state)
    else:
        # Fall back to Phase 1's procedural simulation
        return _simulate_step_phase1(state)


def _simulate_step_phase1(state):
    """ Phase 1's original procedural simulation logic. """
    # 1. Update the simulation time by one step
    state["t"] += 1

    # 2. Start any new requests that are ready to run
    new_requests = [req for req in state["future"] if req["t"] == state["t"]]
    for req in new_requests:
        req["status"] = "waiting"  # Set new requests to waiting status
    state["pending"].extend(new_requests)  # Move new requests to pending
    state["future"] = [req for req in state["future"] if req["t"] > state["t"]]  # Remove activated requests from future

    # 3. Make sure the dropoffs list exists in state
    if "dropoffs" not in state:
        state["dropoffs"] = []

    # 4. Assign available drivers to waiting requests
    for req in state["pending"]:
        if req["status"] == "waiting":
            # Find nearest available driver (one without target_id)
            driver = hf.find_nearest_avb_driver(state["drivers"], (req["px"], req["py"]))
            if driver:
                req["driver_id"] = driver["driver_id"]  # Assign driver to request
                req["status"] = "assigned"  # Mark request as assigned
                driver["target_id"] = req["id"]  # Assign request to driver
                driver["tx"] = req["px"]  # Set driver's target x to pickup location
                driver["ty"] = req["py"]  # Set driver's target y to pickup location
                driver["status"] = "assigned"  # Mark driver as assigned

    # 5. Move drivers towards their current targets (pickup or dropoff)
    for driver in state["drivers"]:
        if driver.get("target_id") is not None:
            req = next((req for req in state["pending"] if req["id"] == driver["target_id"]), None)
            if req:
                if req["status"] == "assigned":
                    # Move driver towards the pickup location
                    hf.move_driver_towards(driver, (req["px"], req["py"]), driver["speed"])
                elif req["status"] == "picked":
                    # Move driver towards the dropoff location
                    hf.move_driver_towards(driver, (req["dx"], req["dy"]), driver["speed"])

    # 6. Handle pickups and dropoffs
    served = []
    for req in state["pending"]:
        if req.get("driver_id") is not None:
            driver = next((driver for driver in state["drivers"] if driver["driver_id"] == req["driver_id"]), None)
            if driver:
                # If driver has reached the pickup location, pick up the request
                if req["status"] == "assigned" and hf.at_target(driver, (req["px"], req["py"])):
                    req["status"] = "picked"
                    driver["tx"] = req["dx"]  # Set drivers target x to requests dropoff x
                    driver["ty"] = req["dy"]  # Set drivers target y to requests dropoff y
                # If driver has reached the dropoff location, complete the request
                elif req["status"] == "picked" and hf.at_target(driver, (req["dx"], req["dy"])):
                    req["status"] = "delivered"
                    served.append(req)  # Add to list of served requests
                    state["dropoffs"].append((driver["x"], driver["y"]))  # Save dropoff location
                    hf.clear_driver_target(driver)  # Clear driver's target
                    driver["status"] = "free"  # Mark driver as free again
                    req["driver_id"] = None  # Unassign driver from request

    # 7. Mark requests as expired if they have waited too long
    expired = []
    max_wait = state.get("timeout")
    for req in state["pending"]:
        wait_time = state["t"] - req["t"]
        if req["status"] == "waiting" and wait_time > max_wait:
            req["status"] = "expired"
            expired.append(req)

    # 8. Updates statistics
    state["served"] += len(served)
    state["expired"] += len(expired)

    # 9. Calculates average waiting time for requests served this step
    if served:
        avg_wait = sum(state["t"] - req["t"] for req in served) / len(served)
    else:
        avg_wait = 0.0

    # 10. Updates cumulative waiting time and total served for overall average (optional)
    state["sum_wait"] = state.get("sum_wait", 0) + sum(state["t"] - req["t"] for req in served)
    state["total_served_for_avg"] = state.get("total_served_for_avg", 0) + len(served)

    # 11. Removes served and expired requests from pending
    state["pending"] = [req for req in state["pending"] if req["status"] in ("waiting", "assigned", "picked")]

    # 12. Collects metrics for current simulation step
    metrics = {"served": len(served), "expired": len(expired), "avg_wait": avg_wait}

    # 13. Check our own internal horizon and print once when reached
    if (not state["printed_summary"]
            and not state["pending"]
            and not state["future"]
            and state["t"] > 0):
        total_served = state["served"]
        total_expired = state["expired"]
        total_requests = total_served + total_expired

        if state["total_served_for_avg"] > 0:
            overall_avg_wait = state["sum_wait"] / state["total_served_for_avg"]
        else:
            overall_avg_wait = 0.0

        print("Simulation Summary:")
        print(f"Total requests served: {total_served}")
        print(f"Total requests expired: {total_expired}")
        print(f"Total requests handled: {total_requests}")
        print(f"Overall average waiting time: {overall_avg_wait:.2f} units")

        state["printed_summary"] = True

    return state, metrics