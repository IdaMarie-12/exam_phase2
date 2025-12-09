from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import random
from .driver import Driver
from .request import Request

# --------------------------------------
# Mutation Rule Base class
# --------------------------------------
class MutationRule(ABC):
    """ Abstract base class for all driver mutation rules. """

    @abstractmethod
    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """ Possible mutate the drivers behavior in-place. """
        return NotImplemented

# --------------------------------------
# Performance Based Mutation
# --------------------------------------
class PerformanceBasedMutation(MutationRule):
    """ If a drivers average fare over the last "window" trips is below earnings_threshold, make them more "aggrissive" by switching to a greedy distance behaviour. """

    def __init__(self, window: int = 5, earnings_threshold: float = 5.0):
        self.window = window
        self.earnings_threshold = earnings_threshold

    def _average_fare(self, driver: Driver) -> Optional[float]:
        history = driver.history[-self.window:]
        if not history:
            return None
        total = sum(entry.get("fare", 0.0) for entry in history)
        return total / len(history)

    def maybe_mutate(self, driver: Driver, time: int) -> None:
        avg = self._average_fare(driver)
        if avg is None:
            return
        if avg < self.earnings_threshold:
            driver.behavior = GreedyDistanceBehaviour(max_distance=10.0)

# --------------------------------------
# Exploration Mutation
# --------------------------------------
class ExplorationMutation(MutationRule):
    """ With probability "p" on each tick, randomly switch the dirvers behaviour to one of several predefined strategies. """

    def __init__(self, p: float = 0.1):
        self.p = p

    def maybe_mutate(self, driver: Driver, time: int) -> None:
        if random.random() >= self.p:
            return

        choice = random.choice(["greedy", "earnigns", "lazy"])
        if choice == "greedy":
            driver.behaviour = GreedyDistanceBehaviour(max_distance = 15.0)
        elif choice == "earnings":
            driver.behaviour = EarningsMaxBehaviour(min_reward_per_time = 0.5)
        else:
            driver.behaviour = LazyBehaviour(idle_ticks_needed = 3, max_distance = 5.0)
