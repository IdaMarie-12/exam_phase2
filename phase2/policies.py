from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple
from .driver import IDLE
from .request import WAITING

if TYPE_CHECKING:
    from phase2.driver import Driver
    from phase2.request import Request


# ====================================================================
# Dispatch Policy Base Class
# ====================================================================

class DispatchPolicy:
    """Abstract base class for dispatch policies.
    Determines which idle drivers should be offered which waiting requests.
    """

    def assign(self,
                drivers: List["Driver"],
                requests: List["Request"],
                time: int
            ) -> List[Tuple["Driver", "Request"]]:
        raise NotImplementedError



# ====================================================================
# Nearest Neighbour Policy
# ====================================================================

class NearestNeighborPolicy(DispatchPolicy):
    """Iteratively finds closest idle driver-request pair, assigns it, and repeats."""
    def assign(
            self,
            drivers: List["Driver"],
            requests: List["Request"],
            time: int
        ) -> List[Tuple["Driver", "Request"]]:
        """Propose pairs using iterative greedy nearest-neighbor matching by distance."""
        # Filter only idle drivers and waiting requests
        idle = [d for d in drivers if d.status == IDLE]
        waiting = [r for r in requests if r.status == WAITING]

        pairs: List[Tuple["Driver", "Request"]] = []

        # Greedy iterative nearest matching by distance
        while idle and waiting:
            best_dist = float("inf") 
            best_pair = None        

            # Find the driver-request pair with shortest distance
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

class GlobalGreedyPolicy(DispatchPolicy):
    """Global greedy dispatch policy with distance-based optimization.
    Computes all driver-request distances, sorts by distance,
    then greedily selects closest pairs."""
    def assign(
        self,
        drivers: List["Driver"],
        requests: List["Request"],
        time: int
    ) -> List[Tuple["Driver", "Request"]]:
        """Propose pairs using global greedy distance-based matching."""
        # Filter idle drivers and waiting requests
        idle = [d for d in drivers if d.status == IDLE]
        waiting = [r for r in requests if r.status == WAITING]

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

        # Greedily pick the closest pairs, avoiding reuse of driver/request
        for dist, d, r in all_pairs:
            if d.id in assigned_drivers or r.id in assigned_requests:
                continue  # Skip if driver or request already assigned
            result.append((d, r))
            assigned_drivers.add(d.id)
            assigned_requests.add(r.id)

        return result



# ====================================================================
# Adaptive Hybrid Policy (Binary Selection by Driver-Request Ratio)
# ====================================================================

class AdaptiveHybridPolicy(DispatchPolicy):
    """Intelligent hybrid dispatch that adapts based on driver-request ratio.
    Strategy:
    - When requests > drivers: Use GlobalGreedy
    - When drivers >= requests: Use NearestNeighbor"""
    def assign(
        self,
        drivers: List["Driver"],
        requests: List["Request"],
        time: int
    ) -> List[Tuple["Driver", "Request"]]:
        """Assign drivers to requests with binary strategy based on load balance.
        Selects between GlobalGreedy (optimize scarce resources) and 
        NearestNeighbor (fast with abundant drivers) based on current ratio.
        """
        # Filter idle drivers and waiting requests
        idle = [d for d in drivers if d.status == IDLE]
        waiting = [r for r in requests if r.status == WAITING]

        if not idle or not waiting:
            return []

        # Strategy selection based on request-driver ratio
        if len(waiting) > len(idle):
            # More requests than drivers: Use GlobalGreedy for resource optimization
            return GlobalGreedyPolicy().assign(idle, waiting, time)
        else:
            # Drivers >= requests: Use NearestNeighbor for responsive speed
            return NearestNeighborPolicy().assign(idle, waiting, time)

