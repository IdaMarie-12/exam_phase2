import unittest
from datetime import datetime
from phase2.offer import Offer
from phase2.driver import Driver
from phase2.request import Request
from phase2.point import Point


class TestOfferCreation(unittest.TestCase):
    """Test Offer instantiation and basic properties."""

    def setUp(self):
        """Create driver, request, and offer for testing."""
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

    def test_offer_creation_basic(self):
        """Offer is created with all required fields."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        self.assertEqual(offer.driver.id, 1)
        self.assertEqual(offer.request.id, 42)
        self.assertEqual(offer.estimated_travel_time, 10.0)
        self.assertEqual(offer.estimated_reward, 15.0)

    def test_offer_with_policy_name(self):
        """Offer stores policy name when provided."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
            policy_name="GreedyDistance",
        )
        self.assertEqual(offer.policy_name, "GreedyDistance")

    def test_offer_without_policy_name(self):
        """Offer has None policy_name when not provided."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        self.assertIsNone(offer.policy_name)

    def test_offer_created_at_default(self):
        """Offer has created_at timestamp set by default."""
        before = datetime.now()
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        after = datetime.now()
        self.assertIsNotNone(offer.created_at)
        self.assertGreaterEqual(offer.created_at, before)
        self.assertLessEqual(offer.created_at, after)

    def test_offer_created_at_explicit(self):
        """Offer accepts explicit created_at timestamp."""
        ts = datetime(2025, 12, 12, 10, 30, 45)
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
            created_at=ts,
        )
        self.assertEqual(offer.created_at, ts)


class TestRewardPerTime(unittest.TestCase):
    """Test reward_per_time calculation."""

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

    def test_reward_per_time_basic(self):
        """reward_per_time = reward / travel_time."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
        )
        self.assertAlmostEqual(offer.reward_per_time(), 2.0)

    def test_reward_per_time_fractional(self):
        """reward_per_time works with fractional values."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=3.0,
            estimated_reward=7.5,
        )
        self.assertAlmostEqual(offer.reward_per_time(), 2.5)

    def test_reward_per_time_zero_travel_time(self):
        """Zero travel time returns 0.0 to prevent division by zero."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=0.0,
            estimated_reward=20.0,
        )
        self.assertEqual(offer.reward_per_time(), 0.0)

    def test_reward_per_time_negative_travel_time(self):
        """Negative travel time returns 0.0."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=-5.0,
            estimated_reward=20.0,
        )
        self.assertEqual(offer.reward_per_time(), 0.0)

    def test_reward_per_time_zero_reward(self):
        """Zero reward returns 0.0."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=0.0,
        )
        self.assertEqual(offer.reward_per_time(), 0.0)

    def test_reward_per_time_high_efficiency(self):
        """High reward with low travel time gives high efficiency."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=1.0,
            estimated_reward=100.0,
        )
        self.assertEqual(offer.reward_per_time(), 100.0)

    def test_reward_per_time_low_efficiency(self):
        """Low reward with high travel time gives low efficiency."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=100.0,
            estimated_reward=1.0,
        )
        self.assertAlmostEqual(offer.reward_per_time(), 0.01)


