"""
Unit tests for Mutation classes and behaviour adaptation strategies.
Tests HybridMutation with performance-based and exploration-based switching.
"""

import unittest
import random
from phase2.mutation import (
    HybridMutation,
    HYBRID_LOW_EARNINGS_THRESHOLD,
    HYBRID_HIGH_EARNINGS_THRESHOLD,
    HYBRID_COOLDOWN_TICKS,
    HYBRID_STAGNATION_WINDOW,
    HYBRID_EXPLORATION_PROBABILITY,
    GREEDY_MAX_DISTANCE,
    EARNINGS_MIN_REWARD_PER_TIME,
    LAZY_IDLE_TICKS_NEEDED,
)
from phase2.driver import Driver
from phase2.request import Request
from phase2.point import Point
from phase2.behaviours import (
    GreedyDistanceBehaviour,
    EarningsMaxBehaviour,
    LazyBehaviour,
)


class TestHybridMutationInit(unittest.TestCase):
    """Test HybridMutation initialization and validation."""

    def test_init_default_parameters(self):
        """HybridMutation initializes with default parameters."""
        mutation = HybridMutation()
        self.assertEqual(mutation.window, 5)
        self.assertEqual(mutation.low_threshold, HYBRID_LOW_EARNINGS_THRESHOLD)
        self.assertEqual(mutation.high_threshold, HYBRID_HIGH_EARNINGS_THRESHOLD)
        self.assertEqual(mutation.cooldown_ticks, HYBRID_COOLDOWN_TICKS)
        self.assertEqual(mutation.stagnation_window, HYBRID_STAGNATION_WINDOW)
        self.assertEqual(mutation.exploration_prob, HYBRID_EXPLORATION_PROBABILITY)

    def test_init_custom_parameters(self):
        """HybridMutation accepts custom parameters."""
        mutation = HybridMutation(
            window=10,
            low_threshold=2.0,
            high_threshold=8.0,
            cooldown_ticks=5,
            stagnation_window=10,
            exploration_prob=0.5
        )
        self.assertEqual(mutation.window, 10)
        self.assertEqual(mutation.low_threshold, 2.0)
        self.assertEqual(mutation.high_threshold, 8.0)
        self.assertEqual(mutation.cooldown_ticks, 5)
        self.assertEqual(mutation.stagnation_window, 10)
        self.assertEqual(mutation.exploration_prob, 0.5)

    def test_init_invalid_window(self):
        """Invalid window raises ValueError."""
        with self.assertRaises(ValueError):
            HybridMutation(window=0)
        with self.assertRaises(ValueError):
            HybridMutation(window=-1)

    def test_init_invalid_low_threshold(self):
        """Invalid low_threshold raises ValueError."""
        with self.assertRaises(ValueError):
            HybridMutation(low_threshold=-1.0)

    def test_init_invalid_threshold_order(self):
        """high_threshold must be >= low_threshold."""
        with self.assertRaises(ValueError):
            HybridMutation(low_threshold=10.0, high_threshold=5.0)

    def test_init_invalid_cooldown(self):
        """Invalid cooldown raises ValueError."""
        with self.assertRaises(ValueError):
            HybridMutation(cooldown_ticks=-1)

    def test_init_invalid_stagnation_window(self):
        """Invalid stagnation_window raises ValueError."""
        with self.assertRaises(ValueError):
            HybridMutation(stagnation_window=0)
        with self.assertRaises(ValueError):
            HybridMutation(stagnation_window=-1)

    def test_init_invalid_exploration_prob(self):
        """Invalid exploration_prob raises ValueError."""
        with self.assertRaises(ValueError):
            HybridMutation(exploration_prob=-0.1)
        with self.assertRaises(ValueError):
            HybridMutation(exploration_prob=1.1)

    def test_init_tracking_structures(self):
        """HybridMutation initializes tracking structures."""
        mutation = HybridMutation()
        self.assertEqual(mutation.mutation_transitions, {})
        self.assertEqual(mutation.mutation_history, [])


