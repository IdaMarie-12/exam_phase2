import unittest
from phase2.driver import Driver, IDLE, TO_PICKUP, TO_DROPOFF
from phase2.point import Point
from phase2.request import Request, WAITING, ASSIGNED, PICKED, DELIVERED
from phase2.helpers_2.core_helpers import (
    is_at_target,
    move_towards,
    record_assignment_start,
    record_completion,
)


def calculate_points(fare: float, wait_time: int) -> float:
    """Calculate driver points: max(0, fare - 0.1 * wait_time)."""
    return max(0.0, fare - 0.1 * wait_time)


class TestPointHelpers(unittest.TestCase):
    """Test Point helper functions."""

    def test_is_at_target_exact_match(self):
        """Driver is at target when positions are identical."""
        p1 = Point(5.0, 5.0)
        p2 = Point(5.0, 5.0)
        self.assertTrue(is_at_target(p1, p2))

    def test_is_at_target_within_epsilon(self):
        """Driver is at target when distance is within epsilon tolerance."""
        p1 = Point(5.0, 5.0)
        p2 = Point(5.0, 5.0 + 1e-10)  # Much less than EPSILON (1e-9)
        self.assertTrue(is_at_target(p1, p2))

    def test_is_at_target_outside_epsilon(self):
        """Driver is NOT at target when distance exceeds epsilon."""
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 0.0)
        self.assertFalse(is_at_target(p1, p2))

    def test_is_at_target_custom_tolerance(self):
        """is_at_target respects custom tolerance parameter."""
        p1 = Point(0.0, 0.0)
        p2 = Point(0.5, 0.0)
        self.assertFalse(is_at_target(p1, p2, tolerance=0.1))
        self.assertTrue(is_at_target(p1, p2, tolerance=1.0))

    def test_move_towards_zero_distance(self):
        """Moving zero distance returns current position."""
        current = Point(0.0, 0.0)
        target = Point(10.0, 0.0)
        result = move_towards(current, target, 0.0)
        self.assertEqual(result, current)

    def test_move_towards_partial_distance(self):
        """Moving partial distance interpolates correctly."""
        current = Point(0.0, 0.0)
        target = Point(10.0, 0.0)
        result = move_towards(current, target, 5.0)
        self.assertEqual(result.x, 5.0)
        self.assertEqual(result.y, 0.0)

    def test_move_towards_exact_distance(self):
        """Moving exact distance reaches target."""
        current = Point(0.0, 0.0)
        target = Point(10.0, 0.0)
        result = move_towards(current, target, 10.0)
        self.assertAlmostEqual(result.x, 10.0, places=9)
        self.assertAlmostEqual(result.y, 0.0, places=9)

    def test_move_towards_overshooting_prevented(self):
        """Moving more than target distance doesn't overshoot."""
        current = Point(0.0, 0.0)
        target = Point(10.0, 0.0)
        result = move_towards(current, target, 20.0)
        # Should be clamped at target
        self.assertAlmostEqual(result.x, 10.0, places=9)
        self.assertAlmostEqual(result.y, 0.0, places=9)

    def test_move_towards_diagonal(self):
        """Moving towards diagonal target works correctly."""
        current = Point(0.0, 0.0)
        target = Point(3.0, 4.0)  # Distance = 5.0
        result = move_towards(current, target, 2.5)
        # Should move halfway (2.5 / 5.0 = 0.5 of the way)
        self.assertAlmostEqual(result.x, 1.5, places=9)
        self.assertAlmostEqual(result.y, 2.0, places=9)

    def test_move_towards_already_at_target(self):
        """Moving when already at target returns a copy of current."""
        current = Point(5.0, 5.0)
        target = Point(5.0, 5.0)
        result = move_towards(current, target, 10.0)
        self.assertEqual(result.x, current.x)
        self.assertEqual(result.y, current.y)

    def test_move_towards_negative_distance_raises(self):
        """Negative distance raises ValueError."""
        current = Point(0.0, 0.0)
        target = Point(10.0, 0.0)
        with self.assertRaises(ValueError):
            move_towards(current, target, -1.0)


