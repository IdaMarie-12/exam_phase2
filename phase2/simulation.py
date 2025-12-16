from collections import defaultdict
from .offer import Offer
from .helpers_2.engine_helpers import (
    gen_requests, expire_requests, get_proposals, collect_offers,
    resolve_conflicts, assign_requests, move_drivers,
    handle_pickup, handle_dropoff, mutate_drivers
)

EPSILON = 1e-3
MIN_SPEED = 1e-6

"""Orchestrates the 9-step delivery simulation with drivers, requests, and policies.
Maintains persistent state and coordinates dispatch decisions, behavior adaptation, and driver movement.
Deterministic tick cycle ensures reproducible simulation outcomes for analysis and testing.
"""

class DeliverySimulation:
    """Main delivery simulation orchestrator with persistent state and policy-driven dispatch."""

    def __init__(self, drivers, dispatch_policy, request_generator, mutation_rule, timeout=20):
        # Initialize with drivers, policy, generator, mutation rule, and timeout.
        if not drivers:
            raise ValueError("DeliverySimulation requires at least one driver")
        if timeout < 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")

        self.time = 0
        self.drivers = drivers
        self.requests = []
        self.offer_history = []  # Track all offers for metrics

        self.dispatch_policy = dispatch_policy
        self.request_generator = request_generator
        self.mutation_rule = mutation_rule
        self.timeout = timeout

        self.served_count = 0
        self.expired_count = 0
        self._wait_samples = []
        self.avg_wait = 0.0
        self.earnings_by_behaviour = defaultdict(list)


    # ================================================================
    # MAIN TICK (9-phase orchestration)
    # ================================================================

    def tick(self):
        """Run one simulation tick (9 phases): generate, expire, propose, collect, resolve, assign, move, mutate, increment time."""
        # step 1: Generate new requests via stochastic process
        gen_requests(self)
        # step 2: Expire old requests (age >= timeout)
        expire_requests(self)
        # step 3: Policy proposes driver-request pairs
        proposals = get_proposals(self)
        # step 4: Drivers accept/reject via behaviour evaluation
        offers = collect_offers(self, proposals)
        # step 5: Resolve conflicts (one driver per request, nearest wins)
        final = resolve_conflicts(self, offers)
        # step 6: Finalize assignments (update statuses, link objects)
        assign_requests(self, final)
        # step 7: Move drivers toward destinations, handle arrivals
        move_drivers(self)
        # step 8: Apply behaviour mutations if configured
        mutate_drivers(self)
        # step 9: Increment global time
        self.time += 1


    # ================================================================
    # Statistics and Snapshots
    # ================================================================

    def get_snapshot(self):
        """Returns JSON-serializable state including driver positions, requests, and metrics."""
        return {
            "time": self.time,
            "drivers": [
                {
                    "id": d.id,
                    "x": d.position.x,
                    "y": d.position.y,
                    "status": d.status,
                    "rid": d.current_request.id if d.current_request else None,  # current request assignment
                    "tx": d.current_request.pickup.x if (d.current_request and d.current_request.status in ("WAITING", "ASSIGNED")) else (d.current_request.dropoff.x if d.current_request else None),
                    "ty": d.current_request.pickup.y if (d.current_request and d.current_request.status in ("WAITING", "ASSIGNED")) else (d.current_request.dropoff.y if d.current_request else None),
                }
                for d in self.drivers
            ],
            "pickups": [{"id": r.id, "x": r.pickup.x, "y": r.pickup.y} for r in self.requests
                        if r.status in ("WAITING", "ASSIGNED")],
            "dropoffs": [{"id": r.id, "x": r.dropoff.x, "y": r.dropoff.y} for r in self.requests
                         if r.status == "PICKED"],
            "statistics": {
                "served": self.served_count,
                "expired": self.expired_count,
                "avg_wait": self.avg_wait,
            },
        }

