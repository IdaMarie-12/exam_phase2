import unittest

from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
from phase2.driver import Driver
from phase2.behaviours import GreedyDistanceBehaviour
from phase2.point import Point


class MockSimulation:
    """Mock simulation for metrics tracking tests."""
    
    def __init__(self, num_drivers=3):
        self.time = 0
        self.served_count = 0
        self.expired_count = 0
        self.avg_wait = 0.0
        self.requests = []
        self.drivers = [
            Driver(id=i, position=Point(i, i), 
                   behaviour=GreedyDistanceBehaviour(10.0))
            for i in range(num_drivers)
        ]
        # Initialize all drivers to IDLE status
        for driver in self.drivers:
            driver.status = 'IDLE'
        self.offer_history = []
        self.mutation_rule = None


class TestSimulationTimeSeriesInitialization(unittest.TestCase):
    """Test SimulationTimeSeries initialization with new metrics."""
    
    def test_initialization_creates_empty_lists(self):
        """Initialization creates empty tracking lists."""
        ts = SimulationTimeSeries()
        
        # Core metrics
        self.assertEqual(ts.times, [])
        self.assertEqual(ts.served, [])
        self.assertEqual(ts.expired, [])
        self.assertEqual(ts.avg_wait, [])
        self.assertEqual(ts.service_level, [])
        self.assertEqual(ts.utilization, [])
        
        # Behaviour tracking
        self.assertEqual(ts.behaviour_distribution, [])
        self.assertEqual(ts.mutation_rate, [])
        self.assertEqual(ts.stable_ratio, [])
        
        # Mutation root cause
        self.assertEqual(ts.mutation_reasons, [])
        self.assertEqual(ts.driver_mutation_freq, {})
        
        # Policy & Offer tracking
        self.assertEqual(ts.offers_generated, [])
        self.assertEqual(ts.offer_acceptance_rate, [])
        self.assertEqual(ts.policy_distribution, [])
        self.assertEqual(ts.avg_offer_quality, [])
    
    def test_initialization_sets_mutation_counter_to_zero(self):
        """Mutation counter starts at zero."""
        ts = SimulationTimeSeries()
        self.assertEqual(ts._total_mutations, 0)
    
    def test_initialization_sets_mutation_reasons(self):
        """Mutation reason counts initialized to zero."""
        ts = SimulationTimeSeries()
        expected_reasons = {
            'performance_low_earnings': 0,
            'performance_high_earnings': 0,
            'exit_greedy': 0,
            'exit_earnings': 0,
            'exit_lazy': 0,
            'stagnation_exploration': 0
        }
        self.assertEqual(ts._mutation_reason_counts, expected_reasons)


class TestRecordTick(unittest.TestCase):
    """Test recording simulation ticks."""
    
    def setUp(self):
        self.ts = SimulationTimeSeries()
        self.sim = MockSimulation(num_drivers=5)
    
    def test_record_tick_adds_time(self):
        """record_tick adds current time."""
        self.sim.time = 10
        self.ts.record_tick(self.sim)
        self.assertEqual(self.ts.times, [10])
    
    def test_record_tick_adds_served_expired(self):
        """record_tick records served and expired counts."""
        self.sim.served_count = 15
        self.sim.expired_count = 5
        self.ts.record_tick(self.sim)
        
        self.assertEqual(self.ts.served, [15])
        self.assertEqual(self.ts.expired, [5])
    
    def test_record_tick_calculates_service_level(self):
        """record_tick calculates service level percentage."""
        self.sim.served_count = 30
        self.sim.expired_count = 20
        self.ts.record_tick(self.sim)
        
        # 30 / (30 + 20) * 100 = 60%
        self.assertEqual(self.ts.service_level, [60.0])
    
    def test_record_tick_service_level_zero_requests(self):
        """Service level is 0 when no requests."""
        self.sim.served_count = 0
        self.sim.expired_count = 0
        self.ts.record_tick(self.sim)
        
        self.assertEqual(self.ts.service_level, [0.0])
    
    def test_record_tick_calculates_utilization(self):
        """record_tick calculates driver utilization percentage."""
        # Mark some drivers as busy
        for i in range(3):
            self.sim.drivers[i].status = 'BUSY'
        # 2 drivers remain IDLE, 3 are BUSY
        # Utilization = 3/5 * 100 = 60%
        
        self.ts.record_tick(self.sim)
        
        self.assertEqual(self.ts.utilization, [60.0])
    
    def test_record_tick_multiple_ticks(self):
        """Multiple ticks append to lists."""
        for tick_num in range(1, 4):
            self.sim.time = tick_num
            self.sim.served_count = tick_num * 10
            self.ts.record_tick(self.sim)
        
        self.assertEqual(self.ts.times, [1, 2, 3])
        self.assertEqual(self.ts.served, [10, 20, 30])
        self.assertEqual(len(self.ts.behaviour_distribution), 3)


