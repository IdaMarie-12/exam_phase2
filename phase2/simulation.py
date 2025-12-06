from collections import defaultdict
from .request import RequestStatus
from .offer import Offer

EPSILON = 1e-3
MIN_SPEED = 1e-6

class DeliverySimulation:
    """
    Orchestrates a delivery simulation by generating requests, assigning
    drivers, moving them, completing pickups/dropoffs, and tracking stats.
    Tick loop is short; detailed logic is delegated to helper methods. Initializes with
    zero completed, expired requests, empty wait-time and earnings records,
    which are incrementally updated to monitor system statistics and driver behavior.
    """
    def __init__(self, drivers, dispatch_policy, request_generator, mutation_rule, timeout=20):
        self.time = 0
        self.drivers = drivers
        self.requests = []

        self.dispatch_policy = dispatch_policy
        self.request_generator = request_generator
        self.mutation_rule = mutation_rule
        self.timeout = timeout

        self.served_count = 0
        self.expired_count = 0
        self._wait_samples = []
        self.avg_wait = 0.0
        self.earnings_by_behaviour = defaultdict(list)

    # -----------------------------------------------------
    #                    MAIN TICK
    def tick(self):
        """Performs one simulation step: generate, expire, propose, offer, resolve, assign, move, mutate."""
        # Step 1: Generate new requests
        self._gen_requests()
        # Step 2: Expire old requests
        self._expire_requests()
        # Step 3: Ask policy for driver-request proposals
        proposals = self._get_proposals()
        # Step 4: Let drivers accept/reject offers
        offers = self._collect_offers(proposals)
        # Step 5: Resolve conflicts (one driver per request)
        final = self._resolve_conflicts(offers)
        # Step 6: Assign drivers to requests
        self._assign(final)
        # Step 7: Move drivers and handle pickups/dropoffs
        self._move_drivers()
        # Step 8: Mutate driver behaviour
        self._mutate()
        # Step 9: Advance simulation time
        self.time += 1
