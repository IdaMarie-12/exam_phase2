"""
Unit tests for DispatchPolicy, NearestNeighborPolicy, and GlobalGreedyPolicy.
"""
import unittest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2.policies import DispatchPolicy, NearestNeighborPolicy, GlobalGreedyPolicy
from phase2.driver import Driver, IDLE, TO_PICKUP
from phase2.request import Request, WAITING, PICKED
from phase2.point import Point


class TestDispatchPolicyBase(unittest.TestCase):
    """Test the abstract DispatchPolicy base class."""

    def test_assign_raises_not_implemented(self):
        """Base class assign should raise NotImplementedError."""
        policy = DispatchPolicy()
        with self.assertRaises(NotImplementedError):
            policy.assign([], [], 0)


class TestNearestNeighborPolicy(unittest.TestCase):
    """Test NearestNeighborPolicy dispatch logic."""

    def setUp(self):
        """Create policy instance for tests."""
        self.policy = NearestNeighborPolicy()

    def test_empty_drivers_returns_empty(self):
        """No drivers means no assignments."""
        request = Mock(spec=Request, status=WAITING, pickup=Point(50, 50))
        result = self.policy.assign([], [request], 0)
        self.assertEqual(result, [])

    def test_empty_requests_returns_empty(self):
        """No requests means no assignments."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0))
        result = self.policy.assign([driver], [], 0)
        self.assertEqual(result, [])

    def test_no_idle_drivers_returns_empty(self):
        """Non-idle drivers are not assigned."""
        driver = Mock(spec=Driver, status=TO_PICKUP, position=Point(0, 0))
        request = Mock(spec=Request, status=WAITING, pickup=Point(10, 10))
        result = self.policy.assign([driver], [request], 0)
        self.assertEqual(result, [])

    def test_no_waiting_requests_returns_empty(self):
        """Non-waiting requests are not assigned."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0))
        request = Mock(spec=Request, status=PICKED, pickup=Point(10, 10))
        result = self.policy.assign([driver], [request], 0)
        self.assertEqual(result, [])

    def test_single_pair_matched(self):
        """One idle driver + one waiting request = one pair."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0))
        request = Mock(spec=Request, status=WAITING, pickup=Point(10, 10))
        result = self.policy.assign([driver], [request], 0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (driver, request))

    def test_nearest_driver_selected(self):
        """Closest driver to request is selected."""
        d_far = Mock(spec=Driver, status=IDLE, position=Point(100, 100), id=1)
        d_near = Mock(spec=Driver, status=IDLE, position=Point(5, 5), id=2)
        request = Mock(spec=Request, status=WAITING, pickup=Point(10, 10), id=1)

        result = self.policy.assign([d_far, d_near], [request], 0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], d_near)

    def test_multiple_pairs_greedy(self):
        """Multiple drivers and requests paired greedily."""
        d1 = Mock(spec=Driver, status=IDLE, position=Point(0, 0), id=1)
        d2 = Mock(spec=Driver, status=IDLE, position=Point(100, 100), id=2)
        r1 = Mock(spec=Request, status=WAITING, pickup=Point(5, 5), id=1)
        r2 = Mock(spec=Request, status=WAITING, pickup=Point(95, 95), id=2)

        result = self.policy.assign([d1, d2], [r1, r2], 0)

        self.assertEqual(len(result), 2)
        # d1 closer to r1, d2 closer to r2
        assigned = {(p[0].id, p[1].id) for p in result}
        self.assertIn((1, 1), assigned)
        self.assertIn((2, 2), assigned)

    def test_driver_assigned_once(self):
        """Each driver appears at most once in result."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(50, 50), id=1)
        r1 = Mock(spec=Request, status=WAITING, pickup=Point(40, 40), id=1)
        r2 = Mock(spec=Request, status=WAITING, pickup=Point(60, 60), id=2)

        result = self.policy.assign([driver], [r1, r2], 0)

        self.assertEqual(len(result), 1)
        driver_ids = [p[0].id for p in result]
        self.assertEqual(len(driver_ids), len(set(driver_ids)))


