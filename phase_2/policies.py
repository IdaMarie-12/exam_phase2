from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.model import Driver, Request, Point

#-----------------------------------
# Offer
#-----------------------------------
class Offer:
"""A simple data object describing a proposal from the dispatcher to a driver.
 Attributes (suggested):
 – driver: Driver
 – request: Request
 – estimated_travel_time: float
 – estimated_reward: float (if you choose a reward model) """

#-----------------------------------
# Dispatch Policy
#-----------------------------------
class DispatchPolicy:
    #mangler

#-----------------------------------
# Nearest Neighbor Policy
#-----------------------------------
class NearestNeighborPolicy(DispatchPolicy):
    """ Match each waiting request  to the nearest idle driver. """
    # repeatedly match the closest idle driver to the closest waiting request.

    def assign(self, driver: List["Driver"], requests: List[Request], time: int) -> List[Tuple["Driver", "Request"]]:
        """ Implement nearest-neighbor logic. """
        raise NotImplementedError

#-----------------------------------
# Global Greedy Policy
#-----------------------------------
class GlobalGreedyPolicy(DispatchPolicy):
    """ Build all (idle driver, waiting request) pairs, sort by distance, match greedily. """
     # build all (idle driver, waiting request) pairs, sort by distance, and match greedily while avoiding reuse of drivers and requests

    def assign(self, drivers: List["Driver"], requests: List["Requests"], time: int) -> List[Tuple["Driver", "Request"]]:
        """ Implement global greedy matching. """
        return []

#-----------------------------------
# Combined Score Policy (distance + reward)
#-----------------------------------
class CombinedScorePolicy(DispatchPolicy):
    """
    Combine distance and reward into a single score and match greedily.

    score = w_dist * (1/(1 + distance)) + w_reward * estimated_reward + w_ratio * (estimated_reward / estimated_travel_time)
    """

    def __init__(self, w_dist: float = 0.4, w_reward: float = 0.3, w_ratio: float = 0.3) -> None:
        """ Initialize the combined score policy. """
        self.w_dist = w_dist
        self.w_reward = w_reward
        self.w_ratio = w_ratio

    def assign(self, drivers: List[Driver], requests: List[Request], time: int) -> List[Tuple[Driver, Request]]:
        """ Return proposed (driver, request) pairs for this tick. """
        raise NotImplementedError
