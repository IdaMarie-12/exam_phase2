from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.model import Driver

#-----------------------------------
# Mutation Rule
#-----------------------------------
class MutationRule(ABC):
    """ Abstract base class for behavior mutation rules. """

    @abstractmethod
    def maybe_mutate(self, driver: "Driver", time: int) -> None:
        """ Possible change the driver's behavior based on performance. """
        raise NotImplementedError

#-----------------------------------
# Performance Mutation Rule
#-----------------------------------

@dataclass
class PerformanceMutationRule(MutationRule):
    """ Change behavior if recent performance is below a threshold. """

    def __init__(self, window_size: int = 5, min_avg_earning: float = 8.0, max_speed: float = 2.5, explore_prob: float = 0.02) -> None:
        """ Initialize the mutation rule. """
        raise NotImplementedError

    def maybe_mutate(self, driver: "Driver", time: int) -> None:
        """ Implement mutation logic. """
        raise NotImplementedError
