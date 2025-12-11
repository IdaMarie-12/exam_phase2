from abc import ABC, abstractmethod #is used for abstract base classes
from typing import TYPE_CHECKING #is used to avoid circular imports while maintaining type hints

if TYPE_CHECKING:
    from .offer import Offer
    from .driver import Driver


# ====================================================================
# BEHAVIOUR PARAMETERS and CONSTANTS

# LazyBehaviour: Maximum acceptable distance to pickup location
LAZY_MAX_PICKUP_DISTANCE = 5.0


class DriverBehaviour(ABC):
    """Abstract base class for driver decision strategies.
    
    Subclasses implement decide(driver, offer, time) to return True (accept) or False (reject).
    """

    @abstractmethod
    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """Decide whether driver accepts the offer. Returns True or False.
        
        Subclasses implement their own decision logic. Called during offer collection phase.
        """
        raise NotImplementedError("Subclasses must implement decide()")


class GreedyDistanceBehaviour(DriverBehaviour):
    """Accept offers with pickup distance <= max_distance threshold.
    
    Pragmatic drivers who value convenience and short travel distances.
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
        """Accept if pickup distance is within max_distance threshold.
        
        Raises TypeError if arguments have wrong types.
        """
        from .driver import Driver as DriverClass
        from .offer import Offer as OfferClass
        
        if not isinstance(driver, DriverClass):
            raise TypeError(f"decide() requires Driver, got {type(driver).__name__}")
        if not isinstance(offer, OfferClass):
            raise TypeError(f"decide() requires Offer, got {type(offer).__name__}")
        if not isinstance(time, int):
            raise TypeError(f"decide() requires int time, got {type(time).__name__}")
        
        dist = driver.position.distance_to(offer.request.pickup)
        return dist <= self.max_distance


class EarningsMaxBehaviour(DriverBehaviour):
    """Accept offers where reward/travel_time >= threshold.
    
    Efficiency-focused drivers who maximize hourly earnings regardless of distance.
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
        """Accept if reward/travel_time >= threshold. Returns False if travel_time <= 0.
        """
        from .driver import Driver as DriverClass
        from .offer import Offer as OfferClass
        
        if not isinstance(driver, DriverClass):
            raise TypeError(f"decide() requires Driver, got {type(driver).__name__}")
        if not isinstance(offer, OfferClass):
            raise TypeError(f"decide() requires Offer, got {type(offer).__name__}")
        if not isinstance(time, int):
            raise TypeError(f"decide() requires int time, got {type(time).__name__}")
        
        # Accept if reward per time unit meets threshold
        return offer.reward_per_time() >= self.threshold


class LazyBehaviour(DriverBehaviour):
    """Accept only if driver idle >= min_ticks AND pickup distance < 5.0 units.
    
    Selective drivers who need rest and prefer nearby jobs.
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
        """Accept only if idle >= min_ticks AND pickup distance < 5.0. Raises TypeError for wrong types.
        """
        from .driver import Driver as DriverClass
        from .offer import Offer as OfferClass
        
        if not isinstance(driver, DriverClass):
            raise TypeError(f"decide() requires Driver, got {type(driver).__name__}")
        if not isinstance(offer, OfferClass):
            raise TypeError(f"decide() requires Offer, got {type(offer).__name__}")
        if not isinstance(time, int):
            raise TypeError(f"decide() requires int time, got {type(time).__name__}")
        
        # Calculate how long driver has been idle
        idle_duration = time - driver.idle_since
        
        # Calculate distance to pickup location
        distance_to_pickup = driver.position.distance_to(offer.request.pickup)
        
        # Accept only if both conditions are met: sufficient rest AND nearby job
        return idle_duration >= self.idle_ticks_needed and distance_to_pickup < LAZY_MAX_PICKUP_DISTANCE
