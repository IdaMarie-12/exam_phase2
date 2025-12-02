from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.model import Driver

#-----------------------------------
# Mutation Rule
#-----------------------------------
class MutationRule:
"""  Models how drivers change their behaviour over time.
Responsibility: inspect a driver (and possibly global statistics) and decide whether to update its
behaviour or behaviour parameters.
You must implement at least one non-trivial mutation rule and demonstrate that drivers can
 change behaviour during a simulation run."""
    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """Possibly change the driver's behaviour based on performance"""
        raise NotImplementedError

#-----------------------------------
# Performance Mutation Rule
#-----------------------------------

@dataclass
class PerformanceMutationRule(MutationRule):
    """ Change behavior if recent performance is below a threshold. """
    #mangler:  if the driver’s average earnings or served requests in the last N trips is below a threshold,
    #change from a picky to a more greedy behaviour.

    def __init__(self, window_size: int = 5, min_avg_earning: float = 8.0, max_speed: float = 2.5, explore_prob: float = 0.02) -> None:
        """ Initialize the mutation rule. """
        raise NotImplementedError

    def maybe_mutate(self, driver: "Driver", time: int) -> None:
        """ Implement mutation logic. """
        raise NotImplementedError

class ExplorationMutation(MutationRule):
    #mangler: with a small fixed probability, randomly switch to another behaviour.
