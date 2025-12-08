import random
from typing import List
from .request import Request
from .point import Point

class RequestGenerator:
    """
    Simple request generator for food delivery simulation.
    Generates requests at a fixed average rate per tick, compatible with Phase 1 and Phase 2.
    """

    def __init__(self, rate: float, width: int, height: int, start_id: int = 1):
        self.rate = rate        # expected number of requests per tick
        self.width = width      # map width
        self.height = height    # map height
        self.next_id = start_id # next request ID

    def maybe_generate(self, time: int) -> List[Request]:
        """
        Called once per tick.
        Generates a number of requests based on `self.rate` (Gaussian variation),
        ensures pickup != dropoff, and returns a list of Request objects.
        """
        # Number of new requests this tick (rounded and clipped to >=0)
        num_requests = max(0, int(random.gauss(self.rate, 1)))

        new_requests: List[Request] = []

        for _ in range(num_requests):
            # Generate random pickup coordinates
            px = random.uniform(0, self.width)
            py = random.uniform(0, self.height)

            # Generate dropoff coordinates, ensure different from pickup
            dx, dy = px, py
            while dx == px and dy == py:
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
