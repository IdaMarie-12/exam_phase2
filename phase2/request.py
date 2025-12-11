from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .point import Point

# Status constants for requests
WAITING = "WAITING"         # Request has appeared but not yet assigned
ASSIGNED = "ASSIGNED"       # Request is assigned to a driver
PICKED = "PICKED"           # Driver has picked up the order
DELIVERED = "DELIVERED"     # Order has been delivered
EXPIRED = "EXPIRED"         # Order expired (not picked up in time)


@dataclass
class Request:
    """Represents a single delivery request and its lifecycle.

    Tracks pickup/dropoff points, creation time, assigned driver, status, and
    accumulated wait time. Moves through WAITING → ASSIGNED → PICKED →
    DELIVERED, with EXPIRED as an alternative end state when timeouts hit.

    Attributes:
        id: Unique integer identifier.
        pickup: Pickup location as a ``Point``.
        dropoff: Drop-off location as a ``Point``.
        creation_time: Tick when the request appeared.
        status: One of WAITING, ASSIGNED, PICKED, DELIVERED, EXPIRED.
        assigned_driver_id: Driver id if assigned, else None.
        wait_time: Time spent in system (updated on pickup/delivery/expire or via update_wait).
    """

    id: int
    pickup: Point
    dropoff: Point
    creation_time: int
    status: str = WAITING
    assigned_driver_id: Optional[int] = None
    wait_time: int = 0

    def is_active(self) -> bool:
        """Return True while the request is in-progress.

        Active statuses: WAITING, ASSIGNED, PICKED.
        Inactive statuses: DELIVERED, EXPIRED.
        """
        return self.status in (WAITING, ASSIGNED, PICKED)

    def mark_assigned(self, driver_id: int) -> None:
        """Set ASSIGNED and record the driver id.

        Allowed from WAITING/ASSIGNED; raises if already picked/done/expired.
        """
        if self.status not in (WAITING, ASSIGNED):
            raise ValueError(f"Cannot assign request in status {self.status}")

        self.status = ASSIGNED
        self.assigned_driver_id = int(driver_id)

    def mark_picked(self, time: int) -> None:
        """Set PICKED and update wait_time since creation.

        Allowed from ASSIGNED/PICKED. wait_time becomes max(0, time - creation_time).
        """
        if self.status not in (ASSIGNED, PICKED):
            raise ValueError(f"Cannot pick request in status {self.status}")

        self.status = PICKED
        self.wait_time = max(0, int(time - self.creation_time))

    def mark_delivered(self, time: int) -> None:
        """Set DELIVERED and update total time in system.

        Allowed from PICKED/DELIVERED. wait_time becomes max(0, time - creation_time).
        """
        if self.status not in (PICKED, DELIVERED):
            raise ValueError(f"Cannot deliver request in status {self.status}")

        self.status = DELIVERED
        # Total time in system (appearance -> delivery)
        self.wait_time = max(0, int(time - self.creation_time))

    def mark_expired(self, time: int) -> None:
        """Set EXPIRED when timing out; blocked if already delivered/expired.

        wait_time becomes max(0, time - creation_time).
        """
        if self.status in (DELIVERED, EXPIRED):
            raise ValueError(f"Cannot expire request in status {self.status}")

        self.status = EXPIRED
        self.wait_time = max(0, int(time - self.creation_time))

    def update_wait(self, current_time: int) -> None:
        """Refresh wait_time while WAITING/ASSIGNED; ignored otherwise.

        wait_time becomes max(0, current_time - creation_time).
        """
        if self.status in (WAITING, ASSIGNED):
            self.wait_time = max(0, int(current_time - self.creation_time))

    def __repr__(self) -> str:
        """Readable one-liner for debugging (id/status/wait/pickup)."""
        return f"Request(id={self.id}, status={self.status}, wait={self.wait_time}, pickup={self.pickup})"
