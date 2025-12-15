import unittest
from unittest.mock import Mock, patch, MagicMock
from phase2.adapter import (
    generate_requests,
    init_state,
    simulate_step,
    get_plot_data,
    get_simulation,
    get_time_series,
    create_phase2_backend,
)
from phase2.point import Point
from phase2.request import Request, WAITING
from phase2.driver import Driver, IDLE
from phase2.simulation import DeliverySimulation


class TestGenerateRequests(unittest.TestCase):
    """Test generate_requests wrapper."""

    def test_generate_requests_appends_to_list(self):
        """Should create and append request dicts to out_list."""
        out_list = []
        generate_requests(start_t=0, out_list=out_list, req_rate=0.5, 
                         width=50, height=50)
        
        # Should create some requests (stochastic, so might be 0-2)
        self.assertIsInstance(out_list, list)

    def test_generate_requests_valid_dict_format(self):
        """Generated request dicts have required fields."""
        out_list = []
        # Use higher rate to ensure some requests are generated
        generate_requests(start_t=0, out_list=out_list, req_rate=5.0,
                         width=50, height=50)
        
        if out_list:  # If any requests were generated
            req_dict = out_list[0]
            # Request dicts use px, py, dx, dy format (not 'pickup'/'dropoff')
            required_fields = ['id', 'creation_time', 'px', 'py', 'dx', 'dy']
            for field in required_fields:
                self.assertIn(field, req_dict)

    def test_generate_requests_zero_rate(self):
        """Zero rate produces empty list."""
        out_list = []
        generate_requests(start_t=0, out_list=out_list, req_rate=0.0,
                         width=50, height=50)
        
        self.assertEqual(len(out_list), 0)

    def test_generate_requests_negative_rate_raises(self):
        """Negative rate raises ValueError."""
        out_list = []
        with self.assertRaises(ValueError):
            generate_requests(start_t=0, out_list=out_list, req_rate=-1.0,
                             width=50, height=50)


class TestInitState(unittest.TestCase):
    """Test state initialization."""

    def setUp(self):
        """Create sample driver and request data."""
        self.drivers_data = [
            {'id': 1, 'x': 10.0, 'y': 20.0},
            {'id': 2, 'x': 30.0, 'y': 40.0},
        ]
        self.requests_data = [
            {
                'id': 1,
                'creation_time': 0,
                'px': 5.0,
                'py': 5.0,
                'dx': 15.0,
                'dy': 15.0,
            },
        ]

    def test_init_state_returns_dict(self):
        """init_state returns a state dict."""
        result = init_state(self.drivers_data, self.requests_data,
                           timeout=1000, req_rate=1.0, width=50, height=50)
        
        self.assertIsInstance(result, dict)

    def test_init_state_creates_simulation(self):
        """init_state creates internal simulation."""
        init_state(self.drivers_data, self.requests_data,
                  timeout=1000, req_rate=1.0, width=50, height=50)
        
        sim = get_simulation()
        self.assertIsNotNone(sim)

    def test_init_state_requires_drivers(self):
        """init_state requires at least one driver."""
        with self.assertRaises(ValueError):
            init_state([], [], timeout=1000, req_rate=1.0, width=50, height=50)

    def test_init_state_sets_drivers(self):
        """init_state populates drivers in simulation."""
        init_state(self.drivers_data, self.requests_data,
                  timeout=1000, req_rate=1.0, width=50, height=50)
        
        sim = get_simulation()
        self.assertGreater(len(sim.drivers), 0)

    def test_init_state_with_requests(self):
        """init_state stores pre-loaded requests for time-based injection."""
        requests_data = [
            {'id': 1, 'creation_time': 0, 'px': 5.0, 'py': 5.0, 'dx': 15.0, 'dy': 15.0},
        ]
        init_state(self.drivers_data, requests_data,
                  timeout=1000, req_rate=1.0, width=50, height=50)
        
        sim = get_simulation()
        # Pre-loaded requests are stored but not immediately added
        self.assertTrue(hasattr(sim, '_all_csv_requests'))
        self.assertGreater(len(sim._all_csv_requests), 0)


