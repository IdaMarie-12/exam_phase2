import unittest
from unittest.mock import patch
import matplotlib.pyplot as plt

from phase2.report_window import (
    _plot_requests_evolution,
    _plot_service_level_evolution,
    _plot_utilization_evolution,
    _plot_behaviour_distribution_evolution,
    _plot_driver_mutation_frequency,
    _plot_mutation_categories_pie,
    _plot_mutation_categories_bar,
    _plot_mutation_reason_breakdown_detailed
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
    
    def test_plot_service_level_evolution(self):
        """Plot service level evolution."""
        fig, ax = plt.subplots()
        
        _plot_service_level_evolution(ax, self.time_series)
        
        self.assertEqual(ax.get_title(), 'Service Level Evolution (% Served)')
        # Service level should be between 0 and 100%
        ylim = ax.get_ylim()
        self.assertLessEqual(ylim[1], 105)
    
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
    
    def test_plot_driver_mutation_frequency(self):
        """Plot driver mutation frequency distribution."""
        fig, ax = plt.subplots()
        
        # Add some driver mutations
        self.time_series.driver_mutation_freq = {1: 2, 2: 1, 3: 3, 4: 1}
        
        _plot_driver_mutation_frequency(ax, self.time_series)
        
        self.assertIn('Frequency', ax.get_title())
    
    def test_plot_mutation_categories_pie(self):
        """Plot 3-category mutation distribution as pie chart."""
        fig, ax = plt.subplots()
        
        # Add mutation data to time series
        self.time_series.mutation_reasons = [
            {'performance_low_earnings': 2, 'performance_high_earnings': 1, 
             'stagnation_exploration': 1, 'exit_greedy': 1, 'exit_earnings': 1, 'exit_lazy': 0},
            {'performance_low_earnings': 3, 'performance_high_earnings': 2, 
             'stagnation_exploration': 2, 'exit_greedy': 2, 'exit_earnings': 1, 'exit_lazy': 0}
        ]
        
        _plot_mutation_categories_pie(ax, self.time_series)
        
        self.assertIn('3-Way Split', ax.get_title())
    
    def test_plot_mutation_categories_bar(self):
        """Plot 3-category mutation counts as bar chart."""
        fig, ax = plt.subplots()
        
        # Add mutation data to time series
        self.time_series.mutation_reasons = [
            {'performance_low_earnings': 2, 'performance_high_earnings': 1, 
             'stagnation_exploration': 1, 'exit_greedy': 1, 'exit_earnings': 1, 'exit_lazy': 0}
        ]
        
        _plot_mutation_categories_bar(ax, self.time_series)
        
        self.assertIn('Category', ax.get_title())
    
    def test_plot_mutation_reason_breakdown_detailed(self):
        """Plot detailed breakdown of all 6 mutation reasons."""
        fig, ax = plt.subplots()
        
        # Add mutation data to time series
        self.time_series.mutation_reasons = [
            {'performance_low_earnings': 2, 'performance_high_earnings': 1, 
             'stagnation_exploration': 1, 'exit_greedy': 1, 'exit_earnings': 1, 'exit_lazy': 0}
        ]
        
        _plot_mutation_reason_breakdown_detailed(ax, self.time_series)
        
        self.assertIn('6-Way Breakdown', ax.get_title())


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


if __name__ == '__main__':
    unittest.main()
