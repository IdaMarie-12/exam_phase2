from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from .point import Point
from .request import Request
from .helpers_2.core_helpers import is_at_target, move_towards, calculate_points, record_assignment_start, record_completion, finalize_trip

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
    """
    Driver agent that moves, accepts offers, earns rewards, and evolves through mutation.
    
    A Driver is an active agent in the delivery simulation. It:
    - Moves towards assigned pickup/dropoff locations
    - Accepts or rejects delivery offers based on its behaviour
    - Earns money (fare) and points (for mutation) from completed trips
    - Tracks history of completed deliveries
    - Can mutate its behaviour based on performance (points)
    
    Attributes:
        id: Unique driver identifier
        position: Current location (Point object)
        behaviour: Decision-making strategy (DriverBehaviour policy, can be None)
        speed: Movement speed (units per time step), typically 0.8-1.6
        status: Current state (IDLE, TO_PICKUP, or TO_DROPOFF)
        current_request: Request being handled (None if idle)
        history: List of completed trip records {time, fare, wait, points, request_id, start_time}
        idle_since: Time when driver became IDLE (for tracking idle duration)
        earnings: Total money earned from all completed trips (fare is distance)
        points: Total points earned (for mutation/evolution)
        
    Lifecycle:
        1. Driver starts IDLE (no request)
        2. Assign request → status = TO_PICKUP
        3. Arrive at pickup → complete_pickup() → status = TO_DROPOFF
        4. Arrive at dropoff → complete_dropoff() → status = IDLE
        5. History is updated, earnings/points accumulated
        
    Example:
        >>> driver = Driver(id=1, position=Point(0, 0), speed=1.0)
        >>> request = Request(id=1, pickup=Point(5, 0), dropoff=Point(10, 0), creation_time=0)
        >>> driver.assign_request(request, time=0)
        >>> driver.step(dt=5.0)  # Move 5 units towards pickup
        >>> driver.complete_pickup(time=5)
        >>> driver.step(dt=5.0)  # Move 5 units towards dropoff
        >>> driver.complete_dropoff(time=10)  # Trip complete, earnings += 10
    """

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
        """
        Check if driver is currently idle (not working on any delivery).
        
        Returns True only when:
        - status is IDLE (not moving to pickup/dropoff)
        - current_request is None (no request assigned)
        
        Returns:
            bool: True if idle, False if busy with a delivery
            
        Example:
            >>> driver.is_idle()
            True
            >>> driver.assign_request(request, time=0)
            >>> driver.is_idle()
            False
        """
        return self.status == "IDLE" and self.current_request is None

    # Core lifecycle methods
    def assign_request(self, request: Request, current_time: int) -> None:
        """
        Assign a new request (ride) to this driver.
        
        Transitions driver from IDLE state to TO_PICKUP, setting up the delivery lifecycle.
        Records request assignment in history for tracking and analysis.
        
        Args:
            request (Request): The request to assign to this driver
            current_time (int): Current simulation time for tracking assignment moment
            
        State Transition:
            IDLE → TO_PICKUP (moving to customer pickup location)
            
        Effects:
            - Sets current_request to the provided request
            - Changes status to TO_PICKUP
            - Clears idle_since (driver is no longer idle)
            - Records assignment in history with request_id and start_time
            - Request transitions from WAITING to ASSIGNED
            
        Example:
            >>> driver.status
            'IDLE'
            >>> driver.idle_since
            500
            >>> driver.assign_request(customer_request, current_time=600)
            >>> driver.status
            'TO_PICKUP'
            >>> driver.idle_since is None
            True
        """
        self.current_request = request
        self.status = "TO_PICKUP"
        request.mark_assigned(self.id)
        self.idle_since = None

        # Record when this trip started
        record_assignment_start(self.history, request.id, current_time)

    def target_point(self) -> Optional[Point]:
        """
        Get the current target destination point for the driver.
        
        Returns the appropriate destination based on current delivery state:
        - TO_PICKUP: Returns customer pickup location
        - TO_DROPOFF: Returns customer dropoff location
        - IDLE: Returns None (no destination)
        
        Returns:
            Optional[Point]: The target location, or None if driver is idle
            
        Example:
            >>> driver.status
            'IDLE'
            >>> driver.target_point() is None
            True
            >>> driver.assign_request(request, current_time=0)
            >>> driver.target_point() == request.pickup
            True
        """

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
        """
        Mark pickup complete and transition to dropoff state.
        
        Called when driver reaches the customer's pickup location.
        Transitions driver from TO_PICKUP to TO_DROPOFF state.
        
        Args:
            time (int): Current simulation time when pickup occurs
            
        State Transition:
            TO_PICKUP → TO_DROPOFF (now moving to delivery location)
            
        Effects:
            - Marks current request as PICKED (customer is now in vehicle)
            - Changes driver status to TO_DROPOFF
            - Driver begins moving towards dropoff location
            
        Example:
            >>> driver.status
            'TO_PICKUP'
            >>> driver.current_request.status
            'ASSIGNED'
            >>> driver.complete_pickup(time=150)
            >>> driver.status
            'TO_DROPOFF'
            >>> driver.current_request.status
            'PICKED'
        """

        if not self.current_request:
            return

        self.current_request.mark_picked(time)
        self.status = "TO_DROPOFF"

    def complete_dropoff(self, time: int) -> None:
        """
        Mark dropoff complete and finalize trip.
        
        Updates Request status to DELIVERED, records trip to history,
        updates driver earnings and points using mutation formula,
        and resets driver to IDLE state.
        
        Formula for points: points = max(0, fare - 0.1 * wait_time)
        This incentivizes fast delivery and penalizes long waits.
        """
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

