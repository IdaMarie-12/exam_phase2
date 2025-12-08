from __future__ import annotations
from typing import List, Tuple

class DispatchPolicy:
    def assign(self,
                drivers: list[Driver],
                requests: list[Request],
                time: int
            ) -> list[tuple[Driver, Request]]:
            """Return proposed (driver, request) pairs for this tick."""
            raise NotImplementedError

class NearestNeighbour(DispatchPolicy):
    """
    Match the closest idle driver to the closest waiting request
    Repeat until no idle drivers or no waiting requests remain.
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
                best_dist = float("inf")
                best_pair = None
                for d in idle:
                    for r in waiting:
                        # read-only distance check
                        dist = d.position.distance_to(r.pickup)
                        if dist < best_dist:
                            best_dist = dist
                            best_pair = (d, r)
                if best_pair is None:
                    break
                d_sel, r_sel = best_pair
                pairs.append((d_sel, r_sel))
                # remove selected driver and request from consideration
                idle.remove(d_sel)
                waiting.remove(r_sel)
            
            return pairs

class GlobalGreedy(DispatchPolicy):
    """
     Build all (idle driver, waiting request) pairs, sort by distance,
    then greedily pick the shortest pairs while avoiding reuse of drivers/requests.
    """

    def assign(
        self,
        drivers: List[Driver],
        requests: List[Request],
        time: int
    ) -> List[Tuple[Driver, Request]]:
        idle = [d for d in drivers if getattr(d, "status", None) == d.IDLE]
        waiting = [r for r in requests if getattr(r, "status", None) == r.WAITING]

        all_pairs: List[Tuple[float, Driver, Request]] = []
        for d in idle:
            for r in waiting:
                dist = d.position.distance_to(r.pickup)
                all_pairs.append((dist, d, r))

        # sort by distance (ascending)
        all_pairs.sort(key=lambda x: x[0])

        assigned_drivers = set()
        assigned_requests = set()
        result: List[Tuple[Driver, Request]] = []

        for dist, d, r in all_pairs:
            if d.id in assigned_drivers or r.id in assigned_requests:
                continue
            result.append((d, r))
            assigned_drivers.add(d.id)
            assigned_requests.add(r.id)

        return result
