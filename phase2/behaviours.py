from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .offer import Offer
    from .driver import Driver


class DriverBehaviour(ABC):
    """
    Abstract base class that defines the interface for driver decision strategies.
    
    A DriverBehaviour encapsulates how a driver accepts or rejects delivery offers.
    Different behaviours represent different driver archetypes and decision-making patterns:
    - Greedy drivers accept based on distance
    - Earnings-focused drivers maximize reward-per-time
    - Lazy drivers only work when rested and job is nearby
    
    Subclasses must implement the decide() method to return True (accept) or False (reject).
    
    The purpose of using an abstract base class:
        - Enforce a common interface (all behaviours MUST define decide())
        - Allow polymorphism (different behaviours can be swapped interchangeably)
        - Enable consistent integration with mutation and evolution systems
        
    Example usage:
        >>> behaviour = GreedyDistanceBehaviour(max_distance=10.0)
        >>> offer = Offer(driver, request, travel_time=2.0, reward=5.0)
        >>> if behaviour.decide(driver, offer, time=100):
        ...     driver.assign_request(offer.request, time=100)
    """

    @abstractmethod
    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """
        Decide whether the driver should accept the given offer.
        
        Called by the simulation engine during the offer collection phase.
        Each behaviour implements its own decision logic based on offer attributes
        and driver state.
        
        Args:
            driver: The driver making the decision
            offer: The delivery offer being considered
            time: Current simulation time (for time-dependent decisions)
            
        Returns:
            bool: True to accept the offer, False to reject it
            
        Note:
            This method should NOT have side effects. It only returns a decision.
            The engine handles actual assignment if accepted.
        """
        raise NotImplementedError("Subclasses must implement decide()")


class GreedyDistanceBehaviour(DriverBehaviour):
    """
    Distance-based behaviour: Accept only nearby pickup locations.
    
    This behaviour represents a pragmatic driver who:
    - Values convenience and short travel distances
    - Avoids long pickups that waste time
    - Makes decisions based purely on geography
    
    Use case: Drivers who prefer quick jobs with minimal wait at pickup.
    
    Attributes:
        max_distance: Maximum acceptable distance from current position to pickup
        
    Example:
        >>> behaviour = GreedyDistanceBehaviour(max_distance=5.0)
        >>> # Driver at (0, 0), pickup at (3, 0) → distance 3.0 → ACCEPT
        >>> # Driver at (0, 0), pickup at (8, 0) → distance 8.0 → REJECT
    """

    def __init__(self, max_distance: float):
        """
        Initialize greedy distance behaviour.
        
        Args:
            max_distance: Maximum acceptable pickup distance (units)
            
        Raises:
            ValueError: If max_distance <= 0
        """
        if max_distance <= 0:
            raise ValueError(f"max_distance must be positive, got {max_distance}")
        self.max_distance = max_distance

    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """
        Accept if pickup distance is within max_distance threshold.
        
        Decision rule: distance_to_pickup <= max_distance
        
        Args:
            driver: Driver evaluating the offer
            offer: Delivery offer with request information
            time: Current simulation time (unused for this behaviour)
            
        Returns:
            bool: True if pickup is close enough, False otherwise
            
        Example:
            >>> driver.position = Point(0, 0)
            >>> offer.request.pickup = Point(4, 0)
            >>> behaviour = GreedyDistanceBehaviour(max_distance=5.0)
            >>> behaviour.decide(driver, offer, time=0)
            True
            >>> 
            >>> offer.request.pickup = Point(6, 0)
            >>> behaviour.decide(driver, offer, time=0)
            False
        """
        dist = driver.position.distance_to(offer.request.pickup)
        return dist <= self.max_distance


