"""
Dispatch policies for matching drivers to requests.

This module implements various strategies for assigning idle drivers to waiting requests.
Each policy represents a different optimization criterion (proximity, efficiency, etc.)
and can trade off between assignment quality and computational cost.

Architecture:
    DispatchPolicy (ABC)
        ├── NearestNeighbour - Iterative greedy nearest-matching
        └── GlobalGreedy - Global optimization by distance sorting

Lifecycle:
    1. Simulation creates dispatch_policy (e.g., GlobalGreedy)
    2. On each tick, simulation calls policy.assign(drivers, requests, time)
    3. Policy analyzes idle drivers and waiting requests
    4. Policy returns list of (driver, request) proposal pairs
    5. Simulation presents proposals to drivers via offers
    6. Drivers accept/reject based on their behaviours
    7. Engine handles conflicts (multiple drivers for same request)

Example:
    >>> policy = GlobalGreedy()
    >>> proposals = policy.assign(idle_drivers, waiting_requests, time=100)
    >>> # proposals = [(driver1, request3), (driver2, request1), ...]
    >>> # Engine creates Offer for each proposal
    >>> # Drivers decide to accept/reject

Design Notes:
    - Policies work with idle drivers and waiting requests only
    - Policies can propose multiple drivers for same request (conflicts ok)
    - Conflicts resolved by simulation taking closest driver
    - Multiple policies can be compared in experiments
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from phase2.driver import Driver
    from phase2.request import Request


# ====================================================================
# Dispatch Policy Base Class
# ====================================================================

class DispatchPolicy:
    """
    Abstract base class for dispatch policies.
    
    A DispatchPolicy determines which idle drivers should be offered which waiting
    requests. This is the first stage of assignment - it proposes pairs, but drivers
    still get to accept/reject based on their behaviours.
    
    Responsibilities:
        1. Receive lists of idle drivers and waiting requests
        2. Analyze distances/metrics to make matching decisions
        3. Return list of proposed (driver, request) pairs
        4. All proposals are valid (no duplicate driver assignments)
    
    Key Design Decisions:
        - Operates on idle drivers only (not on assigned/moving drivers)
        - Operates on waiting requests only (not picked/delivered/expired)
        - May propose multiple drivers for same request (conflict resolution handled by engine)
        - Called once per simulation tick, so should be efficient
    
    Subclasses implement different optimization strategies:
        - NearestNeighbour: Fast, simple, greedy nearest-first
        - GlobalGreedy: Better quality, sorts all pairs, optimal distance matching
        - Could add: EarningsMax, TrafficAware, LearningBased, etc.
    
    Example Usage:
        >>> policy = NearestNeighbour()
        >>> proposals = policy.assign(drivers, requests, time=0)
        >>> for driver, request in proposals:
        ...     offer = Offer(driver, request, ...)
        ...     if driver.behaviour.decide(driver, offer, time):
        ...         # Accept: engine assigns request
    """

    def assign(self,
                drivers: List["Driver"],
                requests: List["Request"],
                time: int
            ) -> List[Tuple["Driver", "Request"]]:
        """
        Propose driver-request pairs for this tick.
        
        Implementations should:
        1. Filter drivers with status == IDLE
        2. Filter requests with status == WAITING
        3. Analyze distances/metrics to create proposals
        4. Return list of (driver, request) tuples
        
        The simulation will then:
        - Create Offer for each proposal
        - Present offer to driver
        - Handle accept/reject and conflicts
        
        Args:
            drivers: All drivers in simulation (filter for idle yourself)
            requests: All requests in simulation (filter for waiting yourself)
            time: Current simulation time (in ticks)
            
        Returns:
            List[Tuple[Driver, Request]]: Proposed pairs to offer to drivers
            
        Note:
            - Each driver should appear in at most ONE pair (no duplicates)
            - Each request CAN appear in multiple pairs (conflicts ok)
            - Empty list is valid if no proposals
            - Pairs should be sorted by priority (though not required)
        """
        raise NotImplementedError



# ====================================================================
# Nearest Neighbour Policy
# ====================================================================

class NearestNeighbour(DispatchPolicy):
    """
    Greedy nearest-neighbour dispatch policy.
    
    Implements a simple, iterative greedy algorithm: repeatedly find the closest
    idle driver-request pair, assign it, remove both from consideration, and repeat.
    
    Algorithm:
        1. Start with all idle drivers and waiting requests
        2. Find the driver-request pair with smallest distance
        3. Add pair to results, remove both from available
        4. Repeat until no idle drivers or waiting requests remain
    
    Characteristics:
        - **Simplicity:** Easy to understand and implement
        - **Speed:** O(n² * m²) but with early termination when pairs exhausted
        - **Greediness:** Makes locally optimal choice (closest pair) each iteration
        - **Efficiency:** Not globally optimal, but reasonable results
        - **Fair:** All drivers get considered, no starvation
    
    Advantages:
        - Intuitive: matches driver closest to their first pickup
        - Fast for small numbers of drivers/requests
        - Practical performance on real problems
        - Fair distribution (each driver gets opportunity)
    
    Disadvantages:
        - Not globally optimal (greedy doesn't guarantee best total distance)
        - Can leave distant pairs unmatched if early pairs absorb good matches
        - Performance degrades with many idle drivers/requests
    
    Use Cases:
        - Real-time dispatch with latency constraints
        - Small fleets (< 50 drivers)
        - When fairness is important
        - Prototyping/baseline comparisons
    
    Example:
        >>> policy = NearestNeighbour()
        >>> drivers = [Driver(1, Point(0, 0)), Driver(2, Point(10, 0))]
        >>> requests = [Request(1, Point(2, 0), ...), Request(2, Point(11, 0), ...)]
        >>> # Iteration 1:
        >>> #   Distance(D1, R1) = 2.0, Distance(D1, R2) = 11.0
        >>> #   Distance(D2, R1) = 8.0, Distance(D2, R2) = 1.0 ← closest
        >>> #   Propose: (D2, R2)
        >>> # Iteration 2:
        >>> #   Remaining: D1, R1
        >>> #   Distance(D1, R1) = 2.0 ← only pair
        >>> #   Propose: (D1, R1)
        >>> proposals = policy.assign(drivers, requests, time=0)
        >>> # proposals = [(driver2, request2), (driver1, request1)]
    """

    def assign(
            self,
            drivers: List["Driver"],
            requests: List["Request"],
            time: int
        ) -> List[Tuple["Driver", "Request"]]:
        """
        Propose pairs using iterative greedy nearest-neighbour matching.
        
        Process:
        1. Filter idle drivers and waiting requests
        2. While pairs remain:
           a. Find closest driver-request pair
           b. Add to results, remove from consideration
        3. Return all proposed pairs
        
        Args:
            drivers: All drivers (filtered for idle internally)
            requests: All requests (filtered for waiting internally)
            time: Current simulation time
            
        Returns:
            List of (driver, request) pairs, or empty if none available
            
        Example:
            >>> policy = NearestNeighbour()
            >>> proposals = policy.assign(drivers, requests, time=100)
            >>> # [(driver1, request3), (driver2, request1)]
            
        Performance:
            - Worst case: O(n² * m²) for n drivers, m requests
            - Average: much better due to early termination
            - Practical: fast for typical fleet sizes
        """
        # Filter only idle drivers and waiting requests
        idle = [d for d in drivers if getattr(d, "status", None) == d.IDLE]
        waiting = [r for r in requests if getattr(r, "status", None) == r.WAITING]

        pairs: List[Tuple["Driver", "Request"]] = []

        # Greedy iterative nearest matching
        while idle and waiting:
            best_dist = float("inf")  # Initialize best distance as infinity
            best_pair = None           # Initialize best pair as None

            # Find the closest driver-request pair
            for d in idle:
                for r in waiting:
                    # Compute Euclidean distance
                    dist = d.position.distance_to(r.pickup)
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (d, r)
            
            if best_pair is None:
                break  # No valid pair found, exit loop
            
            # Add best pair to result and remove from further consideration
            d_sel, r_sel = best_pair
            pairs.append((d_sel, r_sel))
            idle.remove(d_sel)
            waiting.remove(r_sel)

        return pairs



# ====================================================================
# Global Greedy Policy
# ====================================================================

class GlobalGreedy(DispatchPolicy):
    """
    Global greedy dispatch policy with distance-based optimization.
    
    Implements a global optimization strategy: compute all possible driver-request
    distances, sort pairs by distance, then greedily select shortest pairs while
    ensuring no driver or request appears twice.
    
    Algorithm:
        1. Create list of all (distance, driver, request) tuples
        2. Sort by distance ascending
        3. Iterate through sorted list, selecting pairs:
           - Skip if driver already assigned
           - Skip if request already assigned
           - Add to results otherwise
        4. Return all selected pairs
    
    Characteristics:
        - **Optimality:** Approximates global optimum (not guaranteed)
        - **Complexity:** O(n*m log(n*m)) sorting dominates
        - **Quality:** Better results than nearest-neighbour
        - **Fairness:** May favor early-in-list drivers
        - **Determinism:** Same input → same output (no randomness)
    
    Advantages:
        - Better assignment quality than greedy nearest-neighbour
        - Scales to moderate fleet sizes (< 1000 drivers)
        - Avoids poor local choices by seeing all options
        - Predictable and reproducible
        - Can be fast with modern sorting algorithms
    
    Disadvantages:
        - More complex than nearest-neighbour
        - Still not guaranteed optimal (greedy nature)
        - Memory: stores all n*m pairs
        - CPU: sorting can be expensive for large fleets
    
    Use Cases:
        - Medium to large fleets (50-1000 drivers)
        - When dispatch quality matters more than latency
        - Batch processing (not strict real-time)
        - Comparison/baseline for optimization algorithms
        - Learning how good dispatch affects earnings
    
    Example:
        >>> policy = GlobalGreedy()
        >>> drivers = [Driver(1, Point(0, 0)), Driver(2, Point(10, 0))]
        >>> requests = [Request(1, Point(2, 0), ...), Request(2, Point(11, 0), ...)]
        >>> # All pairs with distances:
        >>> #   (2.0, D1, R1)
        >>> #   (11.0, D1, R2)
        >>> #   (8.0, D2, R1)
        >>> #   (1.0, D2, R2) ← sorted first
        >>> # Greedy selection:
        >>> #   Select (1.0, D2, R2) → assign D2, R2
        >>> #   Consider (2.0, D1, R1) → D1, R1 free → select
        >>> #   Consider (8.0, D2, R1) → D2 used → skip
        >>> #   Consider (11.0, D1, R2) → R2 used → skip
        >>> proposals = policy.assign(drivers, requests, time=0)
        >>> # proposals = [(driver2, request2), (driver1, request1)]
    
    Comparison with NearestNeighbour:
        GlobalGreedy typically finds better assignments because it:
        - Sees all distances before deciding
        - Avoids "greedy trap" where first pick blocks better later options
        - Prioritizes globally best distances over local best
    """

    def assign(
        self,
        drivers: List["Driver"],
        requests: List["Request"],
        time: int
    ) -> List[Tuple["Driver", "Request"]]:
        """
        Propose pairs using global greedy distance-based matching.
        
        Process:
        1. Create all possible (distance, driver, request) tuples
        2. Sort by distance ascending
        3. Greedily select pairs, avoiding duplicate drivers/requests
        4. Return selected pairs in distance order
        
        Args:
            drivers: All drivers (filtered for idle internally)
            requests: All requests (filtered for waiting internally)
            time: Current simulation time
            
        Returns:
            List of (driver, request) pairs sorted by distance, or empty list
            
        Example:
            >>> policy = GlobalGreedy()
            >>> proposals = policy.assign(drivers, requests, time=100)
            >>> # [(driver_close, request_close), (driver_far, request_far)]
            
        Performance:
            - Complexity: O(n*m log(n*m)) where n=drivers, m=requests
            - Space: O(n*m) for storing all pairs
            - Practical: acceptable for fleets up to ~1000 drivers
        """
        # Filter idle drivers and waiting requests
        idle = [d for d in drivers if getattr(d, "status", None) == d.IDLE]
        waiting = [r for r in requests if getattr(r, "status", None) == r.WAITING]

        # List to hold all possible (distance, driver, request) tuples
        all_pairs: List[Tuple[float, "Driver", "Request"]] = []
        for d in idle:
            for r in waiting:
                # Compute Euclidean distance from driver to pickup
                dist = d.position.distance_to(r.pickup)
                all_pairs.append((dist, d, r))

        # Sort pairs by distance (ascending order - closest first)
        all_pairs.sort(key=lambda x: x[0])

        # Keep track of already assigned drivers and requests (by ID)
        assigned_drivers = set()
        assigned_requests = set()
        result: List[Tuple["Driver", "Request"]] = []

        # Greedily pick the shortest pairs, avoiding reuse of driver/request
        for dist, d, r in all_pairs:
            if d.id in assigned_drivers or r.id in assigned_requests:
                continue  # Skip if driver or request already assigned
            result.append((d, r))
            assigned_drivers.add(d.id)
            assigned_requests.add(r.id)

        return result
