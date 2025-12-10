"""
Behaviour mutation strategies for driver evolution.

Mutations allow drivers to adapt their decision strategies based on performance.
This module provides an abstract MutationRule base class and concrete implementations
for performance-based and exploration-based mutations.

Architecture:
    MutationRule (ABC)
        ├── PerformanceBasedMutation - Switch to greedier behaviour if earnings low
        └── ExplorationMutation - Stochastically explore new strategies

Lifecycle:
    1. Simulation creates mutation_rule (e.g., PerformanceBasedMutation)
    2. On each tick, simulation calls mutation_rule.maybe_mutate(driver, time)
    3. Mutation inspects driver's history and current behaviour
    4. If conditions met, mutation changes driver.behaviour to new strategy
    5. Next offers, driver uses new behaviour to make decisions

Example:
    >>> mutation = PerformanceBasedMutation(window=5, earnings_threshold=5.0)
    >>> driver.behaviour = LazyBehaviour(...)  # Start lazy
    >>> for tick in range(100):
    ...     # If avg earnings over last 5 trips < 5.0, switch to greedy
    ...     mutation.maybe_mutate(driver, tick)
    ...     # Driver now uses GreedyDistanceBehaviour if earnings too low
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import random

from .driver import Driver
from .behaviours import GreedyDistanceBehaviour, EarningsMaxBehaviour, LazyBehaviour

if TYPE_CHECKING:
    from typing import List, Dict, Any


# ====================================================================
# Mutation Rule Base Class
# ====================================================================

class MutationRule(ABC):
    """
    Abstract base class for all driver mutation rules.
    
    Mutations implement adaptive strategies where drivers can change their
    decision-making behaviour based on observed performance. This creates
    realistic agent evolution where poor performers adapt to new strategies.
    
    Subclasses must implement the maybe_mutate() method which:
    1. Examines the driver's history and current state
    2. Decides if mutation conditions are met
    3. Changes driver.behaviour in-place if appropriate
    
    Key Design:
        - Mutations happen during simulation ticks (stochastic timing)
        - Multiple mutations can be chained or used together
        - Each mutation is independent (can be composed)
        - In-place modification allows simulation to observe changes
    
    Example Workflow:
        >>> rule = PerformanceBasedMutation(window=5, earnings_threshold=5.0)
        >>> # Driver with poor earnings switches strategy
        >>> rule.maybe_mutate(driver, time=100)
        >>> # driver.behaviour is now GreedyDistanceBehaviour if conditions met
    """

    @abstractmethod
    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """
        Possibly mutate the driver's behaviour based on history and conditions.
        
        Implementations should:
        1. Check driver.history for performance metrics
        2. Evaluate mutation condition (earnings, idle time, etc.)
        3. If condition met, replace driver.behaviour with new strategy
        4. If condition not met, leave behaviour unchanged
        
        This is called once per simulation tick per driver, so should be
        computationally efficient.
        
        Args:
            driver: Driver to possibly mutate
            time: Current simulation time (in ticks)
            
        Returns:
            None (modifies driver.behaviour in-place if mutation occurs)
            
        Note:
            Subclasses should handle:
            - Empty history gracefully (no completed trips yet)
            - Division by zero in ratio calculations
            - Stochastic conditions (probability thresholds)
        """
        return NotImplemented



# ====================================================================
# Performance-Based Mutation
# ====================================================================

class PerformanceBasedMutation(MutationRule):
    """
    Adaptive mutation strategy based on driver earnings performance.
    
    Monitors driver's average earnings over a sliding window of completed trips.
    If average falls below threshold, driver switches to greedier behaviour
    (GreedyDistanceBehaviour) to increase pickup frequency and recovery earnings.
    
    This creates realistic adaptation: struggling drivers become less selective
    and more willing to accept distant pickups to improve revenue.
    
    Strategy Logic:
        1. Look at last N completed trips (window)
        2. Calculate average fare per trip
        3. If avg_fare < earnings_threshold:
            - Switch to GreedyDistanceBehaviour (distance-focused)
            - Allows driver to accept more distant offers
            - Increases pickup frequency, improves earnings
        4. If avg_fare >= earnings_threshold:
            - Keep current behaviour (successful strategy)
    
    Parameters:
        window: Number of recent trips to analyze (default: 5)
                - Larger window: More stable but slower adaptation
                - Smaller window: Quick adaptation but noisier
        earnings_threshold: Minimum acceptable average fare (default: 5.0)
                - Below this triggers mutation to greedier strategy
                - Should be tuned to simulation parameters
    
    Example:
        >>> mutation = PerformanceBasedMutation(window=5, earnings_threshold=5.0)
        >>> # Driver has completed 10 trips with fares [2, 3, 2, 4, 3, ...]
        >>> # Last 5 trips average: (2+4+3+2+4)/5 = 3.0 < 5.0
        >>> mutation.maybe_mutate(driver, time=100)
        >>> # driver.behaviour is now GreedyDistanceBehaviour(max_distance=10.0)
        >>> # Next offers: driver will accept pickups up to 10.0 units away
        
    Design Notes:
        - Only mutates if sufficient history exists (window trips completed)
        - No mutation if driver has < window completed trips
        - Greedy parameters (max_distance=10.0) chosen for balanced exploration
    """

    def __init__(self, window: int = 5, earnings_threshold: float = 5.0):
        """
        Initialize performance-based mutation rule.
        
        Args:
            window: Number of recent trips to average (must be > 0)
            earnings_threshold: Minimum avg fare before switching to greedy
            
        Raises:
            ValueError: If window <= 0 or earnings_threshold < 0
        """
        if window <= 0:
            raise ValueError(f"window must be > 0, got {window}")
        if earnings_threshold < 0:
            raise ValueError(f"earnings_threshold must be >= 0, got {earnings_threshold}")
        
        self.window = window
        self.earnings_threshold = earnings_threshold

    def _average_fare(self, driver: Driver) -> Optional[float]:
        """
        Calculate average fare from driver's recent completed trips.
        
        Extracts the last N trip records from driver.history and computes
        mean fare. Returns None if insufficient history (< window trips).
        
        Args:
            driver: Driver with history of completed trips
            
        Returns:
            float: Average fare over last window trips, or None if < window trips
            
        Example:
            >>> driver.history = [
            ...     {"request_id": 1, "fare": 5.0},
            ...     {"request_id": 2, "fare": 3.5},
            ...     {"request_id": 3, "fare": 6.0},
            ... ]
            >>> mutation._average_fare(driver)
            4.833...
        """
        history = driver.history[-self.window:]
        if not history:
            return None
        total = sum(entry.get("fare", 0.0) for entry in history)
        return total / len(history)

    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """
        Check if driver should switch to greedier behaviour based on earnings.
        
        Process:
        1. Calculate average fare over last window trips
        2. If no history available, skip mutation
        3. If avg_fare < earnings_threshold, switch to GreedyDistanceBehaviour
        4. Otherwise, leave behaviour unchanged
        
        Args:
            driver: Driver to possibly mutate
            time: Current simulation time (not used, provided for interface)
            
        Example:
            >>> mutation = PerformanceBasedMutation(window=5, earnings_threshold=5.0)
            >>> mutation.maybe_mutate(driver, time=100)
            >>> # If low earnings detected:
            >>> # driver.behaviour = GreedyDistanceBehaviour(max_distance=10.0)
        """
        avg = self._average_fare(driver)
        if avg is None:
            return  # Not enough history yet
        
        if avg < self.earnings_threshold:
            driver.behaviour = GreedyDistanceBehaviour(max_distance=10.0)



# ====================================================================
# Exploration-Based Mutation
# ====================================================================

class ExplorationMutation(MutationRule):
    """
    Stochastic mutation strategy for behavioural exploration.
    
    With fixed probability p on each tick, randomly switches driver's behaviour
    to one of three strategies: GreedyDistanceBehaviour, EarningsMaxBehaviour,
    or LazyBehaviour. This adds exploration to avoid getting stuck in poor
    local optima and models drivers trying new approaches.
    
    Strategy Logic:
        1. On each tick, generate random number r in [0, 1)
        2. If r < p (probability threshold):
            - Randomly choose one of three behaviours
            - Replace driver.behaviour with new strategy
            - Driver uses new strategy for next decisions
        3. If r >= p:
            - Keep current behaviour unchanged
    
    Parameters:
        p: Probability of exploration on each tick (default: 0.1)
           - p=0.0: Never explore (stick with current strategy)
           - p=0.1: ~10% chance of exploration each tick
           - p=1.0: Always explore (random each tick)
    
    Behaviour Distribution:
        When exploration triggers, equally likely to get:
        - GreedyDistanceBehaviour(max_distance=15.0)  - 1/3 probability
        - EarningsMaxBehaviour(min_reward_per_time=0.5)  - 1/3 probability
        - LazyBehaviour(idle_ticks_needed=3, max_distance=5.0)  - 1/3 probability
    
    Example Scenario:
        >>> mutation = ExplorationMutation(p=0.1)
        >>> driver.behaviour = LazyBehaviour(...)  # Start lazy
        >>> for tick in range(1000):
        ...     # Each tick, ~10% chance to randomly switch
        ...     mutation.maybe_mutate(driver, tick)
        ...     # Sometimes driver.behaviour becomes GreedyDistanceBehaviour
        ...     # Sometimes EarningsMaxBehaviour, sometimes stays lazy
        
    Use Cases:
        1. **Escape Local Optima:** Help drivers stuck in suboptimal strategies
        2. **Realistic Behaviour:** Model drivers trying new approaches
        3. **Exploration vs Exploitation:** Balance current strategy vs trying new ones
        4. **Parameter Tuning:** Adjust p to control exploration rate
    
    Design Notes:
        - Independent of driver history (doesn't look at performance)
        - Pure stochasticity (random exploration)
        - Can be combined with PerformanceBasedMutation for hybrid strategies
        - Parameters for chosen behaviour are fixed (hardcoded)
    """

    def __init__(self, p: float = 0.1):
        """
        Initialize exploration-based mutation rule.
        
        Args:
            p: Probability of exploration on each tick (must be in [0, 1])
            
        Raises:
            ValueError: If p not in [0, 1]
        """
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"p must be in [0, 1], got {p}")
        self.p = p

    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """
        Randomly explore new behaviours with probability p.
        
        Process:
        1. Generate random number r in [0, 1)
        2. If r >= p, skip mutation (keep current behaviour)
        3. If r < p, randomly choose and switch to new behaviour:
           - "greedy": GreedyDistanceBehaviour(max_distance=15.0)
           - "earnings": EarningsMaxBehaviour(min_reward_per_time=0.5)
           - "lazy": LazyBehaviour(idle_ticks_needed=3, max_distance=5.0)
        
        Args:
            driver: Driver to possibly explore with
            time: Current simulation time (not used, provided for interface)
            
        Example:
            >>> mutation = ExplorationMutation(p=0.2)
            >>> mutation.maybe_mutate(driver, time=100)
            >>> # 20% chance: driver.behaviour changes to random new strategy
            >>> # 80% chance: driver.behaviour unchanged
            
        Notes:
            - Each behaviour chosen with equal probability (1/3 each)
            - Parameters for behaviours are fixed (could be made configurable)
            - Previous behaviour is lost (no history of past strategies)
        """
        if random.random() >= self.p:
            return  # Skip exploration (keep current behaviour)

        # Randomly choose new behaviour
        choice = random.choice(["greedy", "earnings", "lazy"])
        
        if choice == "greedy":
            driver.behaviour = GreedyDistanceBehaviour(max_distance=15.0)
        elif choice == "earnings":
            driver.behaviour = EarningsMaxBehaviour(min_reward_per_time=0.5)
        else:  # choice == "lazy"
            driver.behaviour = LazyBehaviour(idle_ticks_needed=3, max_distance=5.0)
