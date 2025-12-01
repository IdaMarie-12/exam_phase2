from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from phase2.model import Driver
    from phase2.policies import Offer

#-----------------------------------
# Driver Decision-Making behavior
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
