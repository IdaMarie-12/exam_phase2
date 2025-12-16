import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from unittest.mock import Mock
from phase2.behaviours import (
    GreedyDistanceBehaviour,
    EarningsMaxBehaviour,
    LazyBehaviour,
)
from phase2.point import Point


# ====================================================================
# TEST FIXTURES (Mock Objects Setup)
# ====================================================================

class TestGreedyDistanceBehaviour(unittest.TestCase):
    """Test GreedyDistanceBehaviour strategy."""

    def setUp(self):
        """Create mock objects for each test."""
        from phase2.driver import Driver
        from phase2.offer import Offer
        
        self.behaviour = GreedyDistanceBehaviour(max_distance=5.0)
        
        # Create real Point object (not mocked - pure math class)
        self.driver_position = Point(0, 0)
        
        # Mock the Driver object (with spec for isinstance compatibility)
        self.driver = Mock(spec=Driver)
        self.driver.position = self.driver_position
        
        # Mock the Request object with pickup location
        self.request = Mock()
        self.request.pickup = Point(3, 4)  # Distance = 5.0 from driver
        
        # Mock the Offer object (with spec for isinstance compatibility)
        self.offer = Mock(spec=Offer)
        self.offer.request = self.request

    # ================================================================
    # TEST NORMAL CASES (Happy Path)
    # ================================================================

    def test_accept_offer_at_exact_threshold(self):
        """Test Accept offer when pickup distance equals max_distance."""
        # Driver at (0,0), request at (3,4) → distance = 5.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer at exact threshold")

    def test_accept_offer_within_distance(self):
        """Test Accept offer when pickup distance < max_distance."""
        self.request.pickup = Point(3, 0)  # Distance = 3.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer with pickup < threshold")

    def test_reject_offer_beyond_distance(self):
        """Test Reject offer when pickup distance > max_distance."""
        self.request.pickup = Point(10, 0)  # Distance = 10.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result, "Should reject offer beyond max_distance")

    def test_accept_zero_distance_offer(self):
        """Test: Accept offer at zero distance (already at pickup location)."""
        self.request.pickup = Point(0, 0)  # Same as driver position
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer at zero distance")

    # ================================================================
    # TEST EDGE CASES
    # ================================================================

    def test_very_large_distance_rejected(self):
        """Test Reject offer at very large distance."""
        self.request.pickup = Point(1000, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result)

    def test_small_threshold_rejects_nearby(self):
        """Test Behaviour with small threshold rejects slightly far offers."""
        strict_behaviour = GreedyDistanceBehaviour(max_distance=1.0)
        self.request.pickup = Point(2, 0)  # Distance = 2.0
        result = strict_behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result, "Strict threshold should reject")

    def test_large_threshold_accepts_far(self):
        """Test Behaviour with large threshold accepts distant offers."""
        generous_behaviour = GreedyDistanceBehaviour(max_distance=100.0)
        self.request.pickup = Point(50, 0)
        result = generous_behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Large threshold should accept")

    # ================================================================
    # TEST TYPE VALIDATION (TypeError Cases)
    # ================================================================

    def test_type_error_invalid_driver_type(self):
        """Test Raise TypeError when driver is not Driver instance."""
        with self.assertRaises(TypeError) as context:
            self.behaviour.decide("invalid_driver", self.offer, time=0)
        self.assertIn("requires Driver", str(context.exception))

    def test_type_error_invalid_offer_type(self):
        """Test Raise TypeError when offer is not Offer instance."""
        with self.assertRaises(TypeError) as context:
            self.behaviour.decide(self.driver, {}, time=0)
        self.assertIn("requires Offer", str(context.exception))

    def test_type_error_invalid_time_type(self):
        """Test Raise TypeError when time is not int. """
        with self.assertRaises(TypeError) as context:
            self.behaviour.decide(self.driver, self.offer, time="invalid")
        self.assertIn("requires int time", str(context.exception))

    def test_type_error_time_is_float(self):
        """Test Reject float time (must be int)."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(self.driver, self.offer, time=5.5)

    # ================================================================
    # TEST INITIALIZATION ERRORS
    # ================================================================

    def test_init_error_negative_distance(self):
        """Test Raise ValueError for negative max_distance."""
        with self.assertRaises(ValueError) as context:
            GreedyDistanceBehaviour(max_distance=-5.0)
        self.assertIn("must be positive", str(context.exception))

    def test_init_error_zero_distance(self):
        """Test Raise ValueError for zero max_distance."""
        with self.assertRaises(ValueError):
            GreedyDistanceBehaviour(max_distance=0.0)


# ====================================================================
# TEST EARNINGS MAX BEHAVIOUR
# ====================================================================

class TestEarningsMaxBehaviour(unittest.TestCase):
    """Test EarningsMaxBehaviour strategy."""

    def setUp(self):
        """Create mock objects for each test."""
        from phase2.driver import Driver
        from phase2.offer import Offer
        
        self.behaviour = EarningsMaxBehaviour(min_reward_per_time=10.0)
        
        self.driver = Mock(spec=Driver)
        self.driver.position = Point(0, 0)
        
        self.request = Mock()
        self.request.pickup = Point(0, 0)
        
        self.offer = Mock(spec=Offer)
        self.offer.request = self.request
        # Configure reward_per_time() to return a value
        self.offer.reward_per_time = Mock(return_value=15.0)

    # ================================================================
    # TEST NORMAL CASES
    # ================================================================

    def test_accept_offer_above_threshold(self):
        """Test Accept offer when reward/time > threshold."""
        self.offer.reward_per_time.return_value = 15.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer above threshold")

    def test_accept_offer_at_threshold(self):
        """Test Accept offer when reward/time equals threshold."""
        self.offer.reward_per_time.return_value = 10.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer at threshold")

    def test_reject_offer_below_threshold(self):
        """Test Reject offer when reward/time < threshold."""
        self.offer.reward_per_time.return_value = 5.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result, "Should reject offer below threshold")

    def test_accept_high_earnings_offer(self):
        """Test Accept very lucrative offer."""
        self.offer.reward_per_time.return_value = 100.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result)

    def test_reject_zero_earnings(self):
        """Test Reject offer with zero earnings."""
        self.offer.reward_per_time.return_value = 0.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result)

    # ================================================================
    # TEST EDGE CASES
    # ================================================================

    def test_zero_threshold_accepts_any_positive(self):
        """Zero threshold accepts any positive reward."""
        lenient_behaviour = EarningsMaxBehaviour(min_reward_per_time=0.0)
        self.offer.reward_per_time.return_value = 0.1
        result = lenient_behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result)

    def test_high_threshold_rejects_most(self):
        """High threshold rejects moderate offers."""
        strict_behaviour = EarningsMaxBehaviour(min_reward_per_time=100.0)
        self.offer.reward_per_time.return_value = 50.0
        result = strict_behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result)

    # ================================================================
    # TEST TYPE VALIDATION
    # ================================================================

    def test_type_error_invalid_driver(self):
        """Test: Raise TypeError for invalid driver."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(None, self.offer, time=0)

    def test_type_error_invalid_offer(self):
        """Test: Raise TypeError for invalid offer."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(self.driver, [], time=0)

    def test_type_error_invalid_time(self):
        """Test: Raise TypeError for non-int time."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(self.driver, self.offer, time="zero")

    # ================================================================
    # TEST INITIALIZATION ERRORS
    # ================================================================

    def test_init_error_negative_threshold(self):
        """Test: Raise ValueError for negative threshold."""
        with self.assertRaises(ValueError):
            EarningsMaxBehaviour(min_reward_per_time=-5.0)


