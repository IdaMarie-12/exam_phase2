from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .offer import Offer
    from .driver import Driver


# ====================================================================
# BEHAVIOUR PARAMETERS and CONSTANTS

# LazyBehaviour: Maximum acceptable distance to pickup location
LAZY_MAX_PICKUP_DISTANCE = 5.0


class DriverBehaviour(ABC):
    """Abstract base class for driver decision strategies."""

    @abstractmethod
    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """Decide whether driver accepts the offer."""
        raise NotImplementedError("Subclasses must implement decide()")


class GreedyDistanceBehaviour(DriverBehaviour):
    """Accept offers with pickup distance <= max_distance threshold."""

    def __init__(self, max_distance: float):
        """Initialize greedy distance behaviour."""
        if max_distance <= 0:
            raise ValueError(f"max_distance must be positive, got {max_distance}")
        self.max_distance = max_distance

    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """Accept if pickup distance is within max_distance threshold."""
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
        """Initialize earnings maximization behaviour."""
        if min_reward_per_time < 0:
            raise ValueError(f"min_reward_per_time must be non-negative, got {min_reward_per_time}")
        self.threshold = min_reward_per_time

    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """Accept if reward/travel_time >= threshold."""
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
        """Initialize lazy behaviour."""
        if idle_ticks_needed < 0:
            raise ValueError(f"idle_ticks_needed must be non-negative, got {idle_ticks_needed}")
        self.idle_ticks_needed = idle_ticks_needed

    def decide(self, driver: "Driver", offer: "Offer", time: int) -> bool:
        """Accept only if idle >= min_ticks AND pickup distance < 5.0."""
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
