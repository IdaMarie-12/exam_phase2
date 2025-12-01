from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.model import Driver, Request, Point

#-----------------------------------
# Offer
#-----------------------------------
@dataclass
class Offer:
    """ A proposed pairing between a driver and request, with estimated values. """
    driver: Driver
    request: Request
    estimated_travel_time: float
    estimated_reward: float
    pickup_distance: float

#-----------------------------------
# Dispatch Policy
#-----------------------------------
class DispatchPolicy(ABC):
    """ Abstract base class for dispatch strategies. """
    @abstractmethod
    def assign(self, driver: List["Driver"], requests: List[Request], time: int) -> List[Tuple["Driver", "Request"]]:
        """ Return proposed (driver, request) pairs for this tick. """
        raise NotImplementedError

#-----------------------------------
# Nearest Neighbor Policy
#-----------------------------------
class NearestNeighborPolicy(DispatchPolicy):
    """ Match each waiting request  to the nearest idle driver. """

    def assign(self, driver: List["Driver"], requests: List[Request], time: int) -> List[Tuple["Driver", "Request"]]:
        """ Implement nearest-neighbor logic. """
        raise NotImplementedError

#-----------------------------------
# Global Greedy Policy
#-----------------------------------
class GlobalGreedyPolicy(DispatchPolicy):
    """ Build all (idle driver, waiting request) pairs, sort by distance, match greedily. """

    def assign(self, drivers: List["Driver"], requests: List["Requests"], time: int) -> List[Tuple["Driver", "Request"]]:
        """ Implement global greedy matching. """
        return []