class TestHistoryRecording(unittest.TestCase):
    """Test history recording helpers."""

    def test_record_assignment_start(self):
        """record_assignment_start creates correct history entry."""
        history = []
        record_assignment_start(history, request_id=42, current_time=100)
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["request_id"], 42)
        self.assertEqual(history[0]["start_time"], 100)

    def test_record_assignment_start_multiple(self):
        """Multiple assignments append to history."""
        history = []
        record_assignment_start(history, 1, 10)
        record_assignment_start(history, 2, 20)
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["request_id"], 2)

    def test_record_completion(self):
        """record_completion creates complete history entry."""
        history = []
        record_completion(
            history,
            request_id=42,
            creation_time=0,
            time=100,
            fare=15.5,
            wait=25
        )
        
        self.assertEqual(len(history), 1)
        entry = history[0]
        self.assertEqual(entry["request_id"], 42)
        self.assertEqual(entry["time"], 100)
        self.assertEqual(entry["fare"], 15.5)
        self.assertEqual(entry["wait"], 25)
        self.assertEqual(entry["start_time"], 0)

    def test_record_completion_multiple(self):
        """Multiple completions create separate entries."""
        history = []
        record_completion(history, 1, 0, 50, 10.0, 10)
        record_completion(history, 2, 50, 100, 15.0, 15)
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["fare"], 10.0)
        self.assertEqual(history[1]["fare"], 15.0)


class TestCalculatePoints(unittest.TestCase):
    """Test points calculation logic."""

    def test_calculate_points_basic(self):
        """Points = fare - 0.1 * wait_time."""
        points = calculate_points(fare=10.0, wait_time=5)
        self.assertAlmostEqual(points, 9.5)

    def test_calculate_points_no_wait(self):
        """No wait time means full points."""
        points = calculate_points(fare=10.0, wait_time=0)
        self.assertAlmostEqual(points, 10.0)

    def test_calculate_points_heavy_wait_penalty(self):
        """Heavy wait time reduces points significantly."""
        points = calculate_points(fare=10.0, wait_time=100)
        self.assertAlmostEqual(points, 0.0)  # 10.0 - 0.1*100 = 0

    def test_calculate_points_negative_clamped_to_zero(self):
        """Negative points are clamped to zero."""
        points = calculate_points(fare=5.0, wait_time=100)
        self.assertAlmostEqual(points, 0.0)  # max(0, 5.0 - 10.0) = 0

    def test_calculate_points_fractional(self):
        """Points calculation works with fractional values."""
        points = calculate_points(fare=7.5, wait_time=3)
        self.assertAlmostEqual(points, 7.2)


class TestDriverBasics(unittest.TestCase):
    """Test basic Driver functionality."""

    def setUp(self):
        """Create a driver for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )

    def test_driver_creation(self):
        """Driver is created in IDLE state."""
        self.assertEqual(self.driver.id, 1)
        self.assertEqual(self.driver.status, IDLE)
        self.assertEqual(self.driver.position, Point(0.0, 0.0))
        self.assertIsNone(self.driver.current_request)
        self.assertEqual(self.driver.earnings, 0.0)

    def test_driver_is_idle_true(self):
        """is_idle returns True when driver is IDLE and not assigned."""
        self.assertTrue(self.driver.is_idle())

    def test_driver_is_idle_false_with_request(self):
        """is_idle returns False when driver has current_request."""
        request = Request(
            id=1,
            pickup=Point(5.0, 5.0),
            dropoff=Point(10.0, 10.0),
            creation_time=0
        )
        self.driver.assign_request(request, current_time=0)
        self.assertFalse(self.driver.is_idle())


class TestDriverAssignment(unittest.TestCase):
    """Test driver request assignment."""

    def setUp(self):
        """Create driver and request for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )
        self.request = Request(
            id=42,
            pickup=Point(5.0, 5.0),
            dropoff=Point(15.0, 15.0),
            creation_time=0
        )

    def test_assign_request_changes_status(self):
        """Assigning request changes driver status to TO_PICKUP."""
        self.driver.assign_request(self.request, current_time=10)
        self.assertEqual(self.driver.status, TO_PICKUP)
        self.assertEqual(self.driver.current_request.id, 42)

    def test_assign_request_marks_request_assigned(self):
        """Assigning request marks request as ASSIGNED."""
        self.driver.assign_request(self.request, current_time=10)
        self.assertEqual(self.request.status, ASSIGNED)
        self.assertEqual(self.request.assigned_driver_id, 1)

    def test_assign_request_clears_idle_since(self):
        """Assigning request clears idle_since."""
        self.driver.idle_since = 5
        self.driver.assign_request(self.request, current_time=10)
        self.assertIsNone(self.driver.idle_since)

    def test_assign_request_records_history(self):
        """Assigning request records start in history."""
        self.driver.assign_request(self.request, current_time=10)
        self.assertEqual(len(self.driver.history), 1)
        self.assertEqual(self.driver.history[0]["request_id"], 42)
        self.assertEqual(self.driver.history[0]["start_time"], 10)