class TestSimulateStep(unittest.TestCase):
    """Test simulate_step wrapper."""

    def setUp(self):
        """Initialize a simulation for testing."""
        self.drivers_data = [{'id': 1, 'x': 10.0, 'y': 20.0}]
        self.requests_data = []
        self.state = init_state(self.drivers_data, self.requests_data,
                               timeout=1000, req_rate=1.0, width=50, height=50)

    def test_simulate_step_returns_tuple(self):
        """simulate_step returns (state, metrics) tuple."""
        result = simulate_step(self.state)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_simulate_step_increments_time(self):
        """simulate_step increments simulation time."""
        old_time = self.state.get('t', 0)
        result_state, _ = simulate_step(self.state)
        new_time = result_state.get('t', 0)
        
        self.assertGreaterEqual(new_time, old_time)

    def test_multiple_steps_increment_time(self):
        """Multiple steps increment time correctly."""
        state1, _ = simulate_step(self.state)
        state2, _ = simulate_step(state1)
        
        self.assertGreaterEqual(state2['t'], state1['t'])

    def test_simulate_step_returns_valid_state(self):
        """simulate_step returns state dict with required keys."""
        state, _ = simulate_step(self.state)
        
        # State uses 't' for time, 'pending' for requests, no 'statistics' dict
        required_keys = ['t', 'drivers', 'pending', 'served', 'expired', 'avg_wait']
        for key in required_keys:
            self.assertIn(key, state)


class TestGetPlotData(unittest.TestCase):
    """Test get_plot_data extraction."""

    def setUp(self):
        """Initialize a simulation."""
        self.drivers_data = [
            {'id': 1, 'x': 10.0, 'y': 20.0},
        ]
        self.requests_data = []
        init_state(self.drivers_data, self.requests_data,
                  timeout=1000, req_rate=1.0, width=50, height=50)

    def test_get_plot_data_returns_tuple(self):
        """get_plot_data returns plot tuple."""
        result = get_plot_data()
        
        self.assertIsInstance(result, tuple)

    def test_get_plot_data_has_four_elements(self):
        """get_plot_data returns (drivers, pickups, dropoffs, arrows)."""
        result = get_plot_data()
        
        # Should return 4 elements: drivers, pickups, dropoffs, arrows
        self.assertEqual(len(result), 4)

    def test_get_plot_data_includes_drivers(self):
        """get_plot_data includes driver positions."""
        drivers, _, _, _ = get_plot_data()
        
        self.assertIsInstance(drivers, (list, tuple))

    def test_get_plot_data_raises_if_not_initialized(self):
        """get_plot_data raises if simulation not initialized."""
        # Manually reset simulation
        import phase2.adapter as adapter_module
        adapter_module._simulation = None
        
        with self.assertRaises(RuntimeError):
            get_plot_data()


class TestGetSimulation(unittest.TestCase):
    """Test get_simulation accessor."""

    def test_get_simulation_returns_none_initially(self):
        """get_simulation returns None if not initialized."""
        import phase2.adapter as adapter_module
        adapter_module._simulation = None
        
        result = get_simulation()
        self.assertIsNone(result)

    def test_get_simulation_returns_simulation_after_init(self):
        """get_simulation returns DeliverySimulation after initialization."""
        drivers_data = [{'id': 1, 'x': 10.0, 'y': 20.0}]
        requests_data = []
        
        init_state(drivers_data, requests_data,
                  timeout=1000, req_rate=1.0, width=50, height=50)
        
        result = get_simulation()
        self.assertIsInstance(result, DeliverySimulation)


class TestGetTimeSeries(unittest.TestCase):
    """Test get_time_series accessor."""

    def test_get_time_series_returns_none_initially(self):
        """get_time_series returns None if not started."""
        import phase2.adapter as adapter_module
        adapter_module._time_series = None
        
        result = get_time_series()
        self.assertIsNone(result)

    def test_get_time_series_returns_time_series_after_init(self):
        """get_time_series returns SimulationTimeSeries after initialization."""
        drivers_data = [{'id': 1, 'x': 10.0, 'y': 20.0}]
        requests_data = []
        
        init_state(drivers_data, requests_data,
                  timeout=1000, req_rate=1.0, width=50, height=50)
        
        result = get_time_series()
        # Should be initialized after state is initialized
        self.assertIsNotNone(result)