class EarningsMaxBehaviour(DriverBehaviour):
    """
    Earnings-focused behaviour: Maximize reward per unit time.
    
    This behaviour represents an efficiency-focused driver who:
    - Prioritizes earnings over distance or idle time
    - Calculates reward-to-time ratio for each offer
    - Rejects low-efficiency jobs regardless of other factors
    
    Use case: Drivers who want to maximize hourly earnings by choosing high-reward short trips.
    
    The decision is based on: reward / travel_time >= threshold
    
    Attributes:
        threshold: Minimum acceptable reward-per-time ratio
        
    Example:
        >>> behaviour = EarningsMaxBehaviour(min_reward_per_time=0.5)
        >>> # Offer: reward=10.0, travel_time=15.0 → ratio=0.67 → ACCEPT
        >>> # Offer: reward=2.0, travel_time=10.0 → ratio=0.20 → REJECT
    """

    def __init__(self, min_reward_per_time: float):
        """
        Initialize earnings maximization behaviour.
        
        Args:
            min_reward_per_time: Minimum acceptable reward-per-time ratio
            
        Raises:
            ValueError: If min_reward_per_time < 0
        """
        if min_reward_per_time < 0:
            raise ValueError(f"min_reward_per_time must be non-negative, got {min_reward_per_time}")
        self.threshold = min_reward_per_time

    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """
        Accept if reward-per-time ratio meets or exceeds threshold.
        
        Decision rule: (reward / travel_time) >= threshold
        
        Args:
            driver: Driver evaluating the offer (not used for this behaviour)
            offer: Delivery offer with reward and travel time
            time: Current simulation time (unused for this behaviour)
            
        Returns:
            bool: True if earnings efficiency is acceptable, False otherwise
            
        Raises:
            Implicitly handles zero travel_time by returning False
            
        Example:
            >>> behaviour = EarningsMaxBehaviour(min_reward_per_time=0.5)
            >>> offer1 = Offer(..., estimated_reward=10.0, estimated_travel_time=15.0)
            >>> behaviour.decide(driver, offer1, time=0)  # 10/15 = 0.67 >= 0.5
            True
            >>> offer2 = Offer(..., estimated_reward=2.0, estimated_travel_time=10.0)
            >>> behaviour.decide(driver, offer2, time=0)  # 2/10 = 0.20 < 0.5
            False
        """
        # Prevent division by zero
        if offer.estimated_travel_time <= 0:
            return False

        # Check if earnings efficiency meets threshold
        return (offer.estimated_reward / offer.estimated_travel_time) >= self.threshold


class LazyBehaviour(DriverBehaviour):
    """
    Lazy behaviour: Accept only after resting AND close proximity.
    
    This behaviour represents a selective driver who:
    - Requires sufficient idle/rest time before accepting new work
    - Only accepts jobs with nearby pickups (< 5 units)
    - Combines rest requirement with distance preference
    - Models drivers who value balance and avoid exhaustion
    
    Use case: Drivers who want breaks and prefer convenient jobs.
    
    Attributes:
        idle_ticks_needed: Minimum idle time before accepting new work
        
    Example:
        >>> behaviour = LazyBehaviour(idle_ticks_needed=10)
        >>> # Driver idle for 15 ticks, pickup at (3, 0) from (0, 0) → ACCEPT
        >>> # Driver idle for 5 ticks, pickup at (3, 0) → REJECT (needs rest)
        >>> # Driver idle for 15 ticks, pickup at (8, 0) → REJECT (too far)
    """

    def __init__(self, idle_ticks_needed: int):
        """
        Initialize lazy behaviour.
        
        Args:
            idle_ticks_needed: Minimum idle time in simulation ticks before accepting work
            
        Raises:
            ValueError: If idle_ticks_needed < 0
        """
        if idle_ticks_needed < 0:
            raise ValueError(f"idle_ticks_needed must be non-negative, got {idle_ticks_needed}")
        self.idle_ticks_needed = idle_ticks_needed

    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """
        Accept only if driver is well-rested AND pickup is nearby.
        
        Decision rule: 
            1. Driver must be IDLE (not working)
            2. Driver must have idle_since tracking
            3. Idle duration must >= idle_ticks_needed
            4. Pickup must be < 5.0 units away
            
        All four conditions must be satisfied to accept.
        
        Args:
            driver: Driver evaluating the offer
            offer: Delivery offer with request information
            time: Current simulation time (for idle duration calculation)
            
        Returns:
            bool: True only if all conditions satisfied, False otherwise
            
        Example:
            >>> behaviour = LazyBehaviour(idle_ticks_needed=10)
            >>> driver.status = "IDLE"
            >>> driver.idle_since = 85
            >>> driver.position = Point(0, 0)
            >>> offer.request.pickup = Point(3, 0)
            >>> 
            >>> # At time=95: idle for 10 ticks, pickup 3 units away
            >>> behaviour.decide(driver, offer, time=95)
            True
            >>> 
            >>> # At time=88: idle for only 3 ticks (need 10)
            >>> behaviour.decide(driver, offer, time=88)
            False
            >>> 
            >>> # At time=95 but pickup 8 units away
            >>> offer.request.pickup = Point(8, 0)
            >>> behaviour.decide(driver, offer, time=95)
            False
        """
        # Check if driver is currently idle
        if driver.status != "IDLE":
            return False

        # Retrieve idle start time
        idle_since = getattr(driver, "idle_since", None)
        if idle_since is None:
            return False

        # Check if driver has been idle long enough
        idle_duration = time - idle_since
        if idle_duration < self.idle_ticks_needed:
            return False

        # Check if pickup is close enough (hardcoded to 5.0 units for laziness)
        pickup_distance = driver.position.distance_to(offer.request.pickup)
        return pickup_distance < 5.0
