from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from phase2.model import Driver
    from phase2.policies import Offer

#-----------------------------------
# Base class
#-----------------------------------
class DriverBehavior(ABC):
    """ Abstract base class for driver decision-making behavior. """

    @abstractmethod
    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """ Return True if the driver accepts the offer, False otherwise."""
        raise NotImplementedError

#-----------------------------------
# Greedy Behavior
#-----------------------------------
class GreedyDistanceBehavior(DriverBehavior):
    """ Accept if the distance to pickup is below a threshold. """

#-----------------------------------
# Earning Max Behavior
#-----------------------------------
class EarningsMaxBehavior(DriverBehavior):
    """ Accept if reward/time ratio exceeds a threshold. """

#-----------------------------------
# Lazy Behavior
#-----------------------------------
class LazyBehavior(DriverBehavior):
    """
    Accept only if:
        - driver has been idle for at least min_idle_time ticks
        - pickup distance is not too large
    """

    def __init__(self, max_pickup_distance: float = 12.0, min_idle_time: int = 5) -> None:
        """ Initialize the behavior. """
        self.max_pickup_distance = max_pickup_distance
        self.min_idle_time = min_idle_time

    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """ Return True if the driver accepts the offer, False otherwise. """
        raise NotImplementedError