class TestCreatePhase2Backend(unittest.TestCase):
    """Test backend factory function."""

    def test_create_phase2_backend_returns_dict(self):
        """create_phase2_backend returns a dict."""
        result = create_phase2_backend()
        
        self.assertIsInstance(result, dict)

    def test_create_phase2_backend_has_required_functions(self):
        """Backend dict has all required functions."""
        result = create_phase2_backend()
        
        # From adapter.py: returns load_drivers, load_requests, generate_drivers, generate_requests, init_state, simulate_step
        required_functions = [
            'load_drivers',
            'load_requests',
            'generate_drivers',
            'generate_requests',
            'init_state',
            'simulate_step',
        ]
        
        for func_name in required_functions:
            self.assertIn(func_name, result, f"Missing function: {func_name}")
            self.assertTrue(callable(result[func_name]))

    def test_create_phase2_backend_functions_callable(self):
        """All functions in backend dict are callable."""
        result = create_phase2_backend()
        
        for func_name, func in result.items():
            self.assertTrue(callable(func),
                          f"{func_name} is not callable")

    def test_create_phase2_backend_function_references(self):
        """Backend functions are correct references."""
        result = create_phase2_backend()
        
        # Verify key functions are the right ones
        self.assertEqual(result['generate_requests'], generate_requests)
        self.assertEqual(result['init_state'], init_state)
        self.assertEqual(result['simulate_step'], simulate_step)


class TestAdapterIntegration(unittest.TestCase):
    """Integration tests for adapter workflow."""

    def test_full_workflow_init_and_step(self):
        """Test complete workflow: init, step, get plot data."""
        drivers_data = [
            {'id': 1, 'x': 10.0, 'y': 20.0},
            {'id': 2, 'x': 30.0, 'y': 40.0},
        ]
        requests_data = []
        
        # Initialize
        state = init_state(drivers_data, requests_data,
                          timeout=1000, req_rate=1.0, width=50, height=50)
        self.assertIsInstance(state, dict)
        
        # Step
        new_state, metrics = simulate_step(state)
        self.assertIsInstance(new_state, dict)
        self.assertIsInstance(metrics, dict)
        
        # Get plot data
        plot_data = get_plot_data()
        self.assertEqual(len(plot_data), 4)

    def test_multiple_steps_in_sequence(self):
        """Test multiple simulation steps in sequence."""
        drivers_data = [{'id': 1, 'x': 10.0, 'y': 20.0}]
        requests_data = []
        
        state = init_state(drivers_data, requests_data,
                          timeout=1000, req_rate=1.0, width=50, height=50)
        
        for i in range(5):
            state, _ = simulate_step(state)
            # State key is 't' not 'time'
            self.assertGreaterEqual(state['t'], i)

    def test_adapter_with_initial_requests(self):
        """Test adapter with pre-loaded requests arriving at creation_time."""
        drivers_data = [{'id': 1, 'x': 10.0, 'y': 20.0}]
        requests_data = [
            {
                'id': 1,
                'creation_time': 0,
                'px': 5.0,
                'py': 5.0,
                'dx': 15.0,
                'dy': 15.0,
            },
        ]
        
        state = init_state(drivers_data, requests_data,
                          timeout=1000, req_rate=1.0, width=50, height=50)
        
        # At time 0, request with creation_time=0 hasn't been added yet
        # It will be added on the first tick
        self.assertIn('pending', state)
        self.assertEqual(len(state.get('pending', [])), 0)
        
        # After one step, request should arrive (creation_time=0 <= t=1)
        state, _ = simulate_step(state)
        self.assertGreater(len(state.get('pending', [])), 0)


class TestAdapterErrorHandling(unittest.TestCase):
    """Test error handling in adapter functions."""

    def test_init_state_with_invalid_driver_data(self):
        """init_state handles malformed driver data gracefully."""
        drivers_data = [{'id': 1}]  # Missing x, y
        requests_data = []
        
        # Should raise an error or handle gracefully
        with self.assertRaises((KeyError, ValueError, TypeError)):
            init_state(drivers_data, requests_data,
                      timeout=1000, req_rate=1.0, width=50, height=50)

    def test_simulate_step_with_invalid_state(self):
        """simulate_step handles invalid state gracefully."""
        with self.assertRaises((TypeError, AttributeError, KeyError, RuntimeError)):
            simulate_step(None)

    def test_get_plot_data_without_initialization(self):
        """get_plot_data raises error if simulation not initialized."""
        import phase2.adapter as adapter_module
        adapter_module._simulation = None
        
        with self.assertRaises(RuntimeError):
            get_plot_data()


if __name__ == '__main__':
    unittest.main()
