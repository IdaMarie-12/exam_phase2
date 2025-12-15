import unittest
from unittest.mock import patch
import matplotlib.pyplot as plt

from phase2.report_window import (
    _plot_requests_evolution,
    _plot_service_level_evolution,
    _plot_wait_time_evolution,
    _plot_utilization_evolution,
    _plot_behaviour_distribution_evolution,
    _plot_mutation_rate_evolution,
    _plot_driver_mutation_frequency,
    _plot_offers_generated,
    _plot_offer_acceptance_rate,
    _plot_offer_quality,
    _plot_policy_distribution
)
from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
from phase2.driver import Driver
from phase2.behaviours import GreedyDistanceBehaviour
from phase2.point import Point


class MockSimulation:
    """Mock simulation for report window tests."""
    
    def __init__(self, num_drivers=5):
        self.time = 100
        self.served_count = 50
        self.expired_count = 25
        self.avg_wait = 3.5
        self.timeout = 20  # Add default timeout for tests
        self.drivers = [
            Driver(id=i, position=Point(i, i), 
                   behaviour=GreedyDistanceBehaviour(10.0))
            for i in range(num_drivers)
        ]
        self.requests = []
        self.offer_history = []


class TestPlotFunctions(unittest.TestCase):
    """Test plot generation functions."""
    
    def setUp(self):
        """Create test time-series data."""
        self.time_series = SimulationTimeSeries()
        
        # Populate with sample data
        for tick in range(1, 11):
            self.sim = MockSimulation()
            self.sim.time = tick
            self.sim.served_count = tick * 10
            self.sim.expired_count = tick * 3
            self.sim.avg_wait = 2.0 + (tick * 0.1)
            
            # Make some drivers busy for utilization
            for i in range(min(tick, 5)):
                self.sim.drivers[i].status = 'BUSY'
            
            self.time_series.record_tick(self.sim)
    
    def tearDown(self):
        """Close all matplotlib figures."""
        plt.close('all')
    
    def test_plot_requests_evolution_with_data(self):
        """Plot requests evolution with valid data."""
        fig, ax = plt.subplots()
        
        # Should not raise exception
        _plot_requests_evolution(ax, self.time_series)
        
        self.assertEqual(ax.get_title(), 'Request Fulfillment Evolution')
        self.assertTrue(len(ax.lines) > 0)
    
    def test_plot_requests_evolution_no_data(self):
        """Plot requests evolution handles no data gracefully."""
        fig, ax = plt.subplots()
        
        _plot_requests_evolution(ax, None)
        
        self.assertEqual(ax.get_title(), 'Served vs Expired Requests')
    
    def test_plot_service_level_evolution(self):
        """Plot service level evolution."""
        fig, ax = plt.subplots()
        
        _plot_service_level_evolution(ax, self.time_series)
        
        self.assertEqual(ax.get_title(), 'Service Level Evolution (% Served)')
        # Service level should be between 0 and 100%
        ylim = ax.get_ylim()
        self.assertLessEqual(ylim[1], 105)
    
    def test_plot_wait_time_evolution(self):
        """Plot wait time evolution."""
        fig, ax = plt.subplots()
        
        _plot_wait_time_evolution(ax, self.time_series)
        
        self.assertIn('Wait Time', ax.get_title())
        self.assertTrue(len(ax.lines) > 0)
    
    def test_plot_utilization_evolution(self):
        """Plot utilization evolution."""
        fig, ax = plt.subplots()
        
        _plot_utilization_evolution(ax, self.time_series)
        
        self.assertIn('Utilization', ax.get_title())
        # Utilization should have max line at 100%
        self.assertTrue(len(ax.lines) > 1)
    
    def test_plot_behaviour_distribution_evolution(self):
        """Plot behaviour distribution evolution."""
        fig, ax = plt.subplots()
        
        _plot_behaviour_distribution_evolution(ax, self.time_series)
        
        self.assertIn('Behaviour', ax.get_title())
    
    def test_plot_mutation_rate_evolution(self):
        """Plot mutation rate evolution."""
        fig, ax = plt.subplots()
        
        _plot_mutation_rate_evolution(ax, self.time_series)
        
        self.assertIn('Mutation', ax.get_title())
    
    def test_plot_driver_mutation_frequency(self):
        """Plot driver mutation frequency distribution."""
        fig, ax = plt.subplots()
        
        # Add some driver mutations
        self.time_series.driver_mutation_freq = {1: 2, 2: 1, 3: 3, 4: 1}
        
        _plot_driver_mutation_frequency(ax, self.time_series)
        
        self.assertIn('Frequency', ax.get_title())
    
    def test_plot_offers_generated(self):
        """Plot offers generated."""
        fig, ax = plt.subplots()
        
        _plot_offers_generated(ax, self.time_series)
        
        self.assertEqual(ax.get_title(), 'Offers Generated Per Tick')
    
    def test_plot_offer_acceptance_rate(self):
        """Plot offer acceptance rate."""
        fig, ax = plt.subplots()
        
        _plot_offer_acceptance_rate(ax, self.time_series)
        
        self.assertIn('Acceptance', ax.get_title())
    
    def test_plot_offer_quality(self):
        """Plot offer quality."""
        fig, ax = plt.subplots()
        
        _plot_offer_quality(ax, self.time_series)
        
        self.assertIn('Quality', ax.get_title())
    
    def test_plot_policy_distribution_with_data(self):
        """Plot policy distribution with data."""
        fig, ax = plt.subplots()
        
        # Add actual policy used data
        self.time_series.actual_policy_used = [
            'NearestNeighbor', 'NearestNeighbor', 'GlobalGreedy', 'GlobalGreedy', 'NearestNeighbor'
        ]
        self.time_series.times = [1, 2, 3, 4, 5]
        
        _plot_policy_distribution(ax, self.time_series)
        
        self.assertIn('Policy', ax.get_title())
    
    def test_plot_policy_distribution_no_data(self):
        """Plot policy distribution handles no data."""
        fig, ax = plt.subplots()
        
        _plot_policy_distribution(ax, None)
        
        self.assertIn('Policy', ax.get_title())


class TestReportWindowIntegration(unittest.TestCase):
    """Integration tests for report windows."""
    
    def setUp(self):
        self.sim = MockSimulation()
        self.time_series = SimulationTimeSeries()
        
        # Add some data
        for tick in range(1, 6):
            self.sim.time = tick
            self.sim.served_count += 10
            self.sim.expired_count += 2
            self.time_series.record_tick(self.sim)
    
    def tearDown(self):
        plt.close('all')
    
    @patch('matplotlib.pyplot.show')
    def test_generate_report_creates_windows(self, mock_show):
        """generate_report creates windows without error."""
        from phase2.report_window import generate_report
        
        # Should not raise exception
        generate_report(self.sim, self.time_series)
        
        # Should have called plt.show()
        mock_show.assert_called_once()
    
    def test_time_series_provides_complete_data(self):
        """Time-series provides all necessary data for plots."""
        summary = self.time_series.get_final_summary()
        
        # Check required fields exist
        self.assertIn('total_time', summary)
        self.assertIn('final_served', summary)
        self.assertIn('final_expired', summary)
        self.assertIn('final_service_level', summary)
        self.assertIn('total_behaviour_mutations', summary)


if __name__ == '__main__':
    unittest.main()
