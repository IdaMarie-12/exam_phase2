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

# HybridMutation: Performance zones and mutation thresholds (spec: Appendix XX)
# Zone definitions based on average earnings from last 10 trips:
#   Struggling: < 3.0     → Switch to GreedyDistanceBehaviour
#   Recovery:   3.0-5.0   → Exit zone (Greedy exit at ≥5.0)
#   Normal:     5.0-7.5   → Evaluate stability, not primary action
#   Good:       7.5-10.0  → Stable performance, approaching selectivity
#   Thriving:   > 10.0    → Switch to EarningsMaxBehaviour
HYBRID_LOW_EARNINGS_THRESHOLD = 3.0      # Zone: Struggling (switch to Greedy)
HYBRID_HIGH_EARNINGS_THRESHOLD = 10.0    # Zone: Thriving (switch to EarningsMax)
HYBRID_GREEDY_EXIT_THRESHOLD = 5.0       # Greedy driver exits at avg fare ≥ 5.0
HYBRID_EARNINGS_EXIT_THRESHOLD = 6.0     # EarningsMax driver exits at avg fare < 6.0
HYBRID_COOLDOWN_TICKS = 10               # Minimum ticks between mutations
HYBRID_STAGNATION_WINDOW = 10            # Evaluate stagnation over last 10 trips
HYBRID_EXPLORATION_PROBABILITY = 0.3     # 30% chance to explore when stagnating (Greedy/EarningsMax)

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
        window: int = 10,
        low_threshold: float = HYBRID_LOW_EARNINGS_THRESHOLD,
        high_threshold: float = HYBRID_HIGH_EARNINGS_THRESHOLD,
        cooldown_ticks: int = HYBRID_COOLDOWN_TICKS,
        stagnation_window: int = HYBRID_STAGNATION_WINDOW,
        exploration_prob: float = HYBRID_EXPLORATION_PROBABILITY,
        greedy_exit_threshold: float = HYBRID_GREEDY_EXIT_THRESHOLD,
        earnings_exit_threshold: float = HYBRID_EARNINGS_EXIT_THRESHOLD
    ):
        """Initialize with earnings thresholds, cooldown, and exploration parameters.
        
        Args:
            window: Evaluation window for recent history (default 10 trips per spec)
            low_threshold: Switch to greedy if avg earnings below this (Struggling zone)
            high_threshold: Switch to earnings-max if avg earnings above this (Thriving zone)
            cooldown_ticks: Minimum ticks between mutations (default 10)
            stagnation_window: Evaluate stagnation over this many trips (default 10)
            exploration_prob: Probability to explore when stagnating (default 30%)
            greedy_exit_threshold: Greedy driver exits at avg fare ≥ this (Recovery/Normal boundary)
            earnings_exit_threshold: EarningsMax driver exits at avg fare < this
        """
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
        self.greedy_exit_threshold = greedy_exit_threshold      # Exit Greedy at ≥ 5.0
        self.earnings_max_exit_threshold = earnings_exit_threshold  # Exit EarningsMax at < 7.5
        
        # Track mutations for reporting: {(from_behaviour, to_behaviour): count}
        self.mutation_transitions = {}
        
        # Detailed mutation history for debugging/analysis
        # List of {time, driver_id, from_behaviour, to_behaviour, reason}
        self.mutation_history = []

    def _average_fare(self, driver: Driver) -> Optional[float]:
        """Return average fare from last window trips, or None if insufficient history."""
        history = get_driver_history_window(driver.history, self.window)
        return calculate_average_fare(history)

    def _is_stagnating(self, driver: Driver) -> bool:
        """Check if driver earnings are stagnating (low variance over last window trips)."""
        history = get_driver_history_window(driver.history, self.window)
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
        
        Exit conditions per spec:
        - GreedyDistanceBehaviour: Exit if avg fare > 5.0 (above Recovery zone, into Normal/Good)
        - EarningsMaxBehaviour: Exit if avg fare < 7.5 (below Good zone, into Normal/Recovery)
        - LazyBehaviour: No exit (neutral fallback state)
        
        Args:
            driver: Driver to check
            avg_fare: Average fare from recent trips
            
        Returns:
            bool: True if driver should exit current behaviour, False otherwise
        """
        if avg_fare is None:
            return False
        
        current_behaviour = get_behaviour_name(driver.behaviour)
        
        # GreedyDistanceBehaviour exit: earnings improved above Recovery zone (> 5.0)
        if current_behaviour == "GreedyDistanceBehaviour":
            return avg_fare > self.greedy_exit_threshold
        
        # EarningsMaxBehaviour exit: earnings dropped below Good zone (< 7.5)
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
        """Execute 5-step HybridMutation process per spec (Appendix XX):
        
        Step 1: Assess driver cooldown period - can only mutate once per 10 ticks
        Step 2: Calculate average fare from last 10 trips
        Step 3: Check exit conditions - exit current behaviour if thresholds met
        Step 4a: Primary mutation - performance-based (Struggling → Greedy, Thriving → EarningsMax)
        Step 4b: Secondary mutation - stagnation-based exploration (30% for active behaviours)
        
        Zone mapping (avg earnings):
          Struggling (< 3.0)     → Switch to GreedyDistanceBehaviour
          Recovery (3.0-5.0)     → Exit zone (Greedy exits at ≥5.0)
          Normal (5.0-7.5)       → Evaluate stability, check stagnation
          Good (7.5-10.0)        → Stable, approaching selectivity
          Thriving (> 10.0)      → Switch to EarningsMaxBehaviour
        
        Exit conditions:
          - Greedy: avg ≥ 5.0 → reset to Lazy
          - EarningsMax: avg < 7.5 → reset to Lazy
          - Lazy: no exit (neutral state)
        
        Stagnation (70% variance within ±5% of avg):
          - Lazy: always explore → random Greedy or EarningsMax
          - Greedy/EarningsMax: 30% chance explore → random other active behaviour
        
        New behaviour takes effect next tick (after offers evaluated this tick).
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
            # Struggling: switch to greedy if not already there
            if "Greedy" not in old_behaviour_name:
                # Not in Greedy yet - try greedy approach to accept more jobs
                driver.behaviour = GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
                self._track_transition(old_behaviour_name, "GreedyDistanceBehaviour")
                self._record_detailed_mutation(driver.id, time, old_behaviour_name, "GreedyDistanceBehaviour", 
                                             "performance_low_earnings", avg)
                self._record_mutation(driver, time)
            # else: already greedy, no mutation - let stagnation or exit conditions handle it
        elif avg > self.high_threshold:
            # Thriving: switch to earnings-max if not already there
            if "Earnings" not in old_behaviour_name:
                # Not in EarningsMax yet - try earnings-max approach for selectivity
                driver.behaviour = EarningsMaxBehaviour(min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME)
                self._track_transition(old_behaviour_name, "EarningsMaxBehaviour")
                self._record_detailed_mutation(driver.id, time, old_behaviour_name, "EarningsMaxBehaviour",
                                             "performance_high_earnings", avg)
                self._record_mutation(driver, time)
            # else: already in earnings-max, no mutation - let stagnation or exit conditions handle it
        elif self._is_stagnating(driver):
            # SECONDARY: Stagnating performance → explore to break pattern
            # Exploration probability determines if we mutate when stagnating
            
            should_explore = random.random() < self.exploration_prob
            
            if should_explore:
                # Extract behaviour shorthand: "GreedyDistanceBehaviour" → "greedy", etc.
                if "Greedy" in old_behaviour_name:
                    current_behaviour_short = "greedy"
                elif "Earnings" in old_behaviour_name:
                    current_behaviour_short = "earnings"
                else:
                    current_behaviour_short = "lazy"
                
                # Pick from behaviours different from current
                available_choices = [b for b in ["greedy", "earnings", "lazy"] if b != current_behaviour_short]
                choice = random.choice(available_choices)
                
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
