from __future__ import annotations
from typing import Optional
from phase2.point import Point # skal rettes til rigtige navn når vi har point filen

class Request:
    # Status constants for a request
    WAITING = "WAITING"         # Request has appeared but not yet assigned
    ASSIGNED = "ASSIGNED"       # Request is assigned to a driver
    PICKED = "PICKED"           # Driver has picked up the order
    DELIVERED = "DELIVERED"     # Order has been delivered
    EXPIRED = "EXPIRED"         # Order expired (not picked up in time)

    # Constructor: initialize a request
    def __init__(self, id: int, pickup: Point, dropoff: Point, creation_time: int):
        self.id = int(id)           # Unique identifier for the request
        self.pickup = pickup        # Pickup location (Point object)
        self.dropoff = dropoff      # Dropoff location (Point object)
        self.creation_time = int(creation_time)   # Time when the request was created
        self.status = Request.WAITING  # Initial status is WAITING
        self.assigned_driver_id: Optional[int] = None  # Driver assigned (None if not yet assigned)
        self.wait_time: int = 0     # Time the request has waited until pickup

    # Check if request is still active
    def is_active(self) -> bool:
        """
        Returns True if the is still in the system and not completed or expired.
        Active statuses: WAITING, ASSIGNED, PICKED
        """
        return self.status in (Request.WAITING, Request.ASSIGNED, Request.PICKED)

    # Mark the request as assigned to a driver
    def mark_assigned(self, driver_id: int) -> None:
        """
        Updated the request to ASSIGNED and stores the driver's ID.
        """
        self.status = Request.ASSIGNED
        self.assigned_driver_id = int(driver_id)

    # Mark the request as picked up by the driver
    def mark_picked(self, t: int) -> None:
        """
        Updates the request status to PICKED and calculates the wait_time.
        wait_time = time from creation to pickup.
        """
        self.status = Request.PICKED
        self.wait_time = int(t - self.creation_time)

    # Mark the request as delivered
    def mark_delivered(self, t: int) -> None:
        """
        Updates the request status to DELIVERED
        """
        self.status = Request.DELIVERED

    # Mark the request as expired
    def mark_expired(self, t: int) -> None:
        """
        Updated the request status to EXPIRED.
        This is called when the wait time exceeds a timeout.
        """
        self.status = Request.EXPIRED

    # Update wait time for active requests
    def update_wait(self, current_time: int) -> None:
        """
        Updates the wait_time for requests that are still waiting or assigned.
        PICKED or DELIVERED requests are not updated here.
        """
        if self.status in (Request.WAITING, Request.ASSIGNED):
            self.wait_time = int(current_time - self.creation_time)

    # String representation for debugging
    def __repr__(self):
        """
        Returns a readable string representation of the request.
        Shows id, current status, wait_time, and pickup location.
        """
        return f"Request(id={self.id}, status={self.status}, wait={self.wait_time}, pickup={self.pickup})"