class TestDriverTargetPoint(unittest.TestCase):
    """Test driver target point detection."""

    def setUp(self):
        """Create driver and request."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )
        self.request = Request(
            id=42,
            pickup=Point(5.0, 5.0),
            dropoff=Point(15.0, 15.0),
            creation_time=0
        )

    def test_target_point_idle(self):
        """Idle driver has no target."""
        target = self.driver.target_point()
        self.assertIsNone(target)

    def test_target_point_to_pickup(self):
        """TO_PICKUP driver targets pickup location."""
        self.driver.assign_request(self.request, current_time=0)
        target = self.driver.target_point()
        self.assertEqual(target, Point(5.0, 5.0))

    def test_target_point_to_dropoff(self):
        """TO_DROPOFF driver targets dropoff location."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.status = TO_DROPOFF
        target = self.driver.target_point()
        self.assertEqual(target, Point(15.0, 15.0))


class TestDriverMovement(unittest.TestCase):
    """Test driver step and movement."""

    def setUp(self):
        """Create driver and request."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=5.0,  # Move 5 units per time unit
        )
        self.request = Request(
            id=42,
            pickup=Point(10.0, 0.0),
            dropoff=Point(20.0, 0.0),
            creation_time=0
        )

    def test_step_idle_no_movement(self):
        """Step on idle driver causes no movement."""
        original_pos = self.driver.position
        self.driver.step(dt=1.0)
        self.assertEqual(self.driver.position, original_pos)

    def test_step_towards_target(self):
        """Step moves driver towards target."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.step(dt=1.0)  # Move 5 units toward (10, 0)
        self.assertAlmostEqual(self.driver.position.x, 5.0, places=9)
        self.assertEqual(self.driver.position.y, 0.0)

    def test_step_multiple_times(self):
        """Multiple steps accumulate movement."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.step(dt=0.5)  # Move 2.5 units
        self.driver.step(dt=0.5)  # Move 2.5 more units
        self.assertAlmostEqual(self.driver.position.x, 5.0, places=9)

    def test_step_with_different_speeds(self):
        """Step distance depends on speed."""
        self.driver.speed = 10.0
        self.driver.assign_request(self.request, current_time=0)
        self.driver.step(dt=1.0)  # Move 10 units
        self.assertAlmostEqual(self.driver.position.x, 10.0, places=9)

    def test_step_prevents_overshoot(self):
        """Step doesn't overshoot target."""
        self.driver.speed = 100.0  # Very fast
        self.driver.assign_request(self.request, current_time=0)
        self.driver.step(dt=1.0)  # Would move 100 units, but only 10 away
        self.assertAlmostEqual(self.driver.position.x, 10.0, places=9)
        self.assertAlmostEqual(self.driver.position.y, 0.0, places=9)


