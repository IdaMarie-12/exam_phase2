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
        """ Posible change the driver's behavior based on performance. """
        raise NotImplementedError

@dataclass
class PerformanceMutationRule(MutationRule):
    """ Change behavior if recent performance is below a threshold. """

    def maybe_mutate(self, driver: "Driver", time: int) -> None:
        """ Implement mutation logic. """
        pass