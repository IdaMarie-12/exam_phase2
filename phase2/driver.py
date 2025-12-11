from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from .point import Point
from .helpers_2.core_helpers import is_at_target, move_towards, calculate_points, record_assignment_start, record_completion, finalize_trip

if TYPE_CHECKING:
    from phase2.behaviours import DriverBehaviour
    from phase2.request import Request

# Status constants for drivers
IDLE = "IDLE"
TO_PICKUP = "TO_PICKUP"
TO_DROPOFF = "TO_DROPOFF"

@dataclass
class Driver:
    """Agent that transports requests from pickup to dropoff locations, earning rewards."""

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
        """Return True if driver is idle (not assigned to any request)."""
        return self.status == "IDLE" and self.current_request is None

    # Core lifecycle methods
    def assign_request(self, request: Request, current_time: int) -> None:
        """Assign a request to this driver and transition to TO_PICKUP state."""
        self.current_request = request
        self.status = "TO_PICKUP"
        request.mark_assigned(self.id)
        self.idle_since = None

        # Record when this trip started
        record_assignment_start(self.history, request.id, current_time)

    def target_point(self) -> Optional[Point]:
        """Return the current target destination based on driver status."""

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
        Uses epsilon-safe arrival detection and movement calculation.
        Prevents overshooting the target.
        """
        # Check if driver has a target point
        target = self.target_point()
        if target is None:
            return

        # Check if already at target (epsilon-safe)
        if is_at_target(self.position, target):
            return

        # Move towards target without overshooting
        distance = self.speed * dt
        self.position = move_towards(self.position, target, distance)

    def complete_pickup(self, time: int) -> None:
        """Mark pickup complete and transition to TO_DROPOFF state."""

        if not self.current_request:
            return

        self.current_request.mark_picked(time)
        self.status = "TO_DROPOFF"

    def complete_dropoff(self, time: int) -> None:
        """Mark dropoff complete, record trip, update earnings, and reset to IDLE state."""
        # Check if driver has any requests
        if not self.current_request:
            return

        req = self.current_request
        req.mark_delivered(time)

        # Calculate fare (straight-line distance) and compute points
        fare = req.pickup.distance_to(req.dropoff)
        wait = req.wait_time
        points = calculate_points(fare, wait)

        # Record completion with all trip metrics
        record_completion(self.history, req.id, req.creation_time, time, fare, wait, points)
        
        # Update aggregates and reset state
        self.earnings += fare
        self.points += points
        self.current_request = None
        self.status = "IDLE"
        self.idle_since = time