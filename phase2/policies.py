from __future__ import annotations
from typing import List, Tuple

class DispatchPolicy:
    """
    Abstract base class for dispatch policies.
    Any concrete dispatch policy should inherit from this class and implement
    the assign() method, which determines which drivers are offered which requests.
    """
    def assign(self,
                drivers: list[Driver],
                requests: list[Request],
                time: int
            ) -> list[tuple[Driver, Request]]:
            """Return proposed (driver, request) pairs for this tick."""
            raise NotImplementedError

class NearestNeighbour(DispatchPolicy):
    """
    NearestNeighbour dispatch policy:
    - Match the closest idle driver to the closest waiting request.
    - Repeat until no idle drivers or waiting requests remain.
    - Greedy, iterative approach.
    """
    def assign(
            self,
            drivers: List[Driver],
            requests: List[Request],
            time: int
        ) -> List[Tuple[Driver, Request]]:
            # Filter only idle drivers and waiting requests
            idle = [d for d in drivers if getattr(d, "status", None) == d.IDLE]
            waiting = [r for r in requests if getattr(r, "status", None) == r.WAITING]

            pairs: List[Tuple[Driver, Request]] = []

            # Greedy iterative nearest matching
            while idle and waiting:
                best_dist = float("inf") # Initialize best distance as infinity
                best_pair = None    # Initialize best pair as None

                # Find the closest driver-request pair
                for d in idle:
                    for r in waiting:
                        # read-only distance check
                        dist = d.position.distance_to(r.pickup)  # Compute Euclidean distance
                        if dist < best_dist:
                            best_dist = dist
                            best_pair = (d, r)
                if best_pair is None:
                    break  # No valid pair found, exit loop
                # Add best pair to result and remove them from further consideration
                d_sel, r_sel = best_pair
                pairs.append((d_sel, r_sel))
                # remove selected driver and request from consideration
                idle.remove(d_sel)
                waiting.remove(r_sel)

            return pairs

class GlobalGreedy(DispatchPolicy):
    """
    GlobalGreedy dispatch policy:

    - Consider all idle drivers and all waiting requests.
    - Compute distances for all possible driver-request pairs.
    - Sort all pairs by distance (shortest first).
    - Greedily assign pairs while avoiding assigning the same driver or request twice.
    """
    def assign(
        self,
        drivers: List[Driver],
        requests: List[Request],
        time: int
    ) -> List[Tuple[Driver, Request]]:
        # Filter idle drivers and waiting requests
        idle = [d for d in drivers if getattr(d, "status", None) == d.IDLE]
        waiting = [r for r in requests if getattr(r, "status", None) == r.WAITING]

        # List to hold all possible (distance, driver, request) tuples
        all_pairs: List[Tuple[float, Driver, Request]] = []
        for d in idle:
            for r in waiting:
                dist = d.position.distance_to(r.pickup)  # Compute Euclidean distance
                all_pairs.append((dist, d, r))

        # Sort pairs by distance (ascending order)
        all_pairs.sort(key=lambda x: x[0])

        # Keep track of already assigned drivers and requests
        assigned_drivers = set()
        assigned_requests = set()
        result: List[Tuple[Driver, Request]] = []

        # Greedily pick the shortest pairs, avoiding reuse
        for dist, d, r in all_pairs:
            if d.id in assigned_drivers or r.id in assigned_requests:
                continue  # Skip if driver or request already assigned
            result.append((d, r))
            assigned_drivers.add(d.id)
            assigned_requests.add(r.id)

        return result