class TestAverageFareCalculation(unittest.TestCase):
    """Test _average_fare helper method."""

    def setUp(self):
        """Create driver for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(window=3)

    def test_average_fare_empty_history(self):
        """Empty history returns None."""
        result = self.mutation._average_fare(self.driver)
        self.assertIsNone(result)

    def test_average_fare_with_history(self):
        """Average fare computed from history."""
        self.driver.history = [
            {"fare": 10.0},
            {"fare": 20.0},
            {"fare": 30.0},
        ]
        result = self.mutation._average_fare(self.driver)
        self.assertAlmostEqual(result, 20.0)

    def test_average_fare_respects_window(self):
        """Only recent window entries are used."""
        self.driver.history = [
            {"fare": 5.0},   # Outside window
            {"fare": 10.0},
            {"fare": 20.0},
            {"fare": 30.0},
        ]
        result = self.mutation._average_fare(self.driver)
        # Last 3: (10 + 20 + 30) / 3 = 20.0
        self.assertAlmostEqual(result, 20.0)

    def test_average_fare_insufficient_history(self):
        """Insufficient history returns available average."""
        self.driver.history = [{"fare": 15.0}]
        result = self.mutation._average_fare(self.driver)
        self.assertAlmostEqual(result, 15.0)


class TestStagnationDetection(unittest.TestCase):
    """Test _is_stagnating method."""

    def setUp(self):
        """Create driver for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(stagnation_window=5)

    def test_stagnation_empty_history(self):
        """Empty history is not stagnating."""
        result = self.mutation._is_stagnating(self.driver)
        self.assertFalse(result)

    def test_stagnation_insufficient_history(self):
        """Less than 2 entries is not stagnating."""
        self.driver.history = [{"fare": 10.0}]
        result = self.mutation._is_stagnating(self.driver)
        self.assertFalse(result)

    def test_stagnation_very_low_average(self):
        """Very low average (< 0.1) is not considered stagnating."""
        self.driver.history = [
            {"fare": 0.01},
            {"fare": 0.02},
            {"fare": 0.03},
        ]
        result = self.mutation._is_stagnating(self.driver)
        self.assertFalse(result)

    def test_stagnation_consistent_earnings(self):
        """Consistent earnings are stagnating."""
        # All fares very similar (within 5% of average)
        self.driver.history = [
            {"fare": 10.0},
            {"fare": 10.1},
            {"fare": 9.9},
            {"fare": 10.05},
            {"fare": 10.0},
        ]
        result = self.mutation._is_stagnating(self.driver)
        self.assertTrue(result)

    def test_stagnation_varying_earnings(self):
        """Varying earnings are not stagnating."""
        self.driver.history = [
            {"fare": 5.0},
            {"fare": 15.0},
            {"fare": 8.0},
            {"fare": 20.0},
            {"fare": 10.0},
        ]
        result = self.mutation._is_stagnating(self.driver)
        self.assertFalse(result)


class TestShouldExitBehaviour(unittest.TestCase):
    """Test _should_exit_behaviour method."""

    def setUp(self):
        """Create driver for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(
            low_threshold=3.0,
            high_threshold=10.0
        )

    def test_exit_none_avg_fare(self):
        """None average fare doesn't trigger exit."""
        result = self.mutation._should_exit_behaviour(self.driver, None)
        self.assertFalse(result)

    def test_exit_greedy_behaviour_recovered(self):
        """Exit GreedyDistanceBehaviour when earnings recover."""
        self.driver.behaviour = GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
        result = self.mutation._should_exit_behaviour(self.driver, 7.5)
        self.assertTrue(result)

    def test_exit_greedy_behaviour_still_struggling(self):
        """Don't exit GreedyDistanceBehaviour while still struggling."""
        self.driver.behaviour = GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
        result = self.mutation._should_exit_behaviour(self.driver, 5.0)
        self.assertFalse(result)

    def test_exit_earnings_max_behaviour_unsustainable(self):
        """Exit EarningsMaxBehaviour when earnings drop too low."""
        self.driver.behaviour = EarningsMaxBehaviour(min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME)
        result = self.mutation._should_exit_behaviour(self.driver, 4.0)
        self.assertTrue(result)

    def test_exit_earnings_max_behaviour_sustainable(self):
        """Don't exit EarningsMaxBehaviour when earnings are acceptable."""
        self.driver.behaviour = EarningsMaxBehaviour(min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME)
        result = self.mutation._should_exit_behaviour(self.driver, 6.0)
        self.assertFalse(result)

    def test_exit_lazy_behaviour_never(self):
        """Never exit LazyBehaviour (neutral fallback)."""
        self.driver.behaviour = LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        result = self.mutation._should_exit_behaviour(self.driver, 15.0)
        self.assertFalse(result)
        result = self.mutation._should_exit_behaviour(self.driver, 0.5)
        self.assertFalse(result)


