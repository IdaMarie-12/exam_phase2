from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from .point import Point
from .request import Request

if TYPE_CHECKING:
    from phase2.behaviours import DriverBehaviour

# --------------------------------------
# Driver
# --------------------------------------

# Global definition of driver status
IDLE = "IDLE"
DROPOFF = "DROPOFF"
TO_PICKUP = "TO_PICKUP"

@dataclass
class Driver:
    """ Driver agent that moves, accepts offers, earns rewards, and mutate. """

    # Attributes
    id: int
    position: Point
    behaviour: Optional["DriverBehaviour"] = None
    speed: float = 1.0
    status: str = IDLE
    current_request: Optional[Request] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    idle_since: Optional[int] = 0
    earnings: float = 0.0
    points: float = 0.0

    # Convenience helpers
    def is_idle(self) -> bool:
        """ Return True if driver is currently idle (no active request), false otherwise. """

        return self.status == "IDLE" and self.current_request is None

    # Core lifecycle methods
    def assign_request(self, request: Request, current_time: int) -> None:
        """ Assign a request to this dirver and start moving to pickup. """
        self.current_request = request
        self.status = "TO_PICKUP"
        request.mark_assigned(self.id)
        self.idle_since = None

        # Record when this trip started
        self.history.append({
            "request_id": request.id,
            "start_time": current_time,
        })

    def target_point(self) -> Optional[Point]:
        """ Return the current target point (pickup / dropoff) or None. """

        if self.current_request is None:
            return None
        if self.status == "TO_PICKUP":
            return self.current_request.pickup
        if self.status == "TO_DROPOFF":
            return self.current_request.dropoff
        return None

    def step(self, dt: float) -> None:
        """
        Move the driver towards its current target by at most speed * dt.
        Prevents overshooting the target.
        """

        # Check if driver has a target point
        target = self.target_point()
        if target is None:
            return

        # Find distance to target point
        dx = target.x - self.position.x
        dy = target.y - self.position.y
        dist = self.position.distance_to(target)

        # Check if driver is at target
        if dist <= 1e-9:
            return

        # Driver travel at most speed * dt
        travel = min(self.speed * dt, dist)
        frac = travel / dist
        self.position.x += dx * frac
        self.position.y += dy * frac

    def complete_pickup(self, time: int) -> None:
        """ Mark pickup complete and start moving to dropoff. """

        if not self.current_request:
            return

        self.current_request.mark_picked(time)
        self.status = "TO_DROPOFF"

    def complete_dropoff(self, time: int) -> None:
        """
        Mark dropoff complete and start moving to pickup.

        This method is expected to:
            - Update the Request status to "delivered" and its wait_time
            - Append a trip record to "history"
            - Update "earnings" and "points"
            - Reset the driver to "IDLE" and set "idle_since"
        """

        # Check if driver has any requests
        if not self.current_request:
            return

        req = self.current_request
        req.mark_delivered(time)

        # Fare is straight-line distance between pickup and dropoff
        fare = req.pickup.distance_to(req.dropoff)
        wait = req.wait_time

        # Points for mutation
        points = max(0.0, fare - 0.1 * wait)

        # Record this trip
        self.history.append({
            "time": time,
            "fare": fare,
            "wait": wait,
            "points": points,
            "request_id": req.id,
            "start_time": req.creation_time,
        })

        # Update aggregates
        self.earnings += fare
        self.points += points

        # Reset driver state
        self.current_request = None
        self.status = "IDLE"
        self.idle_since = time

