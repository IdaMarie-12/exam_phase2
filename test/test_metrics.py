"""
Unit tests for metrics tracking in SimulationTimeSeries.

Tests behaviour mutation tracking, stagnation analysis, and post-simulation
summary statistics for comprehensive simulation analysis.
"""

import unittest
from unittest.mock import Mock

from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
from phase2.driver import Driver
from phase2.behaviours import (
    GreedyDistanceBehaviour,
    EarningsMaxBehaviour,
    LazyBehaviour
)
from phase2.point import Point


class MockSimulation:
    """Mock simulation for testing metrics tracking."""
    
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


class TestSimulationTimeSeriesInitialization(unittest.TestCase):
    """Test SimulationTimeSeries initialization."""
    
    def test_initialization_creates_empty_lists(self):
        """Initialization creates empty tracking lists."""
        ts = SimulationTimeSeries()
        
        self.assertEqual(ts.times, [])
        self.assertEqual(ts.served, [])
        self.assertEqual(ts.expired, [])
        self.assertEqual(ts.avg_wait, [])
        self.assertEqual(ts.pending, [])
        self.assertEqual(ts.utilization, [])
        self.assertEqual(ts.behaviour_distribution, [])
        self.assertEqual(ts.behaviour_mutations, [])
        self.assertEqual(ts.behaviour_stagnation, [])
    
    def test_initialization_sets_mutation_counter_to_zero(self):
        """Mutation counter starts at zero."""
        ts = SimulationTimeSeries()
        self.assertEqual(ts._total_mutations, 0)
    
    def test_initialization_sets_empty_behaviour_history(self):
        """Previous behaviour tracking starts empty."""
        ts = SimulationTimeSeries()
        self.assertEqual(ts._previous_behaviours, {})


# ====================================================================
# Basic Recording Tests
# ====================================================================

class TestBasicRecording(unittest.TestCase):
    """Test basic tick recording functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ts = SimulationTimeSeries()
        self.sim = MockSimulation(num_drivers=2)
    
    def test_record_tick_captures_time(self):
        """record_tick captures simulation time."""
        self.sim.time = 5
        self.ts.record_tick(self.sim)
        
        self.assertEqual(self.ts.times[-1], 5)
    
    def test_record_tick_captures_metrics(self):
        """record_tick captures all system metrics."""
        self.sim.time = 10
        self.sim.served_count = 25
        self.sim.expired_count = 3
        self.sim.avg_wait = 12.5
        
        self.ts.record_tick(self.sim)
        
        self.assertEqual(self.ts.served[-1], 25)
        self.assertEqual(self.ts.expired[-1], 3)
        self.assertEqual(self.ts.avg_wait[-1], 12.5)
    
    def test_record_tick_calculates_utilization(self):
        """record_tick calculates driver utilization percentage."""
        self.sim.drivers[0].status = "TO_PICKUP"  # Busy
        self.sim.drivers[1].status = "IDLE"       # Idle
        
        self.ts.record_tick(self.sim)
        
        # 1 busy out of 2 = 50%
        self.assertEqual(self.ts.utilization[-1], 50.0)
    
    def test_record_tick_multiple_times(self):
        """record_tick appends to lists on repeated calls."""
        self.ts.record_tick(self.sim)
        self.ts.record_tick(self.sim)
        self.ts.record_tick(self.sim)
        
        self.assertEqual(len(self.ts.times), 3)
        self.assertEqual(len(self.ts.served), 3)


# ====================================================================
# Behaviour Distribution Tests
# ====================================================================

class TestBehaviourDistribution(unittest.TestCase):
    """Test behaviour distribution tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ts = SimulationTimeSeries()
    
    def test_behaviour_distribution_initial_state(self):
        """Initial behaviour distribution records all driver behaviours."""
        sim = MockSimulation(num_drivers=3)
        sim.drivers[0].behaviour = GreedyDistanceBehaviour(10.0)
        sim.drivers[1].behaviour = EarningsMaxBehaviour(0.8)
        sim.drivers[2].behaviour = LazyBehaviour(idle_ticks_needed=5)
        
        self.ts.record_tick(sim)
        
        dist = self.ts.behaviour_distribution[-1]
        self.assertEqual(dist['GreedyDistanceBehaviour'], 1)
        self.assertEqual(dist['EarningsMaxBehaviour'], 1)
        self.assertEqual(dist['LazyBehaviour'], 1)
    
    def test_behaviour_distribution_with_duplicates(self):
        """Behaviour distribution counts multiple drivers with same behaviour."""
        sim = MockSimulation(num_drivers=4)
        sim.drivers[0].behaviour = GreedyDistanceBehaviour(10.0)
        sim.drivers[1].behaviour = GreedyDistanceBehaviour(10.0)
        sim.drivers[2].behaviour = EarningsMaxBehaviour(0.8)
        sim.drivers[3].behaviour = EarningsMaxBehaviour(0.8)
        
        self.ts.record_tick(sim)
        
        dist = self.ts.behaviour_distribution[-1]
        self.assertEqual(dist['GreedyDistanceBehaviour'], 2)
        self.assertEqual(dist['EarningsMaxBehaviour'], 2)
    
    def test_behaviour_distribution_changes_over_time(self):
        """Behaviour distribution changes as drivers mutate."""
        sim = MockSimulation(num_drivers=2)
        
        # Initial state
        self.ts.record_tick(sim)
        dist1 = self.ts.behaviour_distribution[0]
        self.assertEqual(dist1['GreedyDistanceBehaviour'], 2)
        
        # Mutate first driver
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)
        dist2 = self.ts.behaviour_distribution[1]
        self.assertEqual(dist2['GreedyDistanceBehaviour'], 1)
        self.assertEqual(dist2['EarningsMaxBehaviour'], 1)


