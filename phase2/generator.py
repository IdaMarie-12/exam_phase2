import random
from typing import List
from phase2.point import Point
from phase2.request import Request


class RequestGenerator:
    """
    Request generator for food delivery simulation.
    Generates requests at a Poisson-distributed rate, compatible with Phase 1 and Phase 2.
    
    Uses Poisson distribution to model realistic event arrival patterns where requests
    arrive randomly over time with an average rate (e.g., "3 requests per tick on average").
    Over many ticks, the actual count varies: sometimes 0, sometimes 2-3, averaging to rate.
    """

    def __init__(self, rate: float, width: int, height: int, start_id: int = 1):
        """
        Initialize the request generator.
        
        Args:
            rate: Expected number of requests per tick (lambda parameter for Poisson)
            width: Map width (for random position generation)
            height: Map height (for random position generation)
            start_id: First request ID to use (incremented with each request)
            
        Raises:
            ValueError: If rate < 0
        """
        if rate < 0:
            raise ValueError(f"Request rate must be non-negative, got {rate}")
        self.rate = rate        # expected number of requests per tick (Poisson lambda)
        self.width = width      # map width
        self.height = height    # map height
        self.next_id = start_id # next request ID

    def maybe_generate(self, time: int) -> List[Request]:
        """
        Generate a stochastic number of requests at the given time.
        
        Called once per simulation tick. Uses Poisson distribution to determine
        how many requests are created (realistic distribution for event arrivals).
        
        Args:
            time: Current simulation time (becomes creation_time for requests)
            
        Returns:
            List[Request]: List of newly generated Request objects (may be empty)
            
        Notes:
            - Number of requests follows Poisson(rate) distribution
            - Pickup and dropoff locations are guaranteed to be different
            - Request IDs are auto-incremented
            
        Example:
            >>> gen = RequestGenerator(rate=2.0, width=50, height=50)
            >>> requests = gen.maybe_generate(time=0)
            >>> len(requests) > 0  # Typically 1-3 for rate=2.0
            True
        """
        # Number of new requests this tick using Poisson distribution
        # This matches Phase 1's realistic event arrival pattern
        num_requests = random.poisson(self.rate)

        new_requests: List[Request] = []

        for _ in range(num_requests):
            # Generate random pickup coordinates within bounds
            px = random.uniform(0, self.width)
            py = random.uniform(0, self.height)

            # Generate dropoff coordinates, ensure different from pickup
            # Use floating-point epsilon tolerance for comparison
            dx, dy = px, py
            EPSILON = 1e-9
            while abs(dx - px) < EPSILON and abs(dy - py) < EPSILON:
                dx = random.uniform(0, self.width)
                dy = random.uniform(0, self.height)

            # Create Request object
            req = Request(
                id=self.next_id,
                pickup=Point(px, py),
                dropoff=Point(dx, dy),
                creation_time=time
            )
            self.next_id += 1
            new_requests.append(req)

        return new_requests

