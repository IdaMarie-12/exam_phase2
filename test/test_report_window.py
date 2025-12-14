"""
Unit tests for report_window.py module.
Tests visualization window creation and plot data handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from phase2.report_window import (
    generate_report,
)
from phase2.simulation import DeliverySimulation
from phase2.behaviours import LazyBehaviour
from phase2.helpers_2.metrics_helpers import SimulationTimeSeries


class TestDataFormatForPlotting(unittest.TestCase):
    """Test that plot functions properly handle data."""

    def setUp(self):
        """Create mock time series."""
        self.time_series = Mock(spec=SimulationTimeSeries)
        self.time_series.times = [0, 10, 20, 30]
        self.time_series.get_data.return_value = {
            'times': [0, 10, 20, 30],
            'served': [0, 5, 10, 15],
            'expired': [0, 1, 2, 3],
            'avg_wait': [0, 10, 15, 18],
            'pending': [50, 45, 40, 35],
            'utilization': [50, 60, 70, 80],
        }

    @patch('phase2.report_window.plt')
    def test_plot_requests_evolution_with_data(self, mock_plt):
        """_plot_requests_evolution handles data correctly."""
        from phase2.report_window import _plot_requests_evolution
        
        mock_ax = MagicMock()
        _plot_requests_evolution(mock_ax, self.time_series)
        
        # Should call plot for both served and expired
        self.assertGreaterEqual(mock_ax.plot.call_count, 2)

    @patch('phase2.report_window.plt')
    def test_plot_requests_evolution_none_time_series(self, mock_plt):
        """_plot_requests_evolution handles None time_series."""
        from phase2.report_window import _plot_requests_evolution
        
        mock_ax = MagicMock()
        _plot_requests_evolution(mock_ax, None)
        
        # Should display "No time-series data" message
        mock_ax.text.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_wait_time_evolution_with_data(self, mock_plt):
        """_plot_wait_time_evolution handles data correctly."""
        from phase2.report_window import _plot_wait_time_evolution
        
        mock_ax = MagicMock()
        _plot_wait_time_evolution(mock_ax, self.time_series)
        
        # Should plot wait time data
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_pending_evolution_with_data(self, mock_plt):
        """_plot_pending_evolution handles data correctly."""
        from phase2.report_window import _plot_pending_evolution
        
        mock_ax = MagicMock()
        _plot_pending_evolution(mock_ax, self.time_series)
        
        # Should plot pending data
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_utilization_evolution_with_data(self, mock_plt):
        """_plot_utilization_evolution handles data correctly."""
        from phase2.report_window import _plot_utilization_evolution
        
        mock_ax = MagicMock()
        _plot_utilization_evolution(mock_ax, self.time_series)
        
        # Should plot utilization data
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_utilization_sets_limits(self, mock_plt):
        """_plot_utilization_evolution sets y-limits."""
        from phase2.report_window import _plot_utilization_evolution
        
        mock_ax = MagicMock()
        _plot_utilization_evolution(mock_ax, self.time_series)
        
        # Should set y-limits for utilization
        mock_ax.set_ylim.assert_called()


class TestSummaryStatisticsPlot(unittest.TestCase):
    """Test _plot_summary_statistics function."""

    def setUp(self):
        """Create mock simulation and time series."""
        self.simulation = Mock(spec=DeliverySimulation)
        self.simulation.drivers = [Mock() for _ in range(5)]
        self.simulation.requests = [Mock() for _ in range(100)]
        self.simulation.served_count = 80
        self.simulation.expired_count = 20
        self.simulation.time = 500
        self.simulation.avg_wait = 20.0
        
        self.time_series = Mock(spec=SimulationTimeSeries)

    @patch('phase2.report_window.plt')
    def test_plot_summary_statistics_with_time_series(self, mock_plt):
        """_plot_summary_statistics displays summary with time series."""
        from phase2.report_window import _plot_summary_statistics
        
        mock_ax = MagicMock()
        self.time_series.get_final_summary.return_value = {
            'total_time': 500,
            'total_requests': 100,
            'final_served': 80,
            'final_expired': 20,
            'service_level': 80.0,
            'final_avg_wait': 20.0,
        }
        
        _plot_summary_statistics(mock_ax, self.simulation, self.time_series)
        
        # Should display text with statistics
        mock_ax.text.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_summary_statistics_without_time_series(self, mock_plt):
        """_plot_summary_statistics displays summary without time series."""
        from phase2.report_window import _plot_summary_statistics
        
        mock_ax = MagicMock()
        _plot_summary_statistics(mock_ax, self.simulation, None)
        
        # Should display text with statistics from simulation
        mock_ax.text.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_summary_statistics_turns_off_axes(self, mock_plt):
        """_plot_summary_statistics turns off axes."""
        from phase2.report_window import _plot_summary_statistics
        
        mock_ax = MagicMock()
        _plot_summary_statistics(mock_ax, self.simulation, None)
        
        # Should turn off axis display
        mock_ax.axis.assert_called_with('off')


class TestBehaviourWindow(unittest.TestCase):
    """Test behaviour analysis window functions."""

    def setUp(self):
        """Create mock simulation with drivers."""
        self.simulation = Mock(spec=DeliverySimulation)
        self.driver1 = Mock()
        self.driver1.behaviour = Mock()
        self.driver1.behaviour.__class__.__name__ = 'LazyBehaviour'
        
        self.driver2 = Mock()
        self.driver2.behaviour = Mock()
        self.driver2.behaviour.__class__.__name__ = 'GreedyDistanceBehaviour'
        
        self.simulation.drivers = [self.driver1, self.driver2]

    @patch('phase2.report_window.plt')
    def test_show_behaviour_window_creates_figure(self, mock_plt):
        """_show_behaviour_window creates matplotlib figure."""
        from phase2.report_window import _show_behaviour_window
        
        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig
        
        _show_behaviour_window(self.simulation)
        
        # Should create figure
        mock_plt.figure.assert_called()


class TestMutationWindow(unittest.TestCase):
    """Test mutation analysis window functions."""

    def setUp(self):
        """Create mock simulation with mutation rule."""
        self.simulation = Mock(spec=DeliverySimulation)
        self.simulation.mutation = Mock()
        self.simulation.mutation.mutation_history = [
            {
                'time': 10,
                'driver_id': 1,
                'from_behaviour': 'LazyBehaviour',
                'to_behaviour': 'GreedyDistanceBehaviour',
                'reason': 'performance_low_earnings',
                'avg_fare': 2.5
            },
            {
                'time': 50,
                'driver_id': 2,
                'from_behaviour': 'LazyBehaviour',
                'to_behaviour': 'EarningsMaxBehaviour',
                'reason': 'performance_high_earnings',
                'avg_fare': 12.0
            }
        ]
        self.simulation.mutation.mutation_transitions = {
            ('LazyBehaviour', 'GreedyDistanceBehaviour'): 3,
            ('LazyBehaviour', 'EarningsMaxBehaviour'): 2,
        }

    @patch('phase2.report_window.plt')
    def test_show_mutation_window_creates_figure(self, mock_plt):
        """_show_mutation_window creates matplotlib figure."""
        from phase2.report_window import _show_mutation_window
        
        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig
        
        # Add required attributes to simulation
        self.simulation.served_count = 10
        self.simulation.expired_count = 5
        self.simulation.time = 100
        self.simulation.avg_wait = 15.0
        
        # Create mock drivers without _last_mutation_time attribute (use spec to prevent auto-creation)
        mock_drivers = []
        for i in range(5):
            driver = Mock(spec=['behaviour', 'id'])
            driver.behaviour = Mock(spec=['__class__'])
            driver.behaviour.__class__.__name__ = 'LazyBehaviour'
            driver.id = i
            mock_drivers.append(driver)
        self.simulation.drivers = mock_drivers
        
        _show_mutation_window(self.simulation)
        
        # Should create figure
        mock_plt.figure.assert_called()


class TestPlotDataHandling(unittest.TestCase):
    """Test that plot functions handle various data scenarios."""

    @patch('phase2.report_window.plt')
    def test_plot_with_empty_times(self, mock_plt):
        """Plots handle empty time series."""
        from phase2.report_window import _plot_requests_evolution
        
        mock_ax = MagicMock()
        time_series = Mock()
        time_series.times = []
        
        _plot_requests_evolution(mock_ax, time_series)
        
        # Should display "No time-series data"
        mock_ax.text.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_with_single_datapoint(self, mock_plt):
        """Plots handle single datapoint."""
        from phase2.report_window import _plot_wait_time_evolution
        
        mock_ax = MagicMock()
        time_series = Mock()
        time_series.times = [0]
        time_series.get_data.return_value = {
            'times': [0],
            'avg_wait': [10.0],
        }
        
        _plot_wait_time_evolution(mock_ax, time_series)
        
        # Should still plot
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.plt')
    def test_plot_with_large_dataset(self, mock_plt):
        """Plots handle large datasets."""
        from phase2.report_window import _plot_pending_evolution
        
        mock_ax = MagicMock()
        time_series = Mock()
        times = list(range(0, 10000, 10))
        time_series.times = times
        time_series.get_data.return_value = {
            'times': times,
            'pending': list(range(100, 0, -1)) * 100,  # Downward trend
        }
        
        _plot_pending_evolution(mock_ax, time_series)
        
        # Should handle large dataset
        mock_ax.plot.assert_called()


if __name__ == '__main__':
    unittest.main()