# ====================================================================
# Behaviour Mutation Tests
# ====================================================================

class TestBehaviourMutations(unittest.TestCase):
    """Test mutation event tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ts = SimulationTimeSeries()
    
    def test_no_mutations_on_first_tick(self):
        """No mutations are recorded on first tick (no history)."""
        sim = MockSimulation(num_drivers=2)
        self.ts.record_tick(sim)
        
        self.assertEqual(self.ts.behaviour_mutations[-1], 0)
    
    def test_single_mutation_detection(self):
        """Single driver mutation is detected."""
        sim = MockSimulation(num_drivers=2)
        
        # Tick 0: initial state
        self.ts.record_tick(sim)
        self.assertEqual(self.ts.behaviour_mutations[-1], 0)
        
        # Tick 1: mutate driver 0
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)
        self.assertEqual(self.ts.behaviour_mutations[-1], 1)
    
    def test_multiple_mutations_detected(self):
        """Multiple driver mutations in one tick are detected."""
        sim = MockSimulation(num_drivers=3)
        
        # Tick 0: initial state
        self.ts.record_tick(sim)
        
        # Tick 1: mutate all 3 drivers
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        sim.drivers[1].behaviour = LazyBehaviour(idle_ticks_needed=5)
        sim.drivers[2].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)
        
        # Should have 3 mutations total
        self.assertEqual(self.ts.behaviour_mutations[-1], 3)
    
    def test_mutations_are_cumulative(self):
        """Mutations counter accumulates across ticks."""
        sim = MockSimulation(num_drivers=2)
        
        self.ts.record_tick(sim)  # 0 mutations
        
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)  # 1 mutation total
        self.assertEqual(self.ts.behaviour_mutations[-1], 1)
        
        sim.drivers[1].behaviour = LazyBehaviour(idle_ticks_needed=5)
        self.ts.record_tick(sim)  # 2 mutations total
        self.assertEqual(self.ts.behaviour_mutations[-1], 2)
        
        # No mutations this tick
        self.ts.record_tick(sim)  # Still 2 mutations total
        self.assertEqual(self.ts.behaviour_mutations[-1], 2)
    
    def test_back_to_previous_behaviour_counts_as_mutation(self):
        """Driver changing back to previous behaviour counts as mutation."""
        sim = MockSimulation(num_drivers=1)
        original_behaviour_type = type(sim.drivers[0].behaviour).__name__
        
        # Tick 0: initial
        self.ts.record_tick(sim)
        
        # Tick 1: change behaviour
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)
        self.assertEqual(self.ts.behaviour_mutations[-1], 1)
        
        # Tick 2: change back to original type
        sim.drivers[0].behaviour = GreedyDistanceBehaviour(10.0)
        self.ts.record_tick(sim)
        self.assertEqual(self.ts.behaviour_mutations[-1], 2)


# ====================================================================
# Behaviour Stagnation Tests
# ====================================================================

class TestBehaviourStagnation(unittest.TestCase):
    """Test stagnation (stability) tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ts = SimulationTimeSeries()
    
    def test_stagnation_zero_on_first_tick(self):
        """No stagnation on first tick (no history)."""
        sim = MockSimulation(num_drivers=2)
        self.ts.record_tick(sim)
        
        self.assertEqual(self.ts.behaviour_stagnation[-1], 0)
    
    def test_all_drivers_stagnant_when_no_mutations(self):
        """All drivers are stagnant when behaviours don't change."""
        sim = MockSimulation(num_drivers=3)
        
        self.ts.record_tick(sim)  # Initial - no stagnation count
        self.ts.record_tick(sim)  # Same behaviours - all 3 stagnant
        
        self.assertEqual(self.ts.behaviour_stagnation[-1], 3)
    
    def test_partial_stagnation_with_mutations(self):
        """Some drivers stagnant, others mutate."""
        sim = MockSimulation(num_drivers=3)
        
        self.ts.record_tick(sim)  # Initial state
        
        # Only mutate first driver
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)
        
        # 2 drivers stagnant (0 and 1 didn't change), 1 mutated
        self.assertEqual(self.ts.behaviour_stagnation[-1], 2)
    
    def test_stagnation_count_increases_over_time(self):
        """Stagnation can increase as drivers maintain same behaviour."""
        sim = MockSimulation(num_drivers=1)
        
        self.ts.record_tick(sim)  # Initial: 0 stagnant
        self.ts.record_tick(sim)  # Tick 1: 1 stagnant
        self.ts.record_tick(sim)  # Tick 2: 1 stagnant
        self.ts.record_tick(sim)  # Tick 3: 1 stagnant
        
        self.assertEqual(self.ts.behaviour_stagnation[1], 1)
        self.assertEqual(self.ts.behaviour_stagnation[2], 1)
        self.assertEqual(self.ts.behaviour_stagnation[3], 1)


