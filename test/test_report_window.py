"""
Unit tests for report_window.py module.
Tests data aggregation, summary generation, and report preparation functions.
Note: Visualization functions require matplotlib and are tested for proper data handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from phase2.report_window import (
    _get_static_summary,
    generate_report,
    quick_report,
)
from phase2.simulation import DeliverySimulation
from phase2.driver import Driver, IDLE
from phase2.request import Request, DELIVERED, EXPIRED, WAITING
from phase2.point import Point
from phase2.behaviours import LazyBehaviour
from phase2.helpers_2.metrics_helpers import SimulationTimeSeries


class TestStaticSummary(unittest.TestCase):
    """Test _get_static_summary function."""

    def setUp(self):
        """Create mock simulation for testing."""
        self.simulation = Mock(spec=DeliverySimulation)
        self.simulation.served_count = 50
        self.simulation.expired_count = 10
        self.simulation.time = 1000
        self.simulation.avg_wait = 25.5

    def test_static_summary_all_fields(self):
        """Summary contains all required fields."""
        summary = _get_static_summary(self.simulation)
        
        required_fields = [
            'total_time', 'total_requests', 'final_served',
            'final_expired', 'service_level', 'final_avg_wait'
        ]
        for field in required_fields:
            self.assertIn(field, summary)

    def test_static_summary_total_requests(self):
        """Total requests = served + expired."""
        self.simulation.served_count = 50
        self.simulation.expired_count = 10
        summary = _get_static_summary(self.simulation)
        self.assertEqual(summary['total_requests'], 60)

    def test_static_summary_service_level(self):
        """Service level correctly calculated."""
        self.simulation.served_count = 50
        self.simulation.expired_count = 50
        summary = _get_static_summary(self.simulation)
        self.assertAlmostEqual(summary['service_level'], 50.0)

    def test_static_summary_service_level_all_served(self):
        """Service level 100% when all requests served."""
        self.simulation.served_count = 100
        self.simulation.expired_count = 0
        summary = _get_static_summary(self.simulation)
        self.assertAlmostEqual(summary['service_level'], 100.0)

    def test_static_summary_service_level_none_served(self):
        """Service level 0% when no requests served."""
        self.simulation.served_count = 0
        self.simulation.expired_count = 100
        summary = _get_static_summary(self.simulation)
        self.assertAlmostEqual(summary['service_level'], 0.0)

    def test_static_summary_no_requests(self):
        """Service level 0 when no requests."""
        self.simulation.served_count = 0
        self.simulation.expired_count = 0
        summary = _get_static_summary(self.simulation)
        self.assertEqual(summary['service_level'], 0.0)
        self.assertEqual(summary['total_requests'], 0)

    def test_static_summary_time(self):
        """Summary includes simulation time."""
        self.simulation.time = 2500
        summary = _get_static_summary(self.simulation)
        self.assertEqual(summary['total_time'], 2500)

    def test_static_summary_avg_wait(self):
        """Summary includes average wait time."""
        self.simulation.avg_wait = 42.3
        summary = _get_static_summary(self.simulation)
        self.assertAlmostEqual(summary['final_avg_wait'], 42.3)


class TestGenerateReportMatplotlibCheck(unittest.TestCase):
    """Test generate_report matplotlib availability checking."""

    def setUp(self):
        """Create mock simulation."""
        self.simulation = Mock(spec=DeliverySimulation)
        self.simulation.drivers = []
        self.simulation.requests = []

    @patch('phase2.report_window.HAS_MATPLOTLIB', False)
    def test_generate_report_no_matplotlib_raises(self):
        """generate_report raises RuntimeError if matplotlib not available."""
        with self.assertRaises(RuntimeError) as context:
            generate_report(self.simulation)
        self.assertIn("matplotlib", str(context.exception))

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window._show_mutation_window')
    @patch('phase2.report_window._show_behaviour_window')
    @patch('phase2.report_window.plt')
    def test_generate_report_with_matplotlib_creates_figure(self, mock_plt, mock_behaviour, mock_mutation):
        """generate_report creates figure when matplotlib available."""
        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig
        
        self.simulation.served_count = 10
        self.simulation.expired_count = 5
        self.simulation.time = 100
        self.simulation.avg_wait = 15.0
        self.simulation.mutation = Mock()
        self.simulation.mutation.mutation_history = []
        self.simulation.mutation.mutation_transitions = {}
        
        generate_report(self.simulation, time_series=None)
        
        # Should attempt to create figure
        mock_plt.figure.assert_called()


class TestQuickReport(unittest.TestCase):
    """Test quick_report convenience function."""

    @patch('phase2.report_window.generate_report')
    def test_quick_report_calls_generate_report(self, mock_generate):
        """quick_report calls generate_report with same arguments."""
        sim = Mock(spec=DeliverySimulation)
        time_series = Mock(spec=SimulationTimeSeries)
        
        quick_report(sim, time_series)
        
        mock_generate.assert_called_once_with(sim, time_series)

    @patch('phase2.report_window.generate_report')
    def test_quick_report_without_time_series(self, mock_generate):
        """quick_report handles None time_series."""
        sim = Mock(spec=DeliverySimulation)
        
        quick_report(sim)
        
        mock_generate.assert_called_once_with(sim, None)


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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_plot_requests_evolution_with_data(self, mock_plt):
        """_plot_requests_evolution handles data correctly."""
        from phase2.report_window import _plot_requests_evolution
        
        mock_ax = MagicMock()
        _plot_requests_evolution(mock_ax, self.time_series)
        
        # Should call plot for both served and expired
        self.assertGreaterEqual(mock_ax.plot.call_count, 2)

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_plot_requests_evolution_none_time_series(self, mock_plt):
        """_plot_requests_evolution handles None time_series."""
        from phase2.report_window import _plot_requests_evolution
        
        mock_ax = MagicMock()
        _plot_requests_evolution(mock_ax, None)
        
        # Should display "No time-series data" message
        mock_ax.text.assert_called()

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_plot_wait_time_evolution_with_data(self, mock_plt):
        """_plot_wait_time_evolution handles data correctly."""
        from phase2.report_window import _plot_wait_time_evolution
        
        mock_ax = MagicMock()
        _plot_wait_time_evolution(mock_ax, self.time_series)
        
        # Should plot wait time data
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_plot_pending_evolution_with_data(self, mock_plt):
        """_plot_pending_evolution handles data correctly."""
        from phase2.report_window import _plot_pending_evolution
        
        mock_ax = MagicMock()
        _plot_pending_evolution(mock_ax, self.time_series)
        
        # Should plot pending data
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_plot_utilization_evolution_with_data(self, mock_plt):
        """_plot_utilization_evolution handles data correctly."""
        from phase2.report_window import _plot_utilization_evolution
        
        mock_ax = MagicMock()
        _plot_utilization_evolution(mock_ax, self.time_series)
        
        # Should plot utilization data
        mock_ax.plot.assert_called()

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_plot_summary_statistics_without_time_series(self, mock_plt):
        """_plot_summary_statistics displays summary without time series."""
        from phase2.report_window import _plot_summary_statistics
        
        mock_ax = MagicMock()
        _plot_summary_statistics(mock_ax, self.simulation, None)
        
        # Should display text with statistics from simulation
        mock_ax.text.assert_called()

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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
        self.simulation.drivers = [Mock() for _ in range(3)]
        self.simulation.requests = [Mock() for _ in range(100)]
        self.simulation.served_count = 80
        self.simulation.expired_count = 20
        self.simulation.time = 500
        self.simulation.avg_wait = 20.0
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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
    @patch('phase2.report_window.plt')
    def test_show_mutation_window_creates_figure(self, mock_plt):
        """_show_mutation_window creates matplotlib figure."""
        from phase2.report_window import _show_mutation_window
        
        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig
        
        # Mock the drivers properly to avoid comparison issues
        mock_driver1 = Mock()
        mock_driver1._last_mutation_time = 10
        mock_driver2 = Mock()
        mock_driver2._last_mutation_time = 50
        
        self.simulation.drivers = [mock_driver1, mock_driver2]
        
        _show_mutation_window(self.simulation)
        
        # Should create figure
        mock_plt.figure.assert_called()


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Create mock simulation."""
        self.simulation = Mock(spec=DeliverySimulation)

    def test_static_summary_zero_requests(self):
        """Summary handles zero total requests gracefully."""
        self.simulation.served_count = 0
        self.simulation.expired_count = 0
        self.simulation.time = 100
        self.simulation.avg_wait = 0.0
        
        summary = _get_static_summary(self.simulation)
        
        self.assertEqual(summary['total_requests'], 0)
        self.assertEqual(summary['service_level'], 0.0)

    def test_static_summary_large_numbers(self):
        """Summary handles large numbers."""
        self.simulation.served_count = 1_000_000
        self.simulation.expired_count = 100_000
        self.simulation.time = 10_000
        self.simulation.avg_wait = 500.5
        
        summary = _get_static_summary(self.simulation)
        
        self.assertEqual(summary['total_requests'], 1_100_000)
        self.assertGreater(summary['service_level'], 0)

    def test_static_summary_fractional_wait(self):
        """Summary preserves fractional wait times."""
        self.simulation.served_count = 50
        self.simulation.expired_count = 10
        self.simulation.time = 100
        self.simulation.avg_wait = 3.14159
        
        summary = _get_static_summary(self.simulation)
        
        self.assertAlmostEqual(summary['final_avg_wait'], 3.14159, places=5)


class TestPlotDataHandling(unittest.TestCase):
    """Test that plot functions handle various data scenarios."""

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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

    @patch('phase2.report_window.HAS_MATPLOTLIB', True)
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