class TestDriverPickupAndDropoff(unittest.TestCase):
    """Test driver pickup and dropoff operations."""

    def setUp(self):
        """Create driver and request."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )
        self.request = Request(
            id=42,
            pickup=Point(5.0, 5.0),
            dropoff=Point(15.0, 15.0),
            creation_time=0
        )

    def test_complete_pickup_transitions_status(self):
        """Completing pickup transitions to TO_DROPOFF."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.assertEqual(self.driver.status, TO_DROPOFF)

    def test_complete_pickup_marks_request(self):
        """Completing pickup marks request as PICKED."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.assertEqual(self.request.status, PICKED)
        self.assertEqual(self.request.wait_time, 10)

    def test_complete_pickup_no_request(self):
        """complete_pickup with no request does nothing."""
        # Should not raise, just return
        self.driver.complete_pickup(time=10)
        self.assertEqual(self.driver.status, IDLE)

    def test_complete_dropoff_marks_request(self):
        """Completing dropoff marks request as DELIVERED."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.driver.complete_dropoff(time=20)
        self.assertEqual(self.request.status, DELIVERED)

    def test_complete_dropoff_updates_earnings(self):
        """Completing dropoff updates driver earnings."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.driver.complete_dropoff(time=20)
        # Distance from (5,5) to (15,15) = sqrt(200) ≈ 14.14
        expected_earnings = self.request.pickup.distance_to(self.request.dropoff)
        self.assertAlmostEqual(self.driver.earnings, expected_earnings, places=9)

    def test_complete_dropoff_resets_status(self):
        """Completing dropoff resets driver to IDLE."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.driver.complete_dropoff(time=20)
        self.assertEqual(self.driver.status, IDLE)
        self.assertIsNone(self.driver.current_request)

    def test_complete_dropoff_sets_idle_since(self):
        """Completing dropoff sets idle_since timestamp."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.driver.complete_dropoff(time=20)
        self.assertEqual(self.driver.idle_since, 20)

    def test_complete_dropoff_records_history(self):
        """Completing dropoff records completion in history."""
        self.driver.assign_request(self.request, current_time=0)
        self.driver.complete_pickup(time=10)
        self.driver.complete_dropoff(time=20)
        # Should have 2 entries: assignment and completion
        self.assertEqual(len(self.driver.history), 2)
        completion = self.driver.history[1]
        self.assertEqual(completion["request_id"], 42)
        self.assertEqual(completion["time"], 20)
        # wait_time is calculated as time - creation_time = 20 - 0 = 20
        self.assertEqual(completion["wait"], 20)

    def test_complete_dropoff_no_request(self):
        """complete_dropoff with no request does nothing."""
        self.driver.complete_dropoff(time=20)
        self.assertEqual(self.driver.status, IDLE)
        self.assertEqual(self.driver.earnings, 0.0)


class TestDriverFullCycle(unittest.TestCase):
    """Test complete driver request lifecycle."""

    def test_full_delivery_cycle(self):
        """Complete assignment → pickup → dropoff cycle."""
        driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=5.0,
        )
        request = Request(
            id=42,
            pickup=Point(10.0, 0.0),
            dropoff=Point(20.0, 0.0),
            creation_time=0
        )

        # Assign request
        driver.assign_request(request, current_time=0)
        self.assertEqual(driver.status, TO_PICKUP)
        self.assertEqual(request.status, ASSIGNED)

        # Move to pickup (10 units away, 5 units/time = 2 time units)
        driver.step(dt=1.0)
        driver.step(dt=1.0)
        self.assertAlmostEqual(driver.position.x, 10.0, places=9)

        # Complete pickup
        driver.complete_pickup(time=2)
        self.assertEqual(driver.status, TO_DROPOFF)
        self.assertEqual(request.status, PICKED)

        # Move to dropoff (10 units away, 5 units/time = 2 more time units)
        driver.step(dt=1.0)
        driver.step(dt=1.0)
        self.assertAlmostEqual(driver.position.x, 20.0, places=9)

        # Complete dropoff
        driver.complete_dropoff(time=4)
        self.assertEqual(driver.status, IDLE)
        self.assertEqual(request.status, DELIVERED)
        self.assertEqual(driver.earnings, 10.0)  # Distance from pickup to dropoff

    def test_multiple_deliveries(self):
        """Driver can complete multiple deliveries."""
        driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )

        # First request
        req1 = Request(
            id=1,
            pickup=Point(5.0, 0.0),
            dropoff=Point(10.0, 0.0),
            creation_time=0
        )
        driver.assign_request(req1, current_time=0)
        driver.complete_pickup(time=5)
        driver.complete_dropoff(time=10)
        earnings_after_1 = driver.earnings

        # Second request
        req2 = Request(
            id=2,
            pickup=Point(15.0, 0.0),
            dropoff=Point(20.0, 0.0),
            creation_time=10
        )
        driver.assign_request(req2, current_time=10)
        driver.complete_pickup(time=15)
        driver.complete_dropoff(time=20)

        # Check history has both deliveries
        self.assertEqual(len(driver.history), 4)  # 2 assignments + 2 completions
        self.assertGreater(driver.earnings, earnings_after_1)


if __name__ == '__main__':
    unittest.main()