# ====================================================================
# Inverse Relationship Tests (Mutations vs Stagnation)
# ====================================================================

class TestMutationsVsStagnation(unittest.TestCase):
    """Test the inverse relationship between mutations and stagnation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ts = SimulationTimeSeries()
    
    def test_mutations_and_stagnation_are_complementary(self):
        """mutations + stagnation = total drivers (mostly)."""
        sim = MockSimulation(num_drivers=10)
        
        # Initial tick
        self.ts.record_tick(sim)
        
        # Mutate 3 drivers
        for i in range(3):
            sim.drivers[i].behaviour = EarningsMaxBehaviour(0.8)
        
        self.ts.record_tick(sim)
        
        # After first real tick, we have history
        # Mutations = 3, Stagnation = 7
        self.assertEqual(self.ts.behaviour_mutations[-1], 3)
        self.assertEqual(self.ts.behaviour_stagnation[-1], 7)
    
    def test_high_mutation_low_stagnation(self):
        """High mutations correlate with low stagnation."""
        sim = MockSimulation(num_drivers=5)
        self.ts.record_tick(sim)
        
        # Mutate all drivers with distinctly different behaviours
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        sim.drivers[1].behaviour = LazyBehaviour(5)
        sim.drivers[2].behaviour = EarningsMaxBehaviour(0.9)
        sim.drivers[3].behaviour = LazyBehaviour(3)
        sim.drivers[4].behaviour = EarningsMaxBehaviour(0.7)
        self.ts.record_tick(sim)
        
        # All 5 mutated, none stagnant
        self.assertEqual(self.ts.behaviour_mutations[-1], 5)
        self.assertEqual(self.ts.behaviour_stagnation[-1], 0)
    
    def test_low_mutation_high_stagnation(self):
        """Low mutations correlate with high stagnation."""
        sim = MockSimulation(num_drivers=10)
        self.ts.record_tick(sim)
        
        # Mutate only 1 driver
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        self.ts.record_tick(sim)
        
        # 1 mutated, 9 stagnant
        self.assertEqual(self.ts.behaviour_mutations[-1], 1)
        self.assertEqual(self.ts.behaviour_stagnation[-1], 9)


# ====================================================================
# Summary Statistics Tests
# ====================================================================

class TestFinalSummary(unittest.TestCase):
    """Test final summary generation."""
    
    def test_summary_has_required_fields(self):
        """Final summary contains all required fields."""
        ts = SimulationTimeSeries()
        sim = MockSimulation()
        ts.record_tick(sim)
        ts.record_tick(sim)
        
        summary = ts.get_final_summary()
        
        required_fields = [
            'total_time', 'final_served', 'final_expired',
            'final_avg_wait', 'total_requests', 'service_level',
            'total_behaviour_mutations', 'avg_stagnant_drivers',
            'final_behaviour_distribution'
        ]
        for field in required_fields:
            self.assertIn(field, summary)
    
    def test_summary_calculates_avg_stagnation(self):
        """Summary calculates average stagnation across all ticks."""
        ts = SimulationTimeSeries()
        sim = MockSimulation(num_drivers=4)
        
        ts.record_tick(sim)  # 0 stagnant
        
        sim.drivers[0].behaviour = EarningsMaxBehaviour(0.8)
        ts.record_tick(sim)  # 3 stagnant
        
        ts.record_tick(sim)  # 4 stagnant
        
        summary = ts.get_final_summary()
        
        # Average of [0, 3, 4] = 7/3 ≈ 2.33
        expected_avg = (0 + 3 + 4) / 3
        self.assertAlmostEqual(summary['avg_stagnant_drivers'], expected_avg, places=2)
    
    def test_summary_with_no_data(self):
        """Summary handles empty time series gracefully."""
        ts = SimulationTimeSeries()
        summary = ts.get_final_summary()
        
        self.assertEqual(summary, {})
    
    def test_final_behaviour_distribution(self):
        """Summary includes final behaviour distribution."""
        ts = SimulationTimeSeries()
        sim = MockSimulation(num_drivers=3)
        sim.drivers[0].behaviour = GreedyDistanceBehaviour(10.0)
        sim.drivers[1].behaviour = EarningsMaxBehaviour(0.8)
        sim.drivers[2].behaviour = LazyBehaviour(5)
        
        ts.record_tick(sim)
        
        summary = ts.get_final_summary()
        dist = summary['final_behaviour_distribution']
        
        self.assertEqual(dist['GreedyDistanceBehaviour'], 1)
        self.assertEqual(dist['EarningsMaxBehaviour'], 1)
        self.assertEqual(dist['LazyBehaviour'], 1)


# ====================================================================
# Get Data Tests
# ====================================================================

class TestGetData(unittest.TestCase):
    """Test get_data method."""
    
    def test_get_data_returns_all_lists(self):
        """get_data returns all tracking lists."""
        ts = SimulationTimeSeries()
        sim = MockSimulation()
        ts.record_tick(sim)
        
        data = ts.get_data()
        
        required_keys = [
            'times', 'served', 'expired', 'avg_wait', 'pending',
            'utilization', 'behaviour_distribution', 'behaviour_mutations',
            'behaviour_stagnation'
        ]
        for key in required_keys:
            self.assertIn(key, data)
            self.assertIsInstance(data[key], list)
    
    def test_get_data_list_lengths_match(self):
        """All returned lists have same length."""
        ts = SimulationTimeSeries()
        sim = MockSimulation()
        
        for _ in range(5):
            ts.record_tick(sim)
        
        data = ts.get_data()
        
        # All lists should have 5 elements
        lengths = [len(data[key]) for key in data.keys()]
        self.assertTrue(all(length == 5 for length in lengths))


if __name__ == '__main__':
    unittest.main()
