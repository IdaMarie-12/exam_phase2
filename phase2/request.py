from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .point import Point


# Request status constants
WAITING = "WAITING"      # Not yet assigned
ASSIGNED = "ASSIGNED"    # Assigned to a driver
PICKED = "PICKED"        # Picked up by driver
DELIVERED = "DELIVERED"  # Delivered to customer
EXPIRED = "EXPIRED"      # Expired (not picked up in time)



@dataclass
class Request:
    """Delivery request and its lifecycle state.
    Tracks pickup/dropoff, creation time, assigned driver, status, and wait time.
    Status transitions: WAITING → ASSIGNED → PICKED → DELIVERED (or EXPIRED).
    """

    id: int
    pickup: Point
    dropoff: Point
    creation_time: int
    status: str = WAITING
    assigned_driver_id: Optional[int] = None
    wait_time: int = 0

    def is_active(self) -> bool:
        """Return True if request is in progress (WAITING, ASSIGNED, PICKED)."""
        return self.status in (WAITING, ASSIGNED, PICKED)

    def mark_assigned(self, driver_id: int) -> None:
        """Set ASSIGNED and record driver id. Only allowed from WAITING/ASSIGNED."""
        if self.status not in (WAITING, ASSIGNED):
            raise ValueError(f"Cannot assign request in status {self.status}")
        self.status = ASSIGNED
        self.assigned_driver_id = int(driver_id)

    def mark_picked(self, time: int) -> None:
        """Set PICKED and update wait_time. Only allowed from ASSIGNED/PICKED."""
        if self.status not in (ASSIGNED, PICKED):
            raise ValueError(f"Cannot pick request in status {self.status}")
        self.status = PICKED
        self.wait_time = max(0, int(time - self.creation_time))

    def mark_delivered(self, time: int) -> None:
        """Set DELIVERED and update total time in system. Only allowed from PICKED/DELIVERED."""
        if self.status not in (PICKED, DELIVERED):
            raise ValueError(f"Cannot deliver request in status {self.status}")
        self.status = DELIVERED
        self.wait_time = max(0, int(time - self.creation_time))

    def mark_expired(self, time: int) -> None:
        """Set EXPIRED if timing out. Not allowed if already delivered/expired."""
        if self.status in (DELIVERED, EXPIRED):
            raise ValueError(f"Cannot expire request in status {self.status}")
        self.status = EXPIRED
        self.wait_time = max(0, int(time - self.creation_time))

    def update_wait(self, current_time: int) -> None:
        """Update wait_time if WAITING or ASSIGNED."""
        if self.status in (WAITING, ASSIGNED):
            self.wait_time = max(0, int(current_time - self.creation_time))

    def __repr__(self) -> str:
        """One-line debug string (id/status/wait/pickup)."""
        return f"Request(id={self.id}, status={self.status}, wait={self.wait_time}, pickup={self.pickup})"
