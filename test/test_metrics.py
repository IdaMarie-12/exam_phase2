import unittest
from unittest.mock import Mock

from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
from phase2.driver import Driver
from phase2.behaviours import GreedyDistanceBehaviour
from phase2.point import Point
from phase2.mutation import HybridMutation


class MockSimulation:
    """Mock simulation for metrics tracking tests."""
    
    def __init__(self, num_drivers=3):
        """Initialize mock simulation with default test state."""
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
        for driver in self.drivers:
            driver.status = 'IDLE'
        self.offer_history = []
        self.mutation_rule = MockMutationRule()


class MockMutationRule:
    """Mock mutation rule for testing."""
    
    def __init__(self):
        """Initialize empty mutation history."""
        self.mutation_history = []


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
    






class TestGetFinalSummary(unittest.TestCase):
    """Test final summary generation."""
    
    def setUp(self):
        self.ts = SimulationTimeSeries()
        self.sim = MockSimulation(num_drivers=10)
    
    def test_final_summary_empty(self):
        """Empty time-series returns empty summary."""
        summary = self.ts.get_final_summary()
        self.assertEqual(summary, {})


class TestMutationReasonTracking(unittest.TestCase):
    """Test that mutation reasons are correctly tracked throughout the system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mutation_rule = HybridMutation()
        self.ts = SimulationTimeSeries()
    
    def test_mutation_history_records_reason(self):
        """HybridMutation._record_detailed_mutation stores reason in history."""
        # Record a mutation with a specific reason
        self.mutation_rule._record_detailed_mutation(
            driver_id=1,
            time=10,
            from_behaviour="LazyBehaviour",
            to_behaviour="GreedyDistanceBehaviour",
            reason="performance_low_earnings",
            avg_fare=2.5
        )
        
        # Verify the reason is in the history
        self.assertEqual(len(self.mutation_rule.mutation_history), 1)
        entry = self.mutation_rule.mutation_history[0]
        self.assertEqual(entry['reason'], 'performance_low_earnings')
        self.assertEqual(entry['driver_id'], 1)
        self.assertEqual(entry['avg_fare'], 2.5)
    
    def test_all_six_mutation_reasons_tracked(self):
        """All 6 mutation reason types are recorded in mutation_history."""
        reasons = [
            'performance_low_earnings',
            'performance_high_earnings',
            'exit_greedy',
            'exit_earnings',
            'exit_lazy',
            'stagnation_exploration'
        ]
        
        for i, reason in enumerate(reasons):
            self.mutation_rule._record_detailed_mutation(
                driver_id=i,
                time=i,
                from_behaviour="LazyBehaviour",
                to_behaviour="GreedyDistanceBehaviour",
                reason=reason,
                avg_fare=5.0
            )
        
        # Verify all reasons are in history
        self.assertEqual(len(self.mutation_rule.mutation_history), 6)
        for i, reason in enumerate(reasons):
            self.assertEqual(self.mutation_rule.mutation_history[i]['reason'], reason)
    
    def test_metrics_tracks_mutation_reasons_from_rule(self):
        """SimulationTimeSeries._track_mutation_reasons extracts reasons from mutation_rule."""
        # Create a mock simulation with a mutation rule
        mock_sim = Mock()
        mock_sim.mutation_rule = self.mutation_rule
        
        # Add mutations with different reasons
        self.mutation_rule._record_detailed_mutation(1, 0, "Lazy", "Greedy", "performance_low_earnings", 2.5)
        self.mutation_rule._record_detailed_mutation(2, 1, "Lazy", "EarningsMax", "performance_high_earnings", 11.0)
        self.mutation_rule._record_detailed_mutation(3, 2, "Greedy", "Lazy", "exit_greedy", 5.5)
        self.mutation_rule._record_detailed_mutation(4, 3, "EarningsMax", "Lazy", "exit_earnings", 5.8)
        
        # Track mutations
        self.ts._track_mutation_reasons(mock_sim)
        
        # Verify reason counts
        self.assertEqual(self.ts._mutation_reason_counts['performance_low_earnings'], 1)
        self.assertEqual(self.ts._mutation_reason_counts['performance_high_earnings'], 1)
        self.assertEqual(self.ts._mutation_reason_counts['exit_greedy'], 1)
        self.assertEqual(self.ts._mutation_reason_counts['exit_earnings'], 1)
        self.assertEqual(self.ts._mutation_reason_counts['exit_lazy'], 0)
        self.assertEqual(self.ts._mutation_reason_counts['stagnation_exploration'], 0)
    
    def test_mutation_reasons_appended_each_tick(self):
        """mutation_reasons list records reason breakdown snapshot each tick."""
        mock_sim = Mock()
        mock_sim.mutation_rule = self.mutation_rule
        mock_sim.time = 0
        mock_sim.served_count = 0
        mock_sim.expired_count = 0
        mock_sim.avg_wait = 0
        mock_sim.drivers = []
        mock_sim.policy_manager = Mock()
        mock_sim.policy_manager.driver_policies = {}
        
        # Tick 0: No mutations
        self.ts._track_mutation_reasons(mock_sim)
        self.ts.mutation_reasons.append(self.ts._mutation_reason_counts.copy())
        
        self.assertEqual(len(self.ts.mutation_reasons), 1)
        self.assertEqual(self.ts.mutation_reasons[0]['performance_low_earnings'], 0)
        
        # Tick 1: Add a low earnings mutation
        self.mutation_rule._record_detailed_mutation(1, 1, "Lazy", "Greedy", "performance_low_earnings", 2.5)
        mock_sim.time = 1
        self.ts._track_mutation_reasons(mock_sim)
        self.ts.mutation_reasons.append(self.ts._mutation_reason_counts.copy())
        
        self.assertEqual(len(self.ts.mutation_reasons), 2)
        self.assertEqual(self.ts.mutation_reasons[1]['performance_low_earnings'], 1)
        
        # Tick 2: Add another high earnings mutation
        self.mutation_rule._record_detailed_mutation(2, 2, "Lazy", "EarningsMax", "performance_high_earnings", 11.0)
        mock_sim.time = 2
        self.ts._track_mutation_reasons(mock_sim)
        self.ts.mutation_reasons.append(self.ts._mutation_reason_counts.copy())
        
        self.assertEqual(len(self.ts.mutation_reasons), 3)
        self.assertEqual(self.ts.mutation_reasons[2]['performance_low_earnings'], 1)
        self.assertEqual(self.ts.mutation_reasons[2]['performance_high_earnings'], 1)
    
    def test_reason_counts_are_cumulative(self):
        """Reason counts accumulate across the simulation (not reset each tick)."""
        mock_sim = Mock()
        mock_sim.mutation_rule = self.mutation_rule
        
        # Add 2 low earnings mutations
        self.mutation_rule._record_detailed_mutation(1, 0, "Lazy", "Greedy", "performance_low_earnings", 2.5)
        self.mutation_rule._record_detailed_mutation(2, 1, "Lazy", "Greedy", "performance_low_earnings", 2.8)
        
        # Track
        self.ts._track_mutation_reasons(mock_sim)
        
        # Should have count of 2
        self.assertEqual(self.ts._mutation_reason_counts['performance_low_earnings'], 2)
    
    def test_window_3_data_structure(self):
        """Verify mutation_reasons list format matches what Window 3 expects."""
        mock_sim = Mock()
        mock_sim.mutation_rule = self.mutation_rule
        
        # Simulate 3 ticks with different mutations
        mutations_per_tick = [
            [("performance_low_earnings", 1)],  # Tick 0: 1 low earnings mutation
            [("performance_high_earnings", 2), ("exit_greedy", 1)],  # Tick 1: 2 high + 1 exit_greedy
            [("exit_earnings", 1)],  # Tick 2: 1 exit_earnings
        ]
        
        for tick, mutations in enumerate(mutations_per_tick):
            for reason, count in mutations:
                for _ in range(count):
                    driver_id = len(self.mutation_rule.mutation_history) + 1
                    self.mutation_rule._record_detailed_mutation(
                        driver_id=driver_id,
                        time=tick,
                        from_behaviour="SomeBehaviour",
                        to_behaviour="OtherBehaviour",
                        reason=reason,
                        avg_fare=5.0
                    )
            
            # Record tick
            self.ts._track_mutation_reasons(mock_sim)
            self.ts.mutation_reasons.append(self.ts._mutation_reason_counts.copy())
        
        # Verify structure
        self.assertEqual(len(self.ts.mutation_reasons), 3)
        
        # Tick 0: Should have 1 low earnings
        self.assertEqual(self.ts.mutation_reasons[0]['performance_low_earnings'], 1)
        
        # Tick 1: Should have cumulative 1 low, 2 high, 1 exit_greedy
        self.assertEqual(self.ts.mutation_reasons[1]['performance_low_earnings'], 1)
        self.assertEqual(self.ts.mutation_reasons[1]['performance_high_earnings'], 2)
        self.assertEqual(self.ts.mutation_reasons[1]['exit_greedy'], 1)
        
        # Tick 2: Should have cumulative 1 low, 2 high, 1 exit_greedy, 1 exit_earnings
        self.assertEqual(self.ts.mutation_reasons[2]['performance_low_earnings'], 1)
        self.assertEqual(self.ts.mutation_reasons[2]['performance_high_earnings'], 2)
        self.assertEqual(self.ts.mutation_reasons[2]['exit_greedy'], 1)
        self.assertEqual(self.ts.mutation_reasons[2]['exit_earnings'], 1)
    
    def test_final_summary_includes_mutation_reason_breakdown(self):
        """get_final_summary includes mutation_reason_breakdown."""
        mock_sim = Mock()
        mock_sim.mutation_rule = self.mutation_rule
        mock_sim.time = 5
        
        # Add some mutations
        self.mutation_rule._record_detailed_mutation(1, 0, "L", "G", "performance_low_earnings", 2.5)
        self.mutation_rule._record_detailed_mutation(2, 1, "L", "E", "performance_high_earnings", 11.0)
        self.mutation_rule._record_detailed_mutation(3, 2, "G", "L", "exit_greedy", 5.5)
        
        # Track
        self.ts._track_mutation_reasons(mock_sim)
        
        # Populate minimal required data for get_final_summary to work
        self.ts.times = [5]
        self.ts.served = [10]
        self.ts.expired = [2]
        self.ts.avg_wait = [1.5]
        self.ts.service_level = [83.3]
        self.ts.utilization = [0.75]
        self.ts.mutations_per_tick = [3]  # 3 mutations total
        self.ts.behaviour_distribution = [{"GreedyDistanceBehaviour": 5}]
        
        # Get final summary
        summary = self.ts.get_final_summary()
        
        # Verify breakdown is in summary
        self.assertIn('mutation_reason_breakdown', summary)
        breakdown = summary['mutation_reason_breakdown']
        
        self.assertEqual(breakdown['performance_low_earnings'], 1)
        self.assertEqual(breakdown['performance_high_earnings'], 1)
        self.assertEqual(breakdown['exit_greedy'], 1)
        self.assertEqual(breakdown['exit_earnings'], 0)
        self.assertEqual(breakdown['exit_lazy'], 0)
        self.assertEqual(breakdown['stagnation_exploration'], 0)
    
    def test_mutation_categories_three_way_separation(self):
        """Final summary separates mutations into 3 categories: performance, stagnation, exit."""
        # Create a simulation with mixed mutations
        sim = Mock()
        sim.time = 100
        sim.served_count = 100
        sim.expired_count = 5
        sim.avg_wait = 2.5
        sim.offer_history = []
        sim.request_history = []
        sim.requests = []
        sim.policy_names = []
        sim.actual_policy_used = []
        sim.drivers = [Mock() for _ in range(10)]
        
        # Set up mutation rule with all three types
        mutation_rule = HybridMutation()
        mutation_rule.mutation_history = [
            # ENTRY: Performance-based (market conditions)
            {'time': 10, 'driver_id': 1, 'reason': 'performance_low_earnings'},
            {'time': 20, 'driver_id': 2, 'reason': 'performance_low_earnings'},
            {'time': 30, 'driver_id': 3, 'reason': 'performance_high_earnings'},
            # ENTRY: Stagnation-based (personal plateau)
            {'time': 40, 'driver_id': 4, 'reason': 'stagnation_exploration'},
            {'time': 41, 'driver_id': 5, 'reason': 'stagnation_exploration'},
            # EXIT: Safety valve (strategy failure)
            {'time': 50, 'driver_id': 6, 'reason': 'exit_greedy'},
            {'time': 60, 'driver_id': 7, 'reason': 'exit_earnings'},
        ]
        sim.mutation_rule = mutation_rule
        
        ts = SimulationTimeSeries()
        # Populate required fields
        ts.times = [100]
        ts.served = [100]
        ts.expired = [5]
        ts.avg_wait = [2.5]
        ts.service_level = [95.0]
        ts.stable_ratio = [80.0]
        ts.utilization = [0.85]
        
        # Call _track_mutation_reasons to populate counts
        ts._track_mutation_reasons(sim)
        
        # Calculate categories (same logic as get_final_summary)
        entry_perf = (ts._mutation_reason_counts.get('performance_low_earnings', 0) +
                      ts._mutation_reason_counts.get('performance_high_earnings', 0))
        entry_stag = ts._mutation_reason_counts.get('stagnation_exploration', 0)
        exit_valve = (ts._mutation_reason_counts.get('exit_greedy', 0) +
                      ts._mutation_reason_counts.get('exit_earnings', 0) +
                      ts._mutation_reason_counts.get('exit_lazy', 0))
        
        # Verify performance-based entries (respond to market)
        self.assertEqual(entry_perf, 3)  # 2 low + 1 high
        
        # Verify stagnation-based entries (respond to plateau)
        self.assertEqual(entry_stag, 2)  # 2 stagnation
        
        # Verify exit safety valve (protect against failure)
        self.assertEqual(exit_valve, 2)  # 1 greedy + 1 earnings
        
        # Verify detailed breakdown still available
        breakdown = ts._mutation_reason_counts
        self.assertEqual(breakdown['performance_low_earnings'], 2)
        self.assertEqual(breakdown['performance_high_earnings'], 1)
        self.assertEqual(breakdown['stagnation_exploration'], 2)
        self.assertEqual(breakdown['exit_greedy'], 1)
        self.assertEqual(breakdown['exit_earnings'], 1)


class TestWindow3DataIntegrity(unittest.TestCase):
    """Test that Window 3 has all data it needs."""
    
    def test_time_series_has_mutations_per_tick(self):
        """SimulationTimeSeries tracks mutations per tick."""
        ts = SimulationTimeSeries()
        self.assertEqual(ts.mutations_per_tick, [])
        # Should be populated by record_tick
    
    def test_time_series_has_mutation_reasons(self):
        """SimulationTimeSeries tracks mutation_reasons over time."""
        ts = SimulationTimeSeries()
        self.assertEqual(ts.mutation_reasons, [])
        # Should be populated by record_tick
    
    def test_time_series_has_driver_mutation_freq(self):
        """SimulationTimeSeries tracks driver_mutation_freq."""
        ts = SimulationTimeSeries()
        self.assertEqual(ts.driver_mutation_freq, {})
        # Should be populated by record_tick
    
    def test_mutation_reason_counts_initialized(self):
        """_mutation_reason_counts initialized with all 6 reasons."""
        ts = SimulationTimeSeries()
        expected = {
            'performance_low_earnings': 0,
            'performance_high_earnings': 0,
            'exit_greedy': 0,
            'exit_earnings': 0,
            'exit_lazy': 0,
            'stagnation_exploration': 0
        }
        self.assertEqual(ts._mutation_reason_counts, expected)
    
    def test_format_earnings_statistics_with_drivers(self):
        """format_earnings_statistics generates text with driver data."""
        from phase2.helpers_2.metrics_helpers import format_earnings_statistics
        
        sim = MockSimulation(num_drivers=3)
        # Set some earnings
        sim.drivers[0].earnings = 100.0
        sim.drivers[1].earnings = 150.0
        sim.drivers[2].earnings = 200.0
        sim.earnings_by_behaviour = {
            'GreedyDistanceBehaviour': [100.0, 150.0, 200.0]
        }
        
        text = format_earnings_statistics(sim)
        
        # Verify key information is included
        self.assertIn('EARNINGS SUMMARY', text)
        self.assertIn('Total Fleet Earnings:', text)
        self.assertIn('450', text)  # 100 + 150 + 200
        self.assertIn('Drivers:', text)
        self.assertIn('Avg per Driver:', text)
    
    def test_format_earnings_statistics_no_drivers(self):
        """format_earnings_statistics handles no drivers gracefully."""
        from phase2.helpers_2.metrics_helpers import format_earnings_statistics
        
        sim = MockSimulation(num_drivers=0)
        sim.drivers = []
        sim.earnings_by_behaviour = {}
        
        text = format_earnings_statistics(sim)
        
        # Should still generate text
        self.assertIn('EARNINGS SUMMARY', text)
        self.assertIn('No driver data available', text)


if __name__ == '__main__':
    unittest.main()
