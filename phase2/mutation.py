"""
Behaviour mutation strategies for driver evolution.

Mutations allow drivers to adapt strategies based on performance.
Provides MutationRule (ABC) with HybridMutation implementation:
- HybridMutation: Performance-based primary, stagnation-based exploration

Lifecycle: Simulation calls mutation.maybe_mutate(driver, time) each tick.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import random

from .driver import Driver
from .behaviours import GreedyDistanceBehaviour, EarningsMaxBehaviour, LazyBehaviour
from .helpers_2.core_helpers import (
    get_driver_history_window,
    calculate_average_fare,
    get_behaviour_name,
)

if TYPE_CHECKING:
    from typing import List, Dict, Any


# ====================================================================
# MUTATION BEHAVIOUR PARAMETERS (module-level constants)
# ====================================================================
# Used when creating new behaviour instances during mutations

# HybridMutation: Thresholds for when to switch behaviours
HYBRID_LOW_EARNINGS_THRESHOLD = 3.0      # Switch to greedy if earnings drop below this
HYBRID_HIGH_EARNINGS_THRESHOLD = 10.0    # Switch to earnings-max if earnings exceed this
HYBRID_COOLDOWN_TICKS = 10               # Minimum ticks between mutations (avoid churn)
HYBRID_STAGNATION_WINDOW = 8             # If earnings stagnate for this many ticks, explore
HYBRID_EXPLORATION_PROBABILITY = 0.3     # 30% chance to explore when stagnating

# Greedy mutation: Accept nearby pickups
GREEDY_MAX_DISTANCE = 10.0

# EarningsMax mutation: Accept high-reward-per-time jobs
EARNINGS_MIN_REWARD_PER_TIME = 0.8

# Lazy mutation: Accept only after rest
LAZY_IDLE_TICKS_NEEDED = 5
LAZY_MAX_DISTANCE = 5.0


# ====================================================================
# Mutation Rule Base Class
# ====================================================================

class MutationRule(ABC):
    """Abstract base for driver mutation strategies. Subclasses implement maybe_mutate()."""

    @abstractmethod
    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """Possibly change driver.behaviour based on performance/conditions."""
        raise NotImplementedError("Subclasses must implement maybe_mutate()")



# ====================================================================
# Hybrid Mutation (Performance + Exploration)
# ====================================================================

class HybridMutation(MutationRule):
    """Performance-based primary, exploration-based secondary mutation strategy.
    
    Adapts driver behaviour based on recent earnings performance:
    - LOW earnings: Switch to GREEDY (accept more jobs regardless of distance)
    - HIGH earnings: Switch to EARNINGS-MAX (become picky, optimize reward-per-time)
    - STAGNATING earnings: Explore other behaviours to break pattern (30% chance)
    - COOLDOWN: Driver can mutate at most once per 10 ticks (avoid constant switching)
    
    This models realistic driver adaptation: struggling drivers accept more work,
    successful drivers become selective, stagnating drivers experiment, and all drivers
    need time to adjust to new strategies before switching again.
    """

    def __init__(
        self,
        window: int = 5,
        low_threshold: float = HYBRID_LOW_EARNINGS_THRESHOLD,
        high_threshold: float = HYBRID_HIGH_EARNINGS_THRESHOLD,
        cooldown_ticks: int = HYBRID_COOLDOWN_TICKS,
        stagnation_window: int = HYBRID_STAGNATION_WINDOW,
        exploration_prob: float = HYBRID_EXPLORATION_PROBABILITY
    ):
        """Initialize with earnings window, thresholds, cooldown, and stagnation parameters."""
        if window <= 0:
            raise ValueError(f"window must be > 0, got {window}")
        if low_threshold < 0:
            raise ValueError(f"low_threshold must be >= 0, got {low_threshold}")
        if high_threshold < low_threshold:
            raise ValueError(f"high_threshold must be >= low_threshold")
        if cooldown_ticks < 0:
            raise ValueError(f"cooldown_ticks must be >= 0, got {cooldown_ticks}")
        if stagnation_window <= 0:
            raise ValueError(f"stagnation_window must be > 0, got {stagnation_window}")
        if not (0.0 <= exploration_prob <= 1.0):
            raise ValueError(f"exploration_prob must be in [0, 1], got {exploration_prob}")
        
        self.window = window
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.cooldown_ticks = cooldown_ticks
        self.stagnation_window = stagnation_window
        self.exploration_prob = exploration_prob
        
        # Track mutations for reporting: {(from_behaviour, to_behaviour): count}
        self.mutation_transitions = {}
        
        # Detailed mutation history for debugging/analysis
        # List of {time, driver_id, from_behaviour, to_behaviour, reason}
        self.mutation_history = []
        
        # Exit thresholds for behaviour-specific conditions
        # More generous thresholds to allow drivers time in each behaviour
        self.greedy_exit_threshold = 7.5        # Exit greedy only when earnings well-recovered (>25% above low threshold)
        self.earnings_max_exit_threshold = 5.0  # Exit earnings-max when struggling significantly (<low threshold + 2)
        self.lazy_min_success_threshold = 5.0   # Lazy is the neutral/reset behaviour

    def _average_fare(self, driver: Driver) -> Optional[float]:
        """Return average fare from last window trips, or None if insufficient history."""
        history = get_driver_history_window(driver.history, self.window)
        return calculate_average_fare(history)

    def _is_stagnating(self, driver: Driver) -> bool:
        """Check if driver earnings are stagnating (no improvement over recent window)."""
        history = get_driver_history_window(driver.history, self.stagnation_window)
        if len(history) < 2:
            return False
        
        fares = [entry.get("fare", 0.0) for entry in history]
        avg_fare = calculate_average_fare(history)
        
        if avg_fare is None or avg_fare < 0.1:
            return False
        
        # Check variance: if 70%+ of trips within 5% of average, consider stagnating
        tolerance = avg_fare * 0.05
        stagnant_count = sum(1 for f in fares if abs(f - avg_fare) <= tolerance)
        return stagnant_count >= len(fares) * 0.7

    def _should_exit_behaviour(self, driver: Driver, avg_fare: Optional[float]) -> bool:
        """Check if driver should exit their current behaviour based on earnings recovery/decline.
        
        Exit conditions (behaviour-specific):
        - GreedyDistanceBehaviour: Exit if earnings improve to >= 6.0 (recovered, no longer struggling)
        - EarningsMaxBehaviour: Exit if earnings drop below 6.0 (unsustainable, too picky)
        - LazyBehaviour: No exit (neutral fallback behaviour)
        
        Args:
            driver: Driver to check
            avg_fare: Average fare from recent trips
            
        Returns:
            bool: True if driver should exit current behaviour
        """
        if avg_fare is None:
            return False
        
        current_behaviour = get_behaviour_name(driver.behaviour)
        
        # GreedyDistanceBehaviour exit: earnings recovered to healthy level
        if current_behaviour == "GreedyDistanceBehaviour":
            return avg_fare >= self.greedy_exit_threshold
        
        # EarningsMaxBehaviour exit: earnings unsustainably low
        if current_behaviour == "EarningsMaxBehaviour":
            return avg_fare < self.earnings_max_exit_threshold
        
        # LazyBehaviour: Keep as neutral behaviour (no exit)
        return False

    def _record_detailed_mutation(self, driver_id: int, time: int, from_behaviour: str, 
                                 to_behaviour: str, reason: str, avg_fare: Optional[float] = None) -> None:
        """Record detailed mutation information for analysis.
        
        Args:
            driver_id: ID of the driver being mutated
            time: Simulation time of mutation
            from_behaviour: Behaviour being exited
            to_behaviour: New behaviour assigned
            reason: Why mutation occurred (e.g., "exit_greedy_recovered", "performance_low_earnings")
            avg_fare: Average fare at time of mutation (optional, for context)
        """
        entry = {
            "time": time,
            "driver_id": driver_id,
            "from_behaviour": from_behaviour,
            "to_behaviour": to_behaviour,
            "reason": reason,
            "avg_fare": avg_fare
        }
        self.mutation_history.append(entry)

    def _can_mutate(self, driver: Driver, time: int) -> bool:
        """Check if driver is in cooldown period (can only mutate once per N ticks)."""
        last_mutation_time = getattr(driver, "_last_mutation_time", -float("inf"))
        return (time - last_mutation_time) >= self.cooldown_ticks

    def _record_mutation(self, driver: Driver, time: int) -> None:
        """Record that a mutation occurred at this time."""
        driver._last_mutation_time = time
    
    def _track_transition(self, old_behaviour_name: str, new_behaviour_name: str) -> None:
        """Track behaviour transition for reporting."""
        key = (old_behaviour_name, new_behaviour_name)
        self.mutation_transitions[key] = self.mutation_transitions.get(key, 0) + 1

    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """Adapt behaviour based on performance: low→greedy, high→earnings-max, stagnating→explore.
        
        Applies exit conditions first: if driver should leave current behaviour, reset to LazyBehaviour.
        Then applies performance-based mutations if conditions warrant change.
        """
        # Check cooldown: driver can only mutate once per N ticks
        if not self._can_mutate(driver, time):
            return
        
        avg = self._average_fare(driver)
        if avg is None:
            return  # Not enough history yet
        
        old_behaviour_name = get_behaviour_name(driver.behaviour)
        
        # EXIT CONDITION: Check if driver should leave current behaviour
        if self._should_exit_behaviour(driver, avg):
            # Exit current behaviour by resetting to neutral LazyBehaviour
            reason = f"exit_{old_behaviour_name.lower()}"
            driver.behaviour = LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
            self._track_transition(old_behaviour_name, "LazyBehaviour")
            self._record_detailed_mutation(driver.id, time, old_behaviour_name, "LazyBehaviour", reason, avg)
            self._record_mutation(driver, time)
            return  # Exit early, don't apply performance-based mutations this tick
        
        # PRIMARY: Performance-based switching
        if avg < self.low_threshold:
            # Struggling: switch to greedy (accept more jobs)
            driver.behaviour = GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
            self._track_transition(old_behaviour_name, "GreedyDistanceBehaviour")
            self._record_detailed_mutation(driver.id, time, old_behaviour_name, "GreedyDistanceBehaviour", 
                                         "performance_low_earnings", avg)
            self._record_mutation(driver, time)
        elif avg > self.high_threshold:
            # Thriving: switch to earnings-max (become selective)
            driver.behaviour = EarningsMaxBehaviour(min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME)
            self._track_transition(old_behaviour_name, "EarningsMaxBehaviour")
            self._record_detailed_mutation(driver.id, time, old_behaviour_name, "EarningsMaxBehaviour",
                                         "performance_high_earnings", avg)
            self._record_mutation(driver, time)
        elif self._is_stagnating(driver):
            # SECONDARY: Stagnating performance → explore to break pattern
            if random.random() < self.exploration_prob:
                # Randomly try a different behaviour
                choice = random.choice(["greedy", "earnings", "lazy"])
                if choice == "greedy":
                    driver.behaviour = GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
                    self._track_transition(old_behaviour_name, "GreedyDistanceBehaviour")
                    self._record_detailed_mutation(driver.id, time, old_behaviour_name, "GreedyDistanceBehaviour",
                                                 "stagnation_exploration", avg)
                elif choice == "earnings":
                    driver.behaviour = EarningsMaxBehaviour(min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME)
                    self._track_transition(old_behaviour_name, "EarningsMaxBehaviour")
                    self._record_detailed_mutation(driver.id, time, old_behaviour_name, "EarningsMaxBehaviour",
                                                 "stagnation_exploration", avg)
                else:  # choice == "lazy"
                    driver.behaviour = LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
                    self._track_transition(old_behaviour_name, "LazyBehaviour")
                    self._record_detailed_mutation(driver.id, time, old_behaviour_name, "LazyBehaviour",
                                                 "stagnation_exploration", avg)
                self._record_mutation(driver, time)