# ====================================================================
# TEST LAZY BEHAVIOUR
# ====================================================================

class TestLazyBehaviour(unittest.TestCase):
    """Test LazyBehaviour strategy."""

    def setUp(self):
        """Create mock objects for each test."""
        from phase2.driver import Driver
        from phase2.offer import Offer
        
        self.behaviour = LazyBehaviour(idle_ticks_needed=10)
        
        self.driver = Mock(spec=Driver)
        self.driver.position = Point(0, 0)
        self.driver.idle_since = 0  # Started idle at tick 0
        
        self.request = Mock()
        self.request.pickup = Point(3, 0)  # Distance = 3.0 < 5.0
        
        self.offer = Mock(spec=Offer)
        self.offer.request = self.request

    # ================================================================
    # TEST NORMAL CASES
    # ================================================================

    def test_accept_both_conditions_met(self):
        """Accept when both idle and distance conditions are met."""
        # Current time = 10, idle_since = 0 → idle_duration = 10
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertTrue(result, "Should accept when idle >= need AND distance < 5.0")

    def test_accept_long_idle_nearby(self):
        """Accept with long idle and nearby pickup."""
        self.driver.idle_since = 0
        result = self.behaviour.decide(self.driver, self.offer, time=50)
        self.assertTrue(result)

    # ================================================================
    # TEST REJECTION CASES (Single Condition Fails)
    # ================================================================

    def test_reject_not_idle_enough(self):
        """Reject if idle time insufficient, even if nearby."""
        result = self.behaviour.decide(self.driver, self.offer, time=5)
        self.assertFalse(result, "Should reject if not idle long enough")

    def test_reject_distance_too_far(self):
        """Reject if distance too far, even if well-rested."""
        self.request.pickup = Point(6, 0)  # Distance = 6.0 > 5.0
        result = self.behaviour.decide(self.driver, self.offer, time=20)
        self.assertFalse(result, "Should reject if pickup too far")

    def test_reject_both_conditions_fail(self):
        """Reject if both idle and distance conditions fail."""
        self.request.pickup = Point(10, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=3)
        self.assertFalse(result, "Should reject if both conditions fail")

    # ================================================================
    # TEST EDGE CASES
    # ================================================================

    def test_accept_at_exact_idle_threshold(self):
        """Accept when idle exactly equals required threshold."""
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertTrue(result)

    def test_reject_just_below_idle_threshold(self):
        """Reject when idle is just below required threshold."""
        result = self.behaviour.decide(self.driver, self.offer, time=9)
        self.assertFalse(result, "Should reject at 9 when threshold is 10")

    def test_accept_at_exact_distance_boundary(self):
        """Accept when distance is just below 5.0."""
        self.request.pickup = Point(4.99, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertTrue(result)

    def test_reject_at_distance_boundary(self):
        """Reject when distance equals 5.0 (strictly < required)."""
        self.request.pickup = Point(5.0, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertFalse(result, "Distance must be < 5.0 (strict)")

    def test_zero_idle_needed_accepts_immediately(self):
        """Zero idle threshold accepts immediately if distance is OK."""
        no_rest_behaviour = LazyBehaviour(idle_ticks_needed=0)
        result = no_rest_behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result)

    def test_zero_idle_distance_fails(self):
        """Zero idle threshold still rejects if distance is too far."""
        no_rest_behaviour = LazyBehaviour(idle_ticks_needed=0)
        self.request.pickup = Point(10, 0)
        result = no_rest_behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result)

    # ================================================================
    # TEST TYPE VALIDATION
    # ================================================================

    def test_type_error_invalid_driver(self):
        """Test: Raise TypeError for invalid driver."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(123, self.offer, time=10)

    def test_type_error_invalid_offer(self):
        """Test: Raise TypeError for invalid offer."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(self.driver, "not_offer", time=10)

    def test_type_error_invalid_time(self):
        """Test: Raise TypeError for non-int time."""
        with self.assertRaises(TypeError):
            self.behaviour.decide(self.driver, self.offer, time=10.5)

    # ================================================================
    # TEST INITIALIZATION ERRORS
    # ================================================================

    def test_init_error_negative_idle(self):
        """Test: Raise ValueError for negative idle_ticks_needed."""
        with self.assertRaises(ValueError):
            LazyBehaviour(idle_ticks_needed=-5)


# ====================================================================
# INTEGRATION TEST (Optional: Real Driver + Offer with Mocks)
# ====================================================================

class TestBehaviourIntegration(unittest.TestCase):
    """Integration tests using real Point objects and mocked Driver/Offer."""

    def test_greedy_with_real_point_calculations(self):
        """Test: GreedyDistanceBehaviour with real Point distance calculation."""
        from phase2.driver import Driver
        from phase2.offer import Offer
        
        behaviour = GreedyDistanceBehaviour(max_distance=10.0)
        
        # Real Point objects
        driver_pos = Point(0, 0)
        pickup_pos = Point(6, 8)  # Actual distance = 10.0
        
        # Mock objects with real positions (use spec for isinstance)
        driver = Mock(spec=Driver)
        driver.position = driver_pos
        
        request = Mock()
        request.pickup = pickup_pos
        
        offer = Mock(spec=Offer)
        offer.request = request
        
        # Test with real distance calculation
        result = behaviour.decide(driver, offer, time=0)
        self.assertTrue(result, "Real distance calculation should work")

    def test_lazy_with_real_distance_and_time(self):
        """Test: LazyBehaviour with real Point distance and mock time."""
        from phase2.driver import Driver
        from phase2.offer import Offer
        
        behaviour = LazyBehaviour(idle_ticks_needed=5)
        
        driver = Mock(spec=Driver)
        driver.position = Point(0, 0)
        driver.idle_since = 0
        
        request = Mock()
        request.pickup = Point(2, 0)  # Distance = 2.0 < 5.0
        
        offer = Mock(spec=Offer)
        offer.request = request
        
        # Test at tick 5 (exactly idle for 5 ticks)
        result = behaviour.decide(driver, offer, time=5)
        self.assertTrue(result, "Real workflow should accept")


# ====================================================================
# MAIN - Run Tests
# ====================================================================

if __name__ == '__main__':
    # Run all tests with verbose output
    unittest.main(verbosity=2)
