import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2.generator import RequestGenerator, _generate_poisson
from phase2.request import Request
from phase2.point import Point


class TestGeneratePoisson(unittest.TestCase):
    """Test Poisson random number generator."""

    def test_negative_rate_raises_error(self):
        """Negative rate should raise ValueError."""
        with self.assertRaises(ValueError):
            _generate_poisson(-1.0)

    def test_zero_rate_returns_zero(self):
        """Rate of 0 should always return 0."""
        result = _generate_poisson(0)
        self.assertEqual(result, 0)

    def test_returns_integer(self):
        """Result should be an integer."""
        result = _generate_poisson(2.0)
        self.assertIsInstance(result, int)

    def test_returns_non_negative(self):
        """Result should always be >= 0."""
        for _ in range(20):
            result = _generate_poisson(2.0)
            self.assertGreaterEqual(result, 0)

    @patch('phase2.generator.random.random')
    def test_with_mocked_random(self, mock_random):
        """Test Poisson with controlled random values."""
        mock_random.side_effect = [0.5, 0.1]
        result = _generate_poisson(1.0)
        self.assertEqual(result, 1)


class TestRequestGeneratorInit(unittest.TestCase):
    """Test RequestGenerator initialization and validation."""

    def test_negative_rate_raises_error(self):
        """Negative rate should raise ValueError."""
        with self.assertRaises(ValueError):
            RequestGenerator(rate=-1.0, width=100, height=100)

    def test_zero_width_raises_error(self):
        """Zero width should raise ValueError."""
        with self.assertRaises(ValueError):
            RequestGenerator(rate=1.0, width=0, height=100)

    def test_zero_height_raises_error(self):
        """Zero height should raise ValueError."""
        with self.assertRaises(ValueError):
            RequestGenerator(rate=1.0, width=100, height=0)

    def test_valid_parameters(self):
        """Valid parameters should initialize correctly."""
        gen = RequestGenerator(rate=2.5, width=50, height=75, start_id=10)
        self.assertEqual(gen.rate, 2.5)
        self.assertEqual(gen.width, 50)
        self.assertEqual(gen.height, 75)
        self.assertEqual(gen.next_id, 10)
        self.assertTrue(gen.enabled)

    def test_disabled_generator(self):
        """Generator can be disabled."""
        gen = RequestGenerator(rate=1.0, width=100, height=100, enabled=False)
        self.assertFalse(gen.enabled)


class TestMaybeGenerate(unittest.TestCase):
    """Test RequestGenerator.maybe_generate method."""

    def test_disabled_returns_empty(self):
        """Disabled generator returns empty list."""
        gen = RequestGenerator(rate=5.0, width=100, height=100, enabled=False)
        result = gen.maybe_generate(time=10)
        self.assertEqual(result, [])

    def test_zero_rate_returns_empty(self):
        """Zero rate produces no requests."""
        gen = RequestGenerator(rate=0, width=100, height=100)
        result = gen.maybe_generate(time=0)
        self.assertEqual(result, [])

    def test_returns_list(self):
        """Should return a list."""
        gen = RequestGenerator(rate=2.0, width=100, height=100)
        result = gen.maybe_generate(time=0)
        self.assertIsInstance(result, list)

    @patch('phase2.generator._generate_poisson')
    @patch('phase2.generator.random.uniform')
    def test_generate_with_mocked_randomness(self, mock_uniform, mock_poisson):
        """Test generation with fully controlled random behavior."""
        # Force exactly 1 request
        mock_poisson.return_value = 1
        # Mock: pickup (10, 20), dropoff (30, 40)
        mock_uniform.side_effect = [10.0, 20.0, 30.0, 40.0]

        gen = RequestGenerator(rate=1.0, width=100, height=100, start_id=1)
        requests = gen.maybe_generate(time=5)

        # Verify exactly 1 request
        self.assertEqual(len(requests), 1)
        
        # Verify request properties
        req = requests[0]
        self.assertEqual(req.id, 1)
        self.assertEqual(req.pickup.x, 10.0)
        self.assertEqual(req.pickup.y, 20.0)
        self.assertEqual(req.dropoff.x, 30.0)
        self.assertEqual(req.dropoff.y, 40.0)
        self.assertEqual(req.creation_time, 5)

    @patch('phase2.generator._generate_poisson')
    def test_generates_multiple_requests(self, mock_poisson):
        """Multiple requests get sequential IDs."""
        mock_poisson.return_value = 3

        gen = RequestGenerator(rate=2.0, width=100, height=100, start_id=1)
        requests = gen.maybe_generate(time=0)

        self.assertEqual(len(requests), 3)
        ids = [r.id for r in requests]
        self.assertEqual(ids, [1, 2, 3])

    def test_pickup_dropoff_different(self):
        """Pickup and dropoff must be different."""
        gen = RequestGenerator(rate=3.0, width=100, height=100)
        for t in range(10):
            for req in gen.maybe_generate(time=t):
                self.assertNotEqual(req.pickup, req.dropoff)

    def test_coordinates_within_bounds(self):
        """Coordinates must be within map bounds."""
        width, height = 50, 75
        gen = RequestGenerator(rate=3.0, width=width, height=height)

        for t in range(10):
            for req in gen.maybe_generate(time=t):
                self.assertGreaterEqual(req.pickup.x, 0)
                self.assertLessEqual(req.pickup.x, width)
                self.assertGreaterEqual(req.pickup.y, 0)
                self.assertLessEqual(req.pickup.y, height)

    def test_creation_time_set_correctly(self):
        """Requests have correct creation_time."""
        gen = RequestGenerator(rate=3.0, width=100, height=100)
        for t in [0, 5, 10, 42]:
            for req in gen.maybe_generate(time=t):
                self.assertEqual(req.creation_time, t)


