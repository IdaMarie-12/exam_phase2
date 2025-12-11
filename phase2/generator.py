import random
import math
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from phase2.request import Request
    from phase2.point import Point


def _generate_poisson(rate: float) -> int:
    """Generate a Poisson-distributed random number (Knuth's algorithm)."""
    if rate < 0:
        raise ValueError(f"rate must be non-negative, got {rate}")
    
    if rate == 0:
        return 0
    
    # Knuth's algorithm
    L = math.exp(-rate)
    k = 0
    p = 1.0
    
    while p > L:
        k += 1
        p *= random.random()
    
    return k - 1

# ====================================================================
# Request Generator
# ====================================================================

class RequestGenerator:
    """
    Request generator using Poisson distribution.
    """

    def __init__(self, rate: float, width: int, height: int, start_id: int = 1,
                 enabled: bool = True):
        """
        Initialize the request generator.
        """
        if rate < 0:
            raise ValueError(f"Request rate must be non-negative, got {rate}")
        if width <= 0:
            raise ValueError(f"Map width must be positive, got {width}")
        if height <= 0:
            raise ValueError(f"Map height must be positive, got {height}")
        
        self.rate = rate           # Expected number of requests per tick (Poisson λ)
        self.width = width         # Map width for position bounds
        self.height = height       # Map height for position bounds
        self.next_id = start_id    # Next request ID to use (auto-incremented)
        self.enabled = enabled     # Whether to generate requests

    def maybe_generate(self, time: int) -> List["Request"]:
        """
        Generate requests at the given simulation time.
        """
        # If disabled, return empty list (used when CSV requests are loaded)
        if not self.enabled:
            return []
        
        # Import here to avoid circular imports at module level
        from phase2.request import Request
        from phase2.point import Point
        
        # Generate number of requests from Poisson distribution
        # This models realistic stochastic event arrival
        num_requests = _generate_poisson(self.rate)

        new_requests: List[Request] = []

        for _ in range(num_requests):
            # Generate random pickup coordinates within map bounds
            px = random.uniform(0, self.width)
            py = random.uniform(0, self.height)

            # Generate dropoff coordinates, ensure different from pickup
            # Use epsilon tolerance for floating-point comparison
            EPSILON = 1e-9
            dx, dy = px, py  # Initialize same as pickup
            
            # Keep generating until pickup != dropoff (within tolerance)
            while abs(dx - px) < EPSILON and abs(dy - py) < EPSILON:
                dx = random.uniform(0, self.width)
                dy = random.uniform(0, self.height)

            # Create Request object with auto-incremented ID and current time
            req = Request(
                id=self.next_id,
                pickup=Point(px, py),
                dropoff=Point(dx, dy),
                creation_time=time
            )
            self.next_id += 1
            new_requests.append(req)

        return new_requests

    def get_state(self) -> dict:
        """Get current generator state for serialization/debugging."""
        return {
            'rate': self.rate,
            'width': self.width,
            'height': self.height,
            'next_id': self.next_id,
            'total_generated': self.next_id - 1,
        }