class TestCanMutate(unittest.TestCase):
    """Test _can_mutate cooldown mechanism."""

    def setUp(self):
        """Create driver and mutation for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(cooldown_ticks=10)

    def test_can_mutate_first_time(self):
        """Can mutate if no previous mutation recorded."""
        result = self.mutation._can_mutate(self.driver, 100)
        self.assertTrue(result)

    def test_can_mutate_after_cooldown_expires(self):
        """Can mutate after cooldown_ticks have passed."""
        self.driver._last_mutation_time = 90
        result = self.mutation._can_mutate(self.driver, 100)
        self.assertTrue(result)

    def test_cannot_mutate_during_cooldown(self):
        """Cannot mutate within cooldown period."""
        self.driver._last_mutation_time = 95
        result = self.mutation._can_mutate(self.driver, 100)
        self.assertFalse(result)

    def test_cannot_mutate_just_before_cooldown_expires(self):
        """Cannot mutate one tick before cooldown expires."""
        self.driver._last_mutation_time = 91
        result = self.mutation._can_mutate(self.driver, 100)
        self.assertFalse(result)


class TestRecordMutation(unittest.TestCase):
    """Test _record_mutation and related tracking."""

    def setUp(self):
        """Create driver and mutation for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation()

    def test_record_mutation_sets_timestamp(self):
        """_record_mutation sets _last_mutation_time."""
        self.mutation._record_mutation(self.driver, 50)
        self.assertEqual(self.driver._last_mutation_time, 50)

    def test_track_transition_records_pair(self):
        """_track_transition increments transition counter."""
        self.mutation._track_transition("LazyBehaviour", "GreedyDistanceBehaviour")
        self.assertEqual(
            self.mutation.mutation_transitions[("LazyBehaviour", "GreedyDistanceBehaviour")],
            1
        )

    def test_track_transition_multiple_same(self):
        """Multiple identical transitions increment counter."""
        self.mutation._track_transition("LazyBehaviour", "GreedyDistanceBehaviour")
        self.mutation._track_transition("LazyBehaviour", "GreedyDistanceBehaviour")
        self.assertEqual(
            self.mutation.mutation_transitions[("LazyBehaviour", "GreedyDistanceBehaviour")],
            2
        )

    def test_track_transition_different_pairs(self):
        """Different transitions tracked separately."""
        self.mutation._track_transition("LazyBehaviour", "GreedyDistanceBehaviour")
        self.mutation._track_transition("LazyBehaviour", "EarningsMaxBehaviour")
        self.assertEqual(len(self.mutation.mutation_transitions), 2)

    def test_record_detailed_mutation(self):
        """_record_detailed_mutation stores detailed history."""
        self.mutation._record_detailed_mutation(
            driver_id=1,
            time=50,
            from_behaviour="LazyBehaviour",
            to_behaviour="GreedyDistanceBehaviour",
            reason="performance_low_earnings",
            avg_fare=2.5
        )
        self.assertEqual(len(self.mutation.mutation_history), 1)
        entry = self.mutation.mutation_history[0]
        self.assertEqual(entry["driver_id"], 1)
        self.assertEqual(entry["time"], 50)
        self.assertEqual(entry["from_behaviour"], "LazyBehaviour")
        self.assertEqual(entry["to_behaviour"], "GreedyDistanceBehaviour")
        self.assertEqual(entry["reason"], "performance_low_earnings")
        self.assertAlmostEqual(entry["avg_fare"], 2.5)


class TestMaybeMutatePerformanceLow(unittest.TestCase):
    """Test maybe_mutate with low earnings."""

    def setUp(self):
        """Create driver and mutation for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(low_threshold=5.0)

    def test_mutate_low_earnings_to_greedy(self):
        """Low average earnings trigger switch to GreedyDistanceBehaviour."""
        self.driver.history = [
            {"fare": 2.0},
            {"fare": 3.0},
            {"fare": 2.5},
        ]
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertIsInstance(self.driver.behaviour, GreedyDistanceBehaviour)

    def test_mutate_low_earnings_records_transition(self):
        """Low earnings mutation is recorded."""
        self.driver.history = [
            {"fare": 2.0},
            {"fare": 3.0},
            {"fare": 2.5},
        ]
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertEqual(
            self.mutation.mutation_transitions[("LazyBehaviour", "GreedyDistanceBehaviour")],
            1
        )

    def test_mutate_low_earnings_respects_cooldown(self):
        """Cooldown prevents low earnings mutation."""
        self.driver.history = [
            {"fare": 2.0},
            {"fare": 3.0},
            {"fare": 2.5},
        ]
        self.driver._last_mutation_time = 45  # Recent mutation
        original_behaviour = self.driver.behaviour
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertEqual(type(self.driver.behaviour), type(original_behaviour))


class TestMaybeMutatePerformanceHigh(unittest.TestCase):
    """Test maybe_mutate with high earnings."""

    def setUp(self):
        """Create driver and mutation for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(high_threshold=10.0)

    def test_mutate_high_earnings_to_earnings_max(self):
        """High average earnings trigger switch to EarningsMaxBehaviour."""
        self.driver.history = [
            {"fare": 12.0},
            {"fare": 13.0},
            {"fare": 11.0},
        ]
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertIsInstance(self.driver.behaviour, EarningsMaxBehaviour)

    def test_mutate_high_earnings_records_transition(self):
        """High earnings mutation is recorded."""
        self.driver.history = [
            {"fare": 12.0},
            {"fare": 13.0},
            {"fare": 11.0},
        ]
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertEqual(
            self.mutation.mutation_transitions[("LazyBehaviour", "EarningsMaxBehaviour")],
            1
        )


