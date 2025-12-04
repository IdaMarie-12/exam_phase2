from abc import ABC, abstractmethod     # ABC = Abstract Base Class; allows defining abstract interfaces
from .offer import Offer                # Import the Offer data structure (contains reward, pickup location, etc.)
from .driver import Driver              # Import the Driver class


class DriverBehaviour(ABC):
    """
    Abstract base class that defines a general interface for all driver behaviour strategies.
    Instead, subclasses inherit from this one and implement the 'decide' method.
    The purpose of using an abstract class:
        - enforce a common interface (all behaviours MUST define 'decide')
        - allow polymorphism (different behaviours can be swapped and used interchangeably)
    """

    @abstractmethod
    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """
        Decide whether the driver should accept the given offer at the given simulation time.
        """
        raise NotImplementedError   # Ensures subclasses override this method


# Behaviour 1: GreedyDistanceBehaviour

class GreedyDistanceBehaviour(DriverBehaviour):
    """
    A simple behaviour where a driver only accepts offers that are
    within a maximum pickup distance.
    """

    def __init__(self, max_distance: float):
        self.max_distance = max_distance  # Store the distance threshold

    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """
        Accept the offer if the distance from the driver's position
        to the pickup location is less than or equal to max_distance.
        """
        # Compute the distance between driver and pickup location
        dist = driver.position.distance_to(offer.request.pickup)

        # Accept if the distance is within limits
        return dist <= self.max_distance



# Behaviour 2: EarningsMaxBehaviour

class EarningsMaxBehaviour(DriverBehaviour):
    """
    Accept only offers that yield a sufficient reward per unit time. 
    The idea is, the driver prioritizes earning efficiency rather than distance.
    min_reward_per_time (float): Minimum acceptable ratio of reward/time.
    """

    def __init__(self, min_reward_per_time: float):
        self.threshold = min_reward_per_time   # Store the earnings threshold

    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """
        Accept the offer if the ratio:
            (estimated_reward / estimated_travel_time)
        meets or exceeds the threshold.

        Reject if:
            - travel time is zero or negative (invalid data)
            - earnings are too low
        """
        # Prevent division by zero or nonsensical values
        if offer.estimated_travel_time <= 0:
            return False

        # Compare reward per time against threshold
        return (offer.estimated_reward / offer.estimated_travel_time) >= self.threshold



# Behaviour 3: LazyBehaviour

class LazyBehaviour(DriverBehaviour):
    """
    Accept an offer only if the driver has been idle for long enough AND the pickup is reasonably close.
        This behaviour simulates a driver who is "lazy":
            - They only accept jobs if they have been idle for a certain number of ticks.
            - They also require the pickup to be close (under 5 units).
    """

    def __init__(self, idle_ticks_needed: int):
        self.idle_ticks_needed = idle_ticks_needed  # Required idle time before accepting work

    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """
        Accept the offer if:
            1) The driver is currently idle.
            2) The driver has an attribute 'idle_since' indicating when they became idle.
            3) The time spent idle >= idle_ticks_needed.
            4) The pickup distance is less than 5.0.

        Reject otherwise.
        """

        # Check if the driver is idle
        idle = driver.status == "IDLE"

        # Retrieve when the driver started being idle (may not exist)
        idle_time = getattr(driver, "idle_since", None)

        # If driver is not idle or we don't know when they became idle → reject
        if not idle or idle_time is None:
            return False

        # Check if driver has been idle long enough
        idle_long_enough = (time - idle_time) >= self.idle_ticks_needed

        # Check if pickup is close (lazy drivers only accept very close jobs)
        close_enough = driver.position.distance_to(offer.request.pickup) < 5.0

        # Accept only if both conditions are satisfied
        return idle_long_enough and close_enough