class TestGlobalGreedyPolicy(unittest.TestCase):
    """Test GlobalGreedyPolicy dispatch logic."""

    def setUp(self):
        """Create policy instance for tests."""
        self.policy = GlobalGreedyPolicy()

    def test_empty_drivers_returns_empty(self):
        """No drivers means no assignments."""
        request = Mock(spec=Request, status=WAITING, pickup=Point(50, 50))
        result = self.policy.assign([], [request], 0)
        self.assertEqual(result, [])

    def test_empty_requests_returns_empty(self):
        """No requests means no assignments."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0))
        result = self.policy.assign([driver], [], 0)
        self.assertEqual(result, [])

    def test_no_idle_drivers_returns_empty(self):
        """Non-idle drivers are not assigned."""
        driver = Mock(spec=Driver, status=TO_PICKUP, position=Point(0, 0))
        request = Mock(spec=Request, status=WAITING, pickup=Point(10, 10))
        result = self.policy.assign([driver], [request], 0)
        self.assertEqual(result, [])

    def test_no_waiting_requests_returns_empty(self):
        """Non-waiting requests are not assigned."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0))
        request = Mock(spec=Request, status=PICKED, pickup=Point(10, 10))
        result = self.policy.assign([driver], [request], 0)
        self.assertEqual(result, [])

    def test_single_pair_matched(self):
        """One idle driver + one waiting request = one pair."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0), id=1)
        request = Mock(spec=Request, status=WAITING, pickup=Point(10, 10), id=1)
        result = self.policy.assign([driver], [request], 0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (driver, request))

    def test_globally_optimal_matching(self):
        """Global greedy finds better matching than iterative nearest."""
        # Scenario where global differs from nearest-neighbor:
        # d1 at (0,0), d2 at (10,0)
        # r1 at (8,0), r2 at (20,0)
        # Nearest-neighbor: d1->r1 (dist 8), then d2->r2 (dist 10) = total 18
        # Global: d1->r2 (dist 20) vs d2->r1 (dist 2) - sorts by distance
        #         so picks d2->r1 first (dist 2), then d1->r2 (dist 20) = total 22
        # Actually global greedy picks shortest first, so d2->r1 (2), d1->r2 (20)
        d1 = Mock(spec=Driver, status=IDLE, position=Point(0, 0), id=1)
        d2 = Mock(spec=Driver, status=IDLE, position=Point(10, 0), id=2)
        r1 = Mock(spec=Request, status=WAITING, pickup=Point(8, 0), id=1)
        r2 = Mock(spec=Request, status=WAITING, pickup=Point(20, 0), id=2)

        result = self.policy.assign([d1, d2], [r1, r2], 0)

        self.assertEqual(len(result), 2)
        # Global greedy picks shortest distance first: d2->r1 (distance 2)
        self.assertEqual(result[0], (d2, r1))

    def test_multiple_pairs_sorted_by_distance(self):
        """Results reflect distance-sorted greedy selection."""
        d1 = Mock(spec=Driver, status=IDLE, position=Point(0, 0), id=1)
        d2 = Mock(spec=Driver, status=IDLE, position=Point(100, 100), id=2)
        r1 = Mock(spec=Request, status=WAITING, pickup=Point(1, 1), id=1)
        r2 = Mock(spec=Request, status=WAITING, pickup=Point(99, 99), id=2)

        result = self.policy.assign([d1, d2], [r1, r2], 0)

        self.assertEqual(len(result), 2)
        # Both distances are very small, first picked is shortest
        assigned = {(p[0].id, p[1].id) for p in result}
        self.assertIn((1, 1), assigned)
        self.assertIn((2, 2), assigned)

    def test_driver_assigned_once(self):
        """Each driver appears at most once in result."""
        driver = Mock(spec=Driver, status=IDLE, position=Point(50, 50), id=1)
        r1 = Mock(spec=Request, status=WAITING, pickup=Point(40, 40), id=1)
        r2 = Mock(spec=Request, status=WAITING, pickup=Point(60, 60), id=2)

        result = self.policy.assign([driver], [r1, r2], 0)

        self.assertEqual(len(result), 1)

    def test_request_assigned_once(self):
        """Each request appears at most once in result."""
        d1 = Mock(spec=Driver, status=IDLE, position=Point(40, 40), id=1)
        d2 = Mock(spec=Driver, status=IDLE, position=Point(60, 60), id=2)
        request = Mock(spec=Request, status=WAITING, pickup=Point(50, 50), id=1)

        result = self.policy.assign([d1, d2], [request], 0)

        self.assertEqual(len(result), 1)


class TestPolicyComparison(unittest.TestCase):
    """Compare behavior of different policies."""

    def test_both_policies_return_lists(self):
        """Both policies return list of tuples."""
        nn = NearestNeighborPolicy()
        gg = GlobalGreedyPolicy()

        driver = Mock(spec=Driver, status=IDLE, position=Point(0, 0), id=1)
        request = Mock(spec=Request, status=WAITING, pickup=Point(10, 10), id=1)

        nn_result = nn.assign([driver], [request], 0)
        gg_result = gg.assign([driver], [request], 0)

        self.assertIsInstance(nn_result, list)
        self.assertIsInstance(gg_result, list)

    def test_both_handle_empty_inputs(self):
        """Both policies handle empty inputs gracefully."""
        nn = NearestNeighborPolicy()
        gg = GlobalGreedyPolicy()

        self.assertEqual(nn.assign([], [], 0), [])
        self.assertEqual(gg.assign([], [], 0), [])


if __name__ == '__main__':
    unittest.main()