class TestMaybeMutateExitBehaviour(unittest.TestCase):
    """Test maybe_mutate exit conditions."""

    def setUp(self):
        """Create driver and mutation for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=GreedyDistanceBehaviour(max_distance=GREEDY_MAX_DISTANCE)
        )
        self.mutation = HybridMutation(
            low_threshold=3.0,
            high_threshold=10.0
        )

    def test_mutate_exit_greedy_recovered(self):
        """Exit GreedyDistanceBehaviour when recovered."""
        self.driver.history = [
            {"fare": 8.0},
            {"fare": 8.5},
            {"fare": 7.5},
        ]
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertIsInstance(self.driver.behaviour, LazyBehaviour)

    def test_mutate_exit_greedy_returns_early(self):
        """Exit doesn't apply performance-based mutations."""
        self.driver.history = [
            {"fare": 8.0},
            {"fare": 8.5},
            {"fare": 7.5},
        ]
        self.mutation.maybe_mutate(self.driver, 50)
        # Should be LazyBehaviour (exit), not affected by high earnings
        self.assertIsInstance(self.driver.behaviour, LazyBehaviour)


class TestMaybeMutateStagnation(unittest.TestCase):
    """Test maybe_mutate stagnation-based exploration."""

    def setUp(self):
        """Create driver and mutation for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation(
            low_threshold=2.0,
            high_threshold=15.0,
            stagnation_window=5,
            exploration_prob=1.0  # 100% chance to explore when stagnating
        )

    def test_mutate_stagnation_exploration(self):
        """Stagnating driver explores when in range."""
        # Create consistent earnings (stagnating) within normal range (not too low/high)
        self.driver.history = [
            {"fare": 8.0},
            {"fare": 8.0},
            {"fare": 8.1},
            {"fare": 7.9},
            {"fare": 8.0},
        ]
        # Verify we're in range for exploration (not triggering performance thresholds)
        avg = self.mutation._average_fare(self.driver)
        self.assertTrue(self.mutation.low_threshold < avg < self.mutation.high_threshold)
        
        # With 100% probability and stagnating earnings, should attempt to mutate
        self.mutation.maybe_mutate(self.driver, 50)
        # Check that mutation was recorded (may result in LazyBehaviour if that was random choice)
        self.assertEqual(self.driver._last_mutation_time, 50)

    def test_mutate_stagnation_low_probability(self):
        """Stagnation with low probability may not mutate."""
        self.mutation.exploration_prob = 0.0  # 0% chance
        self.driver.history = [
            {"fare": 8.0},
            {"fare": 8.0},
            {"fare": 8.1},
            {"fare": 7.9},
            {"fare": 8.0},
        ]
        original_behaviour = self.driver.behaviour
        self.mutation.maybe_mutate(self.driver, 50)
        # With 0% probability, should not explore
        self.assertEqual(type(self.driver.behaviour), type(original_behaviour))


class TestMaybeMutateNoHistory(unittest.TestCase):
    """Test maybe_mutate with insufficient history."""

    def setUp(self):
        """Create driver with no history."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
            behaviour=LazyBehaviour(idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED)
        )
        self.mutation = HybridMutation()

    def test_mutate_empty_history_no_change(self):
        """No mutation with empty history."""
        original_behaviour = self.driver.behaviour
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertEqual(type(self.driver.behaviour), type(original_behaviour))

    def test_mutate_insufficient_history_no_change(self):
        """No mutation with insufficient history."""
        self.driver.history = [{"fare": 5.0}]
        original_behaviour = self.driver.behaviour
        self.mutation.maybe_mutate(self.driver, 50)
        self.assertEqual(type(self.driver.behaviour), type(original_behaviour))


if __name__ == '__main__':
    unittest.main()