class TestBehaviourTracking(unittest.TestCase):
    """Test behaviour mutation and distribution tracking."""
    
    def setUp(self):
        self.ts = SimulationTimeSeries()
        self.sim = MockSimulation(num_drivers=3)
    
    def test_behaviour_distribution_recorded(self):
        """Behaviour distribution is recorded."""
        self.ts.record_tick(self.sim)
        
        # All drivers start with GreedyDistanceBehaviour
        dist = self.ts.behaviour_distribution[0]
        self.assertIn('GreedyDistanceBehaviour', dist)
        self.assertEqual(dist['GreedyDistanceBehaviour'], 3)
    
    def test_mutation_detection(self):
        """Mutations are detected when behaviour changes."""
        # First tick
        self.ts.record_tick(self.sim)
        initial_mutations = self.ts._total_mutations
        
        # Change one driver's behaviour
        from phase2.behaviours import LazyBehaviour
        self.sim.drivers[0].behaviour = LazyBehaviour(idle_ticks_needed=5)
        
        # Second tick should detect mutation
        self.ts.record_tick(self.sim)
        
        # Should have detected 1 new mutation
        self.assertEqual(self.ts._total_mutations, initial_mutations + 1)
    
    def test_stable_ratio_tracking(self):
        """Stable drivers ratio is tracked."""
        self.ts.record_tick(self.sim)
        
        # All drivers stable initially
        self.assertGreater(self.ts.stable_ratio[0], 0)


class TestOfferTracking(unittest.TestCase):
    """Test offer and policy tracking."""
    
    def setUp(self):
        self.ts = SimulationTimeSeries()
        self.sim = MockSimulation()
    
    def test_offers_generated_tracked(self):
        """Offers generated are tracked."""
        self.ts.record_tick(self.sim)
        
        # Should record 0 offers when offer_history is empty
        self.assertEqual(self.ts.offers_generated, [0])
    
    def test_service_level_integration(self):
        """Service level correctly integrates with other metrics."""
        self.sim.served_count = 50
        self.sim.expired_count = 30
        self.sim.avg_wait = 2.5
        
        self.ts.record_tick(self.sim)
        
        # Service level = 50 / (50 + 30) * 100 = 62.5%
        self.assertAlmostEqual(self.ts.service_level[0], 62.5, places=1)


class TestGetFinalSummary(unittest.TestCase):
    """Test final summary generation."""
    
    def setUp(self):
        self.ts = SimulationTimeSeries()
        self.sim = MockSimulation(num_drivers=10)
    
    def test_final_summary_empty(self):
        """Empty time-series returns empty summary."""
        summary = self.ts.get_final_summary()
        self.assertEqual(summary, {})
    
    def test_final_summary_single_tick(self):
        """Single tick generates complete summary."""
        self.sim.time = 5
        self.sim.served_count = 20
        self.sim.expired_count = 10
        self.sim.avg_wait = 2.5
        
        self.ts.record_tick(self.sim)
        summary = self.ts.get_final_summary()
        
        self.assertEqual(summary['total_time'], 5)
        self.assertEqual(summary['final_served'], 20)
        self.assertEqual(summary['final_expired'], 10)
        self.assertEqual(summary['final_avg_wait'], 2.5)
        self.assertAlmostEqual(summary['final_service_level'], 66.7, places=1)
        self.assertEqual(summary['total_requests'], 30)


if __name__ == '__main__':
    unittest.main()
