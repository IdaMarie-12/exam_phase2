from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
import math

#-----------------------------------
# Point
#-----------------------------------
@ dataclass
class Point:
    """ A simple 2D point on the map """

    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        """ Return the Euclidean distance to another point. """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.hypot(dx, dy)

#-----------------------------------
# Request
#-----------------------------------
@ dataclass
class Request:
    """ A single food-delivery request with pickup and dropoff points."""
    id: int
    pickup: Point
    dropoff: Point
    creation_time: int
    status: str = request_waiting
    assigned_driver_id: Optional[int] = None

    def is_active(self) -> bool:
        """ Returns True if the request is not delivered or expired. """
        return NotImplementedError

    def update_wait(self, current_time: int) -> None:
        """
        Update wait_time based on current_time.
        Convention: wait_time = time until pickup (not including travel)
        """
        return NotImplementedError

    def mark_assigned(self, driver_id: int) -> None:
        """ Mark request as assigned to a driver. """
        return NotImplementedError

    def mark_picked(self, t: int) -> None:
        """ Mark request as picked up at time t. """
        return NotImplementedError

    def mark_delivered(self, t: int) -> None:
        """ Mark request as delivered at time t. """
        return NotImplementedError

    def mark_expired(self, t: int) -> None:
        """ Mark request as expired at time t. """
        return NotImplementedError

#-----------------------------------
# Driver
#-----------------------------------
@dataclass
class Driver:
    """ A driver agent that can move and accept or reject offers. """
    id: int
    position: Point
    speed: float
    behavior: "DriverBehavior"     # Will be set by the backend when constructing drivers
    status: str = driver_idle
    current_request: Optional[Request] = None
    history: List[dict] = field(default_factory = list)
    total_earnings: float = 0.0    # Optional
    last_action_time: int = 0      # Optional

    def target_point(self) -> Optional[Point]:
        """ Return the current movement target, if any """
        return NotImplementedError

    def assign_request(self, request: Request, current_time: int) -> None:
        """ Assign request to driver. """
        return NotImplementedError

    def step(self, dt: float = 1.0) -> None:
        """ Move the driver towards its target according to its speed and dt. """
        return NotImplementedError

    def complete_pickup(self, time: int) -> None:
        """ Handle logic when driver reaches the pickup. """
        return NotImplementedError

    def complete_dropoff(self, time: int, earning: float) -> None:
        """ Handle logic when driver reaches the dropoff. """
        return NotImplementedError