class TestGetState(unittest.TestCase):
    """Test RequestGenerator.get_state method."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        gen = RequestGenerator(rate=2.0, width=100, height=100)
        state = gen.get_state()
        self.assertIsInstance(state, dict)

    def test_contains_expected_keys(self):
        """State has all expected keys."""
        gen = RequestGenerator(rate=2.0, width=100, height=100)
        state = gen.get_state()
        expected = {'rate', 'width', 'height', 'next_id', 'total_generated'}
        self.assertEqual(set(state.keys()), expected)

    def test_reflects_initial_values(self):
        """State reflects initialization values."""
        gen = RequestGenerator(rate=2.5, width=50, height=75, start_id=5)
        state = gen.get_state()
        self.assertEqual(state['rate'], 2.5)
        self.assertEqual(state['width'], 50)
        self.assertEqual(state['height'], 75)
        self.assertEqual(state['next_id'], 5)

    @patch('phase2.generator._generate_poisson')
    def test_updates_after_generation(self, mock_poisson):
        """State updates after generating requests."""
        mock_poisson.return_value = 2  # 2 requests per tick

        gen = RequestGenerator(rate=2.0, width=100, height=100, start_id=1)
        
        # Generate for 3 ticks = 6 total requests
        for t in range(3):
            gen.maybe_generate(time=t)

        state = gen.get_state()
        self.assertEqual(state['next_id'], 7)
        self.assertEqual(state['total_generated'], 6)


class TestGeneratorIntegration(unittest.TestCase):
    """Integration tests for complete generation workflow."""

    def test_full_workflow(self):
        """Test: create, generate, check state."""
        gen = RequestGenerator(rate=2.0, width=100, height=100, start_id=1)

        # Initial state
        self.assertEqual(gen.get_state()['next_id'], 1)

        # Generate over time
        all_requests = []
        for t in range(20):
            all_requests.extend(gen.maybe_generate(time=t))

        # Final state matches
        final_state = gen.get_state()
        self.assertEqual(final_state['total_generated'], len(all_requests))

        # All requests are valid
        for req in all_requests:
            self.assertIsInstance(req, Request)
            self.assertIsInstance(req.pickup, Point)
            self.assertIsInstance(req.dropoff, Point)

    def test_disabled_produces_nothing(self):
        """Disabled generator never produces requests."""
        gen = RequestGenerator(rate=10.0, width=100, height=100, enabled=False)

        total = 0
        for t in range(100):
            total += len(gen.maybe_generate(time=t))

        self.assertEqual(total, 0)


if __name__ == '__main__':
    unittest.main()