class TestPickupDistance(unittest.TestCase):
    """Test pickup distance calculation."""

    def test_pickup_distance_basic(self):
        """pickup_distance returns distance from driver to pickup."""
        driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )
        request = Request(
            id=42,
            pickup=Point(3.0, 4.0),  # Distance = 5.0
            dropoff=Point(10.0, 10.0),
            creation_time=0
        )
        offer = Offer(
            driver=driver,
            request=request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        self.assertAlmostEqual(offer.pickup_distance(), 5.0)

    def test_pickup_distance_zero(self):
        """pickup_distance is zero when driver at pickup."""
        driver = Driver(
            id=1,
            position=Point(5.0, 5.0),
            speed=1.0,
        )
        request = Request(
            id=42,
            pickup=Point(5.0, 5.0),
            dropoff=Point(15.0, 15.0),
            creation_time=0
        )
        offer = Offer(
            driver=driver,
            request=request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        self.assertAlmostEqual(offer.pickup_distance(), 0.0)

    def test_pickup_distance_large(self):
        """pickup_distance calculates large distances correctly."""
        driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )
        request = Request(
            id=42,
            pickup=Point(30.0, 40.0),  # Distance = 50.0
            dropoff=Point(60.0, 80.0),
            creation_time=0
        )
        offer = Offer(
            driver=driver,
            request=request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        self.assertAlmostEqual(offer.pickup_distance(), 50.0)

    def test_pickup_distance_diagonal(self):
        """pickup_distance works with diagonal positions."""
        driver = Driver(
            id=1,
            position=Point(1.0, 1.0),
            speed=1.0,
        )
        request = Request(
            id=42,
            pickup=Point(4.0, 5.0),
            dropoff=Point(10.0, 10.0),
            creation_time=0
        )
        offer = Offer(
            driver=driver,
            request=request,
            estimated_travel_time=10.0,
            estimated_reward=15.0,
        )
        # Distance from (1,1) to (4,5) = sqrt(9 + 16) = 5.0
        self.assertAlmostEqual(offer.pickup_distance(), 5.0)


class TestAsDict(unittest.TestCase):
    """Test offer serialization to dictionary."""

    def setUp(self):
        """Create offer for testing."""
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
        self.ts = datetime(2025, 12, 12, 10, 30, 45)

    def test_as_dict_contains_all_fields(self):
        """as_dict includes all offer metrics."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
            created_at=self.ts,
            policy_name="TestPolicy",
        )
        d = offer.as_dict()
        
        self.assertIn("driver_id", d)
        self.assertIn("request_id", d)
        self.assertIn("estimated_travel_time", d)
        self.assertIn("estimated_reward", d)
        self.assertIn("reward_per_time", d)
        self.assertIn("pickup_distance", d)
        self.assertIn("created_at", d)
        self.assertIn("policy_name", d)

    def test_as_dict_values(self):
        """as_dict contains correct values."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
            created_at=self.ts,
            policy_name="TestPolicy",
        )
        d = offer.as_dict()
        
        self.assertEqual(d["driver_id"], 1)
        self.assertEqual(d["request_id"], 42)
        self.assertEqual(d["estimated_travel_time"], 10.0)
        self.assertEqual(d["estimated_reward"], 20.0)
        self.assertEqual(d["reward_per_time"], 2.0)
        self.assertEqual(d["policy_name"], "TestPolicy")

    def test_as_dict_pickup_distance_calculated(self):
        """as_dict includes calculated pickup_distance."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
            created_at=self.ts,
        )
        d = offer.as_dict()
        
        # Driver at (0,0), pickup at (5,5) = sqrt(50) ≈ 7.07
        expected_distance = self.driver.position.distance_to(self.request.pickup)
        self.assertAlmostEqual(d["pickup_distance"], expected_distance, places=9)

    def test_as_dict_without_policy_name(self):
        """as_dict has None policy_name when not set."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
            created_at=self.ts,
        )
        d = offer.as_dict()
        self.assertIsNone(d["policy_name"])

    def test_as_dict_created_at_iso_format(self):
        """as_dict converts created_at to ISO format string."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
            created_at=self.ts,
        )
        d = offer.as_dict()
        
        self.assertEqual(d["created_at"], "2025-12-12T10:30:45")

    def test_as_dict_without_created_at(self):
        """as_dict handles None created_at."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
            created_at=None,
        )
        d = offer.as_dict()
        self.assertIsNone(d["created_at"])

    def test_as_dict_returns_float_values(self):
        """as_dict converts all numeric values to float."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10,  # int
            estimated_reward=20,  # int
            created_at=self.ts,
        )
        d = offer.as_dict()
        
        self.assertIsInstance(d["estimated_travel_time"], float)
        self.assertIsInstance(d["estimated_reward"], float)
        self.assertIsInstance(d["reward_per_time"], float)
        self.assertIsInstance(d["pickup_distance"], float)


class TestRepr(unittest.TestCase):
    """Test offer string representation."""

    def setUp(self):
        """Create offer for testing."""
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

    def test_repr_format(self):
        """__repr__ returns formatted string."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
        )
        repr_str = repr(offer)
        
        self.assertIn("Offer", repr_str)
        self.assertIn("driver_id=1", repr_str)
        self.assertIn("request_id=42", repr_str)
        self.assertIn("travel_time=10.00", repr_str)
        self.assertIn("reward=20.00", repr_str)

    def test_repr_readable(self):
        """__repr__ is concise and readable."""
        offer = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=5.5,
            estimated_reward=15.25,
        )
        repr_str = repr(offer)
        
        # Should contain formatted values
        self.assertIn("5.50", repr_str)
        self.assertIn("15.25", repr_str)

    def test_repr_multiple_offers_different(self):
        """Different offers have different repr strings."""
        offer1 = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=5.0,
            estimated_reward=10.0,
        )
        offer2 = Offer(
            driver=self.driver,
            request=self.request,
            estimated_travel_time=10.0,
            estimated_reward=20.0,
        )
        self.assertNotEqual(repr(offer1), repr(offer2))


class TestOfferComparison(unittest.TestCase):
    """Test comparing offers by different metrics."""

    def setUp(self):
        """Create driver and requests for testing."""
        self.driver = Driver(
            id=1,
            position=Point(0.0, 0.0),
            speed=1.0,
        )
        self.request1 = Request(
            id=1,
            pickup=Point(5.0, 5.0),
            dropoff=Point(15.0, 15.0),
            creation_time=0
        )
        self.request2 = Request(
            id=2,
            pickup=Point(10.0, 10.0),
            dropoff=Point(20.0, 20.0),
            creation_time=0
        )

    def test_offers_for_same_request(self):
        """Compare offers for same request from different drivers."""
        driver2 = Driver(
            id=2,
            position=Point(20.0, 0.0),  # Much farther from pickup
            speed=1.0,
        )
        offer1 = Offer(
            driver=self.driver,
            request=self.request1,
            estimated_travel_time=5.0,
            estimated_reward=10.0,
        )
        offer2 = Offer(
            driver=driver2,
            request=self.request1,
            estimated_travel_time=10.0,
            estimated_reward=10.0,
        )
        
        # offer1 is more efficient (shorter travel time)
        self.assertGreater(offer1.reward_per_time(), offer2.reward_per_time())
        # offer1 driver is closer to pickup
        self.assertLess(offer1.pickup_distance(), offer2.pickup_distance())

    def test_offers_efficiency_ranking(self):
        """Offers can be ranked by efficiency."""
        offers = [
            Offer(self.driver, self.request1, 10.0, 5.0),    # 0.5 efficiency
            Offer(self.driver, self.request1, 5.0, 10.0),    # 2.0 efficiency
            Offer(self.driver, self.request1, 2.0, 8.0),     # 4.0 efficiency
        ]
        
        # Sort by reward_per_time (most efficient first)
        sorted_offers = sorted(offers, key=lambda o: o.reward_per_time(), reverse=True)
        
        self.assertEqual(sorted_offers[0].reward_per_time(), 4.0)
        self.assertEqual(sorted_offers[1].reward_per_time(), 2.0)
        self.assertEqual(sorted_offers[2].reward_per_time(), 0.5)


if __name__ == '__main__':
    unittest.main()
