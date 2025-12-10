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
    """
    Request (food delivery order) that moves through a lifecycle.
    
    A Request represents a customer food delivery order in the simulation. It:
    - Appears at a specific time with pickup and dropoff locations
    - Gets assigned to an available driver
    - Gets picked up, transported, and delivered
    - Can expire if not picked up in time
    - Tracks wait time for performance metrics and driver rewards
    
    Attributes:
        id: Unique request identifier
        pickup: Pickup location (Point object)
        dropoff: Delivery location (Point object)
        creation_time: Simulation time when request appeared
        status: Current state (WAITING, ASSIGNED, PICKED, DELIVERED, EXPIRED)
        assigned_driver_id: ID of assigned driver (None if unassigned)
        wait_time: Time elapsed in system (updated as request waits)
        
    Lifecycle:
        1. Request appears → status = WAITING (available for assignment)
        2. Assign to driver → status = ASSIGNED (driver accepted)
        3. Driver picks up → status = PICKED (in vehicle)
        4. Driver delivers → status = DELIVERED (trip complete)
        
        Alternative endpoint:
        - Timeout exceeded → status = EXPIRED (no driver accepted)
        
    Example:
        >>> req = Request(id=1, pickup=Point(0, 0), dropoff=Point(10, 0), creation_time=0)
        >>> req.status
        'WAITING'
        >>> req.is_active()
        True
        >>> req.mark_assigned(driver_id=1)
        >>> req.status
        'ASSIGNED'
        >>> req.assigned_driver_id
        1
        >>> req.mark_picked(time=5)
        >>> req.wait_time
        5
        >>> req.mark_delivered(time=10)
        >>> req.status
        'DELIVERED'
        >>> req.is_active()
        False
    """

    id: int
    pickup: Point
    dropoff: Point
    creation_time: int
    status: str = WAITING
    assigned_driver_id: Optional[int] = None
    wait_time: int = 0

    def is_active(self) -> bool:
        """
        Check if request is still active in the system.
        
        Active requests are those not yet completed or expired.
        Active statuses: WAITING, ASSIGNED, PICKED
        Inactive statuses: DELIVERED, EXPIRED
        
        Returns:
            bool: True if request is still in delivery process, False if completed/expired
            
        Example:
            >>> req = Request(1, Point(0,0), Point(10,0), 0)
            >>> req.is_active()
            True
            >>> req.mark_delivered(5)
            >>> req.is_active()
            False
        """
        return self.status in (WAITING, ASSIGNED, PICKED)

    def mark_assigned(self, driver_id: int) -> None:
        """
        Assign request to a driver and transition to ASSIGNED state.
        
        Called by Driver.assign_request() when driver accepts the delivery.
        Records which driver is now responsible for this delivery.
        
        Args:
            driver_id: ID of the driver accepting this request
            
        State Transition:
            WAITING → ASSIGNED
            
        Effects:
            - Sets status to ASSIGNED
            - Records assigned_driver_id for tracking
            
        Example:
            >>> req = Request(1, Point(0,0), Point(10,0), 0)
            >>> req.status
            'WAITING'
            >>> req.assigned_driver_id is None
            True
            >>> req.mark_assigned(driver_id=5)
            >>> req.status
            'ASSIGNED'
            >>> req.assigned_driver_id
            5
        """
        self.status = ASSIGNED
        self.assigned_driver_id = int(driver_id)

    def mark_picked(self, time: int) -> None:
        """
        Mark request as picked up and calculate wait time.
        
        Called by Driver.complete_pickup() when driver arrives at pickup location
        and customer enters vehicle.
        
        Calculates wait_time as: time - creation_time
        This represents how long customer waited for pickup.
        
        Args:
            time: Simulation time when pickup occurs
            
        State Transition:
            ASSIGNED → PICKED
            
        Effects:
            - Sets status to PICKED (customer now in vehicle)
            - Calculates wait_time = time - creation_time
            - This wait_time is used in driver reward formula
            
        Example:
            >>> req = Request(1, Point(0,0), Point(10,0), creation_time=50)
            >>> req.mark_assigned(1)
            >>> req.mark_picked(time=65)
            >>> req.status
            'PICKED'
            >>> req.wait_time
            15
        """
        self.status = PICKED
        self.wait_time = int(time - self.creation_time)

    def mark_delivered(self, time: int) -> None:
        """
        Mark request as successfully delivered.
        
        Called by Driver.complete_dropoff() when driver arrives at dropoff location
        and completes the delivery. This is the successful completion state.
        
        Args:
            time: Simulation time when delivery completes (not used, but kept for API consistency)
            
        State Transition:
            PICKED → DELIVERED
            
        Effects:
            - Sets status to DELIVERED (order successfully delivered)
            - Trip is now complete
            - Driver gets credited with earnings and points
            
        Example:
            >>> req = Request(1, Point(0,0), Point(10,0), creation_time=50)
            >>> req.mark_assigned(1)
            >>> req.mark_picked(time=65)
            >>> req.mark_delivered(time=75)
            >>> req.status
            'DELIVERED'
            >>> req.is_active()
            False
        """
        self.status = DELIVERED

    def mark_expired(self, time: int) -> None:
        """
        Mark request as expired due to timeout.
        
        Called by engine when wait time exceeds maximum timeout threshold.
        This indicates no driver accepted the request in time.
        
        Args:
            time: Simulation time when expiration occurs (for record keeping)
            
        State Transition:
            WAITING or ASSIGNED → EXPIRED
            
        Effects:
            - Sets status to EXPIRED (no driver delivered this order)
            - Request is removed from available pool
            - Not counted as successful delivery
            
        Example:
            >>> req = Request(1, Point(0,0), Point(10,0), creation_time=0)
            >>> req.is_active()
            True
            >>> req.mark_expired(time=300)
            >>> req.status
            'EXPIRED'
            >>> req.is_active()
            False
        """
        self.status = EXPIRED

    def update_wait(self, current_time: int) -> None:
        """
        Update wait_time counter for requests still waiting/assigned.
        
        Called each simulation step by the engine to track how long
        a request has been waiting for assignment or pickup.
        
        Only updates for WAITING and ASSIGNED statuses.
        PICKED, DELIVERED, EXPIRED requests are not updated.
        
        Args:
            current_time: Current simulation time
            
        Effects:
            - Updates wait_time = current_time - creation_time
            - Reflects cumulative wait duration
            - Used for timeout checks and reward calculations
            
        Example:
            >>> req = Request(1, Point(0,0), Point(10,0), creation_time=10)
            >>> req.update_wait(current_time=25)
            >>> req.wait_time
            15
            >>> req.update_wait(current_time=40)
            >>> req.wait_time
            30
        """
        if self.status in (WAITING, ASSIGNED):
            self.wait_time = int(current_time - self.creation_time)

    def __repr__(self) -> str:
        """
        Return readable string representation for debugging.
        
        Shows id, status, current wait time, and pickup location.
        
        Returns:
            str: Formatted representation
            
        Example:
            >>> req = Request(1, Point(5.0, 10.0), Point(8.0, 12.0), 0)
            >>> repr(req)
            'Request(id=1, status=WAITING, wait=0, pickup=Point(5.0, 10.0))'
        """
        return f"Request(id={self.id}, status={self.status}, wait={self.wait_time}, pickup={self.pickup})"
