"""
Request generation for food delivery simulation.

This module provides the RequestGenerator class for creating food delivery requests
at runtime during simulation. It models realistic request arrival patterns using a
Poisson distribution (matching Phase 1 design), where requests appear randomly over
time with a configurable average rate.

Architecture:
    RequestGenerator
        └── Generates Request objects with random pickup/dropoff locations
        └── Stochastic arrival (Poisson distribution)
        └── Compatible with Phase 1 io_mod.py interface

Lifecycle:
    1. Simulation creates RequestGenerator(rate=2.0, width=50, height=50)
    2. On each tick, calls generator.maybe_generate(current_time)
    3. Generator stochastically produces 0-N requests at that time
    4. Simulation adds requests to active list
    5. Process repeats each tick

Distribution Model:
    Requests follow Poisson(λ) distribution where λ = rate.
    - Realistic: models random event arrival (like food orders)
    - Stochastic: same rate produces different counts each call
    - Phase 1 Compatible: uses same Poisson approach as procedural version
    
    For rate=2.0 per tick over 100 ticks:
    - Expected total: 200 requests
    - Some ticks: 0, some: 4-5, averaging to 2.0

Example Usage:
    >>> gen = RequestGenerator(rate=2.5, width=50, height=30)
    >>> # Each tick:
    >>> requests = gen.maybe_generate(time=100)
    >>> # Typically 2-3 requests, with IDs auto-incremented
    >>> for req in requests:
    ...     print(f"Request {req.id} at ({req.pickup.x}, {req.pickup.y})")
"""

import random
import math
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from phase2.request import Request
    from phase2.point import Point


def _generate_poisson(rate: float) -> int:
    """
    Generate a Poisson-distributed random number using Knuth's algorithm.
    
    Works with standard library only (no NumPy required).
    
    Args:
        rate: Lambda parameter (expected value)
        
    Returns:
        Poisson-distributed integer
    """
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
    Stochastic request generator for food delivery simulation.
    
    Generates food delivery requests at runtime with realistic arrival patterns.
    Requests appear randomly according to a Poisson distribution, modelling
    realistic event arrivals where orders come at unpredictable times but with
    a predictable average rate.
    
    Design Philosophy:
        - **Stochasticity:** Realistic (not uniform) request arrival
        - **Configurability:** Rate tunable for experiment
        - **Compatibility:** Works with Phase 1 io_mod.py patterns
        - **Simplicity:** Easy to understand and extend
    
    Parameters:
        rate: Expected number of requests per tick (Poisson λ)
              - 0.5: ~1 request every 2 ticks
              - 2.0: ~2 requests per tick
              - 5.0: ~5 requests per tick
        width: Map width (for random position bounds)
        height: Map height (for random position bounds)
        start_id: First request ID (incremented automatically)
    
    Characteristics:
        - Requests generated on-demand (not precomputed)
        - ID auto-incrementing ensures uniqueness
        - Pickup and dropoff guaranteed different
        - Locations uniformly random within bounds
        - Time is set to current simulation tick
    
    Phase 1 Compatibility:
        This design matches Phase 1's generate_requests() function:
        - Same Poisson distribution
        - Same random location generation
        - Same parameter interface
        - Differences: now as OO class, generates Request objects
    
    Example Scenario (100 ticks, rate=2.0):
        >>> gen = RequestGenerator(rate=2.0, width=50, height=50)
        >>> total = 0
        >>> for tick in range(100):
        ...     reqs = gen.maybe_generate(tick)
        ...     total += len(reqs)
        >>> total  # ~200 requests over 100 ticks
        
    Use Cases:
        - Continuous simulation (requests appear over time)
        - Experiment with different arrival rates
        - Study system behavior under varying load
        - Realistic delivery dispatch testing
    """

    def __init__(self, rate: float, width: int, height: int, start_id: int = 1):
        """
        Initialize the request generator.
        
        Args:
            rate: Expected number of requests per tick (lambda for Poisson distribution)
                  Must be >= 0. For typical food delivery: 1-5.
            width: Map width in coordinate units (for random position generation)
                   Should match simulation map width.
            height: Map height in coordinate units (for random position generation)
                    Should match simulation map height.
            start_id: First request ID (default: 1). Each generated request gets
                      auto-incremented ID starting from this value.
            
        Raises:
            ValueError: If rate < 0 or width/height <= 0
            
        Example:
            >>> gen = RequestGenerator(rate=2.0, width=50, height=30, start_id=1)
            >>> gen.rate
            2.0
            >>> gen.width
            50
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

    def maybe_generate(self, time: int) -> List["Request"]:
        """
        Generate stochastic requests at the given simulation time.
        
        Called once per simulation tick. Draws a random number from Poisson(rate)
        distribution and creates that many Request objects with current time as
        creation_time. Pickup and dropoff locations are randomly generated within
        the map bounds and guaranteed to be different.
        
        Process:
        1. Draw number of requests from Poisson(rate) distribution
        2. For each request:
           a. Generate random pickup location (px, py)
           b. Generate random dropoff location (dx, dy) != (px, py)
           c. Create Request object with auto-incremented ID
        3. Increment next_id for all created requests
        4. Return list of new Request objects
        
        Args:
            time: Current simulation time (becomes creation_time for all requests)
                  Measured in ticks (integer, typically 0-1000+)
            
        Returns:
            List[Request]: Newly generated requests (may be empty if Poisson draws 0)
            
        Notes:
            - Number of requests follows Poisson(rate) distribution
            - Pickup and dropoff are guaranteed different (epsilon comparison)
            - All requests have status='WAITING' by default (set in Request.__init__)
            - Request IDs are unique across all generator.maybe_generate() calls
            
        Example:
            >>> gen = RequestGenerator(rate=2.0, width=50, height=50)
            >>> requests = gen.maybe_generate(time=0)
            >>> len(requests)  # Typically 0-4 for rate=2.0
            2
            >>> requests[0].id
            1
            >>> requests[1].id
            2
            >>> requests[0].creation_time
            0
            >>> gen.next_id
            3
            
        Performance:
            - Time complexity: O(k) where k = Poisson(rate) drawn number
            - Expected: O(rate) on average
            - Practical: negligible for typical rates (< 10)
        """
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
        """
        Get current generator state for serialization or debugging.
        
        Returns:
            dict: Generator configuration and state with keys:
                - 'rate': Current request rate (Poisson λ)
                - 'width': Map width
                - 'height': Map height
                - 'next_id': Next request ID to be used
                - 'total_generated': (Computed) estimated total requests generated
                
        Example:
            >>> gen = RequestGenerator(rate=2.0, width=50, height=50)
            >>> gen.maybe_generate(0)  # Generate some requests
            >>> state = gen.get_state()
            >>> state['rate']
            2.0
            >>> state['next_id'] > 1
            True
        """
        return {
            'rate': self.rate,
            'width': self.width,
            'height': self.height,
            'next_id': self.next_id,
            'total_generated': self.next_id - 1,
        }

