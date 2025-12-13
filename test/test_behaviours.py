"""
Comprehensive Unit Tests for Driver Behaviour Strategies

This module tests three behaviour classes using unittest, mock, and patch:
    - GreedyDistanceBehaviour: Accepts if pickup distance <= threshold
    - EarningsMaxBehaviour: Accepts if reward/time >= threshold
    - LazyBehaviour: Accepts if idle time >= threshold AND distance < 5.0

Testing Approach:
    1. Mock Driver, Offer, Request objects to isolate behaviour logic
    2. Test normal cases, edge cases, and error cases
    3. Patch random/datetime if needed (future extension)
    4. Verify type validation raises TypeError as expected

Run tests with:
    $ python -m unittest test.test_behaviours -v
    $ python -m unittest discover -s test -p test_behaviours.py
    $ python test/test_behaviours.py
"""

# Ensure phase2 module can be imported (whether running via unittest or directly)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from unittest.mock import Mock
from phase2.behaviours import (
    GreedyDistanceBehaviour,
    EarningsMaxBehaviour,
    LazyBehaviour,
    LAZY_MAX_PICKUP_DISTANCE
)
from phase2.point import Point


# ====================================================================
# TEST FIXTURES (Mock Objects Setup)
# ====================================================================

class TestGreedyDistanceBehaviour(unittest.TestCase):
    """Test suite for GreedyDistanceBehaviour strategy.
    
    GreedyDistanceBehaviour accepts offers if the pickup location is
    within max_distance units of the driver's current position.
    
    Complexity: O(1) - Only checks one distance comparison
    """

    def setUp(self):
        """Create reusable mock objects for each test.
        
        Fixtures created:
            - behaviour: GreedyDistanceBehaviour with threshold of 5.0 units
            - driver_mock: Mock driver at position (0, 0)
            - offer_mock: Mock offer with request at varying distances
            - request_mock: Mock request with pickup location
        """
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
        """Test: Accept offer when pickup distance equals max_distance.
        
        Input: distance = 5.0 (exactly at threshold)
        Expected: True (accept)
        
        Why: The condition is distance <= threshold, so equality should accept.
        """
        # Driver at (0,0), request at (3,4) → distance = 5.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer at exact threshold")

    def test_accept_offer_within_distance(self):
        """Test: Accept offer when pickup distance < max_distance.
        
        Input: distance = 3.0 (less than threshold of 5.0)
        Expected: True (accept)
        
        Why: Short distances are attractive for pragmatic drivers.
        """
        self.request.pickup = Point(3, 0)  # Distance = 3.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer with pickup < threshold")

    def test_reject_offer_beyond_distance(self):
        """Test: Reject offer when pickup distance > max_distance.
        
        Input: distance = 10.0 (greater than threshold of 5.0)
        Expected: False (reject)
        
        Why: Long distances are unattractive for pragmatic drivers.
        """
        self.request.pickup = Point(10, 0)  # Distance = 10.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result, "Should reject offer beyond max_distance")

    def test_accept_zero_distance_offer(self):
        """Test: Accept offer at zero distance (already at pickup location).
        
        Input: distance = 0.0
        Expected: True (accept)
        
        Why: Distance 0 is definitely within threshold.
        """
        self.request.pickup = Point(0, 0)  # Same as driver position
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer at zero distance")

    # ================================================================
    # TEST EDGE CASES
    # ================================================================

    def test_very_large_distance_rejected(self):
        """Test: Reject offer at very large distance.
        
        Input: distance = 1000.0
        Expected: False (reject)
        
        Why: Verify threshold works at far distances.
        """
        self.request.pickup = Point(1000, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result)

    def test_small_threshold_rejects_nearby(self):
        """Test: Behaviour with small threshold rejects slightly far offers.
        
        Input: Small behaviour (threshold=1.0), distance=2.0
        Expected: False (reject)
        
        Why: Verify different thresholds work independently.
        """
        strict_behaviour = GreedyDistanceBehaviour(max_distance=1.0)
        self.request.pickup = Point(2, 0)  # Distance = 2.0
        result = strict_behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result, "Strict threshold should reject")

    def test_large_threshold_accepts_far(self):
        """Test: Behaviour with large threshold accepts distant offers.
        
        Input: Generous behaviour (threshold=100.0), distance=50.0
        Expected: True (accept)
        
        Why: Verify thresholds are configurable.
        """
        generous_behaviour = GreedyDistanceBehaviour(max_distance=100.0)
        self.request.pickup = Point(50, 0)
        result = generous_behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Large threshold should accept")

    # ================================================================
    # TEST TYPE VALIDATION (TypeError Cases)
    # ================================================================

    def test_type_error_invalid_driver_type(self):
        """Test: Raise TypeError when driver is not Driver instance.
        
        Input: driver = "not a driver object"
        Expected: TypeError with clear message
        
        Why: Type checking prevents cryptic AttributeError later.
             Code explicitly validates input types.
        """
        with self.assertRaises(TypeError) as context:
            self.behaviour.decide("invalid_driver", self.offer, time=0)
        self.assertIn("requires Driver", str(context.exception))

    def test_type_error_invalid_offer_type(self):
        """Test: Raise TypeError when offer is not Offer instance.
        
        Input: offer = {}
        Expected: TypeError with clear message
        
        Why: Type checking prevents AttributeError on offer.request.
        """
        with self.assertRaises(TypeError) as context:
            self.behaviour.decide(self.driver, {}, time=0)
        self.assertIn("requires Offer", str(context.exception))

    def test_type_error_invalid_time_type(self):
        """Test: Raise TypeError when time is not int.
        
        Input: time = "not_an_int"
        Expected: TypeError
        
        Why: Type checking for all parameters ensures consistency.
        """
        with self.assertRaises(TypeError) as context:
            self.behaviour.decide(self.driver, self.offer, time="invalid")
        self.assertIn("requires int time", str(context.exception))

    def test_type_error_time_is_float(self):
        """Test: Reject float time (must be int).
        
        Input: time = 5.5
        Expected: TypeError
        
        Why: Simulation uses discrete ticks (integers).
        """
        with self.assertRaises(TypeError):
            self.behaviour.decide(self.driver, self.offer, time=5.5)

    # ================================================================
    # TEST INITIALIZATION ERRORS
    # ================================================================

    def test_init_error_negative_distance(self):
        """Test: Raise ValueError for negative max_distance.
        
        Input: max_distance = -5.0
        Expected: ValueError
        
        Why: Negative distance makes no sense.
        """
        with self.assertRaises(ValueError) as context:
            GreedyDistanceBehaviour(max_distance=-5.0)
        self.assertIn("must be positive", str(context.exception))

    def test_init_error_zero_distance(self):
        """Test: Raise ValueError for zero max_distance.
        
        Input: max_distance = 0.0
        Expected: ValueError
        
        Why: Driver must accept some distance.
        """
        with self.assertRaises(ValueError):
            GreedyDistanceBehaviour(max_distance=0.0)


# ====================================================================
# TEST EARNINGS MAX BEHAVIOUR
# ====================================================================

class TestEarningsMaxBehaviour(unittest.TestCase):
    """Test suite for EarningsMaxBehaviour strategy.
    
    EarningsMaxBehaviour accepts offers if:
        reward / travel_time >= min_reward_per_time
    
    This maximizes hourly earnings regardless of distance.
    
    Complexity: O(1) - Only checks one ratio comparison
    """

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
        """Test: Accept offer when reward/time > threshold.
        
        Input: reward_per_time = 15.0, threshold = 10.0
        Expected: True (accept)
        
        Why: High earnings per time unit is good.
        """
        self.offer.reward_per_time.return_value = 15.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer above threshold")

    def test_accept_offer_at_threshold(self):
        """Test: Accept offer when reward/time equals threshold.
        
        Input: reward_per_time = 10.0, threshold = 10.0
        Expected: True (accept)
        
        Why: Exactly meeting threshold is acceptable.
        """
        self.offer.reward_per_time.return_value = 10.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result, "Should accept offer at threshold")

    def test_reject_offer_below_threshold(self):
        """Test: Reject offer when reward/time < threshold.
        
        Input: reward_per_time = 5.0, threshold = 10.0
        Expected: False (reject)
        
        Why: Low earnings per time unit is inefficient.
        """
        self.offer.reward_per_time.return_value = 5.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result, "Should reject offer below threshold")

    def test_accept_high_earnings_offer(self):
        """Test: Accept very lucrative offer.
        
        Input: reward_per_time = 100.0, threshold = 10.0
        Expected: True (accept)
        
        Why: Very high earnings should always be accepted.
        """
        self.offer.reward_per_time.return_value = 100.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result)

    def test_reject_zero_earnings(self):
        """Test: Reject offer with zero earnings.
        
        Input: reward_per_time = 0.0, threshold = 10.0
        Expected: False (reject)
        
        Why: No payment means no incentive.
        """
        self.offer.reward_per_time.return_value = 0.0
        result = self.behaviour.decide(self.driver, self.offer, time=0)
        self.assertFalse(result)

    # ================================================================
    # TEST EDGE CASES
    # ================================================================

    def test_zero_threshold_accepts_any_positive(self):
        """Test: Zero threshold accepts any positive reward.
        
        Input: threshold = 0.0, reward_per_time = 0.1
        Expected: True (accept)
        
        Why: Verify threshold comparison works at boundary.
        """
        lenient_behaviour = EarningsMaxBehaviour(min_reward_per_time=0.0)
        self.offer.reward_per_time.return_value = 0.1
        result = lenient_behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result)

    def test_high_threshold_rejects_most(self):
        """Test: High threshold rejects moderate offers.
        
        Input: threshold = 100.0, reward_per_time = 50.0
        Expected: False (reject)
        
        Why: Verify high thresholds filter effectively.
        """
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
        """Test: Raise ValueError for negative threshold.
        
        Input: min_reward_per_time = -5.0
        Expected: ValueError
        
        Why: Negative reward doesn't make sense.
        """
        with self.assertRaises(ValueError):
            EarningsMaxBehaviour(min_reward_per_time=-5.0)


# ====================================================================
# TEST LAZY BEHAVIOUR
# ====================================================================

class TestLazyBehaviour(unittest.TestCase):
    """Test suite for LazyBehaviour strategy.
    
    LazyBehaviour accepts offers ONLY IF:
        1. Driver has been idle >= idle_ticks_needed, AND
        2. Pickup distance < LAZY_MAX_PICKUP_DISTANCE (5.0)
    
    Both conditions must be true - it's a strict AND check.
    
    Complexity: O(1) - Two comparisons
    """

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
        """Test: Accept when both idle AND distance are good.
        
        Input: 
            - idle_duration = 10 (exactly meets need)
            - distance = 3.0 (< 5.0 threshold)
        Expected: True (accept)
        
        Why: Both conditions satisfied means rest + nearby job.
        """
        # Current time = 10, idle_since = 0 → idle_duration = 10
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertTrue(result, "Should accept when idle >= need AND distance < 5.0")

    def test_accept_long_idle_nearby(self):
        """Test: Accept with long idle and nearby pickup.
        
        Input:
            - idle_duration = 50 (much more than needed 10)
            - distance = 2.0 (well within 5.0)
        Expected: True (accept)
        
        Why: Driver is well-rested and destination is very close.
        """
        self.driver.idle_since = 0
        result = self.behaviour.decide(self.driver, self.offer, time=50)
        self.assertTrue(result)

    # ================================================================
    # TEST REJECTION CASES (Single Condition Fails)
    # ================================================================

    def test_reject_not_idle_enough(self):
        """Test: Reject if idle time insufficient (even if nearby).
        
        Input:
            - idle_duration = 5 (< 10 needed)
            - distance = 2.0 (< 5.0, OK)
        Expected: False (reject)
        
        Why: Driver needs more rest (time=5, idle_since=0 → idle=5 < 10).
             Distance is fine, but idle condition fails.
        """
        result = self.behaviour.decide(self.driver, self.offer, time=5)
        self.assertFalse(result, "Should reject if not idle long enough")

    def test_reject_distance_too_far(self):
        """Test: Reject if distance too far (even if well-rested).
        
        Input:
            - idle_duration = 20 (> 10, OK)
            - distance = 6.0 (> 5.0 threshold)
        Expected: False (reject)
        
        Why: Distance is too far (distance=6.0 >= 5.0 threshold).
             Idle time is fine, but distance condition fails.
        """
        self.request.pickup = Point(6, 0)  # Distance = 6.0 > 5.0
        result = self.behaviour.decide(self.driver, self.offer, time=20)
        self.assertFalse(result, "Should reject if pickup too far")

    def test_reject_both_conditions_fail(self):
        """Test: Reject if BOTH conditions fail.
        
        Input:
            - idle_duration = 3 (< 10, fails)
            - distance = 10.0 (> 5.0, fails)
        Expected: False (reject)
        
        Why: Neither condition is satisfied.
        """
        self.request.pickup = Point(10, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=3)
        self.assertFalse(result, "Should reject if both conditions fail")

    # ================================================================
    # TEST EDGE CASES
    # ================================================================

    def test_accept_at_exact_idle_threshold(self):
        """Test: Accept when idle exactly equals required (boundary).
        
        Input: idle_duration = 10 (exactly equals need)
        Expected: True (accept)
        
        Why: >= is inclusive, so equality should accept.
        """
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertTrue(result)

    def test_reject_just_below_idle_threshold(self):
        """Test: Reject when idle is 1 tick short.
        
        Input: idle_duration = 9 (one below 10)
        Expected: False (reject)
        
        Why: Boundary check: 9 < 10 fails.
        """
        result = self.behaviour.decide(self.driver, self.offer, time=9)
        self.assertFalse(result, "Should reject at 9 when threshold is 10")

    def test_accept_at_exact_distance_boundary(self):
        """Test: Accept when distance < 5.0 (just barely).
        
        Input: distance = 4.99
        Expected: True (accept)
        
        Why: Boundary: 4.99 < 5.0 is true.
        """
        self.request.pickup = Point(4.99, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertTrue(result)

    def test_reject_at_distance_boundary(self):
        """Test: Reject when distance equals 5.0 (at boundary).
        
        Input: distance = 5.0
        Expected: False (reject)
        
        Why: Condition is < (not <=), so 5.0 fails.
        """
        self.request.pickup = Point(5.0, 0)
        result = self.behaviour.decide(self.driver, self.offer, time=10)
        self.assertFalse(result, "Distance must be < 5.0 (strict)")

    def test_zero_idle_needed_accepts_immediately(self):
        """Test: Zero idle threshold accepts right away (if distance OK).
        
        Input: idle_ticks_needed = 0, current_time = 0
        Expected: True (accept)
        
        Why: No rest required → driver accepts immediately.
        """
        no_rest_behaviour = LazyBehaviour(idle_ticks_needed=0)
        result = no_rest_behaviour.decide(self.driver, self.offer, time=0)
        self.assertTrue(result)

    def test_zero_idle_distance_fails(self):
        """Test: Zero idle threshold still respects distance.
        
        Input: idle_ticks_needed = 0, distance = 10.0
        Expected: False (reject)
        
        Why: Even with no rest needed, distance > 5.0 fails.
        """
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
        """Test: Raise ValueError for negative idle_ticks_needed.
        
        Input: idle_ticks_needed = -5
        Expected: ValueError
        
        Why: Negative idle time doesn't make sense.
        """
        with self.assertRaises(ValueError):
            LazyBehaviour(idle_ticks_needed=-5)


# ====================================================================
# INTEGRATION TEST (Optional: Real Driver + Offer with Mocks)
# ====================================================================

class TestBehaviourIntegration(unittest.TestCase):
    """Integration tests using real Point objects and mocked Driver/Offer.
    
    These tests verify behaviour works with real coordinate calculations.
    """

    def test_greedy_with_real_point_calculations(self):
        """Test: GreedyDistanceBehaviour with real Point distance calculation.
        
        This is a light integration test using:
            - Real Point class (actual distance_to() method)
            - Mock Driver/Offer (but with real position)
        
        Purpose: Verify behaviour works with actual distance calculation.
        """
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
        """Test: LazyBehaviour with real Point distance and mock time.
        
        Purpose: Full workflow with real geometry but controlled time.
        """
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
