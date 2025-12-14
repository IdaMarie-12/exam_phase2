import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from unittest.mock import Mock, patch, call
from phase2.simulation import DeliverySimulation
from phase2.driver import Driver
from phase2.request import Request
from phase2.behaviours import GreedyDistanceBehaviour
from phase2.point import Point


# ====================================================================
# TEST FIXTURES (Setup Helpers)
# ====================================================================

def create_mock_driver(driver_id=1, x=0.0, y=0.0, speed=1.5):
    """Create a real Driver object for testing."""
    behaviour = GreedyDistanceBehaviour(max_distance=10.0)
    return Driver(
        id=driver_id,
        position=Point(x, y),
        speed=speed,
        behaviour=behaviour
    )


def create_mock_request(request_id=1, px=0.0, py=0.0, dx=5.0, dy=5.0, creation_time=0):
    """Create a real Request object for testing."""
    return Request(
        id=request_id,
        pickup=Point(px, py),
        dropoff=Point(dx, dy),
        creation_time=creation_time
    )


# ====================================================================
# INITIALIZATION TESTS
# ====================================================================

class TestDeliverySimulationInit(unittest.TestCase):
    """Test suite for DeliverySimulation.__init__
    """

    def setUp(self):
        """Create reusable mock objects."""
        self.drivers = [create_mock_driver(1), create_mock_driver(2)]
        self.gen_mock = Mock()
        self.policy_mock = Mock()
        self.mutation_mock = Mock()

    def test_init_normal_case(self):
        """Valid initialization with all parameters."""
        sim = DeliverySimulation(
            drivers=self.drivers,
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=self.mutation_mock,
            timeout=20
        )
        self.assertEqual(sim.time, 0)
        self.assertEqual(len(sim.drivers), 2)
        self.assertEqual(sim.timeout, 20)
        self.assertEqual(sim.served_count, 0)
        self.assertEqual(sim.expired_count, 0)

    def test_init_empty_drivers_raises_error(self):
        """Empty drivers list should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DeliverySimulation(
                drivers=[],
                dispatch_policy=self.policy_mock,
                request_generator=self.gen_mock,
                mutation_rule=self.mutation_mock
            )
        self.assertIn("at least one driver", str(ctx.exception))

    def test_init_negative_timeout_raises_error(self):
        """Negative timeout should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DeliverySimulation(
                drivers=self.drivers,
                dispatch_policy=self.policy_mock,
                request_generator=self.gen_mock,
                mutation_rule=self.mutation_mock,
                timeout=-5
            )
        self.assertIn("positive", str(ctx.exception))

    def test_init_zero_timeout_raises_error(self):
        """Zero timeout should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DeliverySimulation(
                drivers=self.drivers,
                dispatch_policy=self.policy_mock,
                request_generator=self.gen_mock,
                mutation_rule=self.mutation_mock,
                timeout=0
            )
        self.assertIn("positive", str(ctx.exception))

    def test_init_default_timeout(self):
        """Default timeout is 20."""
        sim = DeliverySimulation(
            drivers=self.drivers,
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=self.mutation_mock
        )
        self.assertEqual(sim.timeout, 20)

    def test_init_attributes_initialized(self):
        """All attributes initialized correctly."""
        sim = DeliverySimulation(
            drivers=self.drivers,
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=self.mutation_mock,
            timeout=15
        )
        self.assertEqual(sim.time, 0)
        self.assertEqual(sim.requests, [])
        self.assertEqual(sim.served_count, 0)
        self.assertEqual(sim.expired_count, 0)
        self.assertEqual(sim.avg_wait, 0.0)
        self.assertEqual(len(sim._wait_samples), 0)
        self.assertIsNotNone(sim.earnings_by_behaviour)

    def test_init_stores_dependencies(self):
        """Stores references to all dependencies."""
        sim = DeliverySimulation(
            drivers=self.drivers,
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=self.mutation_mock
        )
        self.assertEqual(sim.drivers, self.drivers)
        self.assertEqual(sim.dispatch_policy, self.policy_mock)
        self.assertEqual(sim.request_generator, self.gen_mock)
        self.assertEqual(sim.mutation_rule, self.mutation_mock)


# ====================================================================
# TICK ORCHESTRATION TESTS
# ====================================================================

class TestDeliverySimulationTick(unittest.TestCase):
    """Test suite for DeliverySimulation.tick()
    
    Tests 9-phase orchestration and state progression.
    """

    def setUp(self):
        """Create simulation with mocked helpers."""
        self.drivers = [create_mock_driver(1)]
        self.gen_mock = Mock()
        self.policy_mock = Mock()
        self.mutation_mock = Mock()
        
        self.sim = DeliverySimulation(
            drivers=self.drivers,
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=self.mutation_mock,
            timeout=20
        )

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_executes_all_phases(self, mock_mutate, mock_move, mock_assign, 
                                      mock_resolve, mock_collect, mock_proposals, 
                                      mock_expire, mock_gen):
        """Tick calls all 9 phase functions."""
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = []
        mock_collect.return_value = []
        mock_resolve.return_value = []
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        self.sim.tick()
        
        mock_gen.assert_called_once()
        mock_expire.assert_called_once()
        mock_proposals.assert_called_once()
        mock_collect.assert_called_once()
        mock_resolve.assert_called_once()
        mock_assign.assert_called_once()
        mock_move.assert_called_once()
        mock_mutate.assert_called_once()

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_increments_time(self, mock_mutate, mock_move, mock_assign, 
                                   mock_resolve, mock_collect, mock_proposals, 
                                   mock_expire, mock_gen):
        """Time increments by 1 after tick."""
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = []
        mock_collect.return_value = []
        mock_resolve.return_value = []
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        initial_time = self.sim.time
        self.sim.tick()
        self.assertEqual(self.sim.time, initial_time + 1)

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_multiple_times(self, mock_mutate, mock_move, mock_assign, 
                                  mock_resolve, mock_collect, mock_proposals, 
                                  mock_expire, mock_gen):
        """Multiple ticks increment time correctly."""
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = []
        mock_collect.return_value = []
        mock_resolve.return_value = []
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        for i in range(5):
            self.sim.tick()
        self.assertEqual(self.sim.time, 5)

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_passes_simulation_to_helpers(self, mock_mutate, mock_move, mock_assign, 
                                                mock_resolve, mock_collect, mock_proposals, 
                                                mock_expire, mock_gen):
        """Tick passes self to all helper functions."""
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = []
        mock_collect.return_value = []
        mock_resolve.return_value = []
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        self.sim.tick()
        
        # Check that each helper was called with simulation as argument
        mock_mutate.assert_called_with(self.sim)
        mock_move.assert_called_with(self.sim)

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_proposals_passed_to_collect(self, mock_mutate, mock_move, mock_assign, 
                                               mock_resolve, mock_collect, mock_proposals, 
                                               mock_expire, mock_gen):
        """Proposals from phase 3 passed to phase 4."""
        proposals = [("driver", "request")]
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = proposals
        mock_collect.return_value = []
        mock_resolve.return_value = []
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        self.sim.tick()
        
        mock_collect.assert_called_once()
        call_args = mock_collect.call_args
        self.assertEqual(call_args[0][1], proposals)

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_offers_passed_to_resolve(self, mock_mutate, mock_move, mock_assign, 
                                            mock_resolve, mock_collect, mock_proposals, 
                                            mock_expire, mock_gen):
        """Offers from phase 4 passed to phase 5."""
        offers = [Mock()]
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = []
        mock_collect.return_value = offers
        mock_resolve.return_value = []
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        self.sim.tick()
        
        mock_resolve.assert_called_once()
        call_args = mock_resolve.call_args
        self.assertEqual(call_args[0][1], offers)

    @patch('phase2.simulation.gen_requests')
    @patch('phase2.simulation.expire_requests')
    @patch('phase2.simulation.get_proposals')
    @patch('phase2.simulation.collect_offers')
    @patch('phase2.simulation.resolve_conflicts')
    @patch('phase2.simulation.assign_requests')
    @patch('phase2.simulation.move_drivers')
    @patch('phase2.simulation.mutate_drivers')
    def test_tick_final_assignments_passed_to_assign(self, mock_mutate, mock_move, mock_assign, 
                                                      mock_resolve, mock_collect, mock_proposals, 
                                                      mock_expire, mock_gen):
        """Final assignments from phase 5 passed to phase 6."""
        final = [Mock()]
        mock_gen.return_value = None
        mock_expire.return_value = None
        mock_proposals.return_value = []
        mock_collect.return_value = []
        mock_resolve.return_value = final
        mock_assign.return_value = None
        mock_move.return_value = None
        mock_mutate.return_value = None
        
        self.sim.tick()
        
        mock_assign.assert_called_once()
        call_args = mock_assign.call_args
        self.assertEqual(call_args[0][1], final)


# ====================================================================
# SNAPSHOT TESTS
# ====================================================================

class TestGetSnapshot(unittest.TestCase):
    """Test suite for DeliverySimulation.get_snapshot()
    
    Tests JSON serialization and correctness of state snapshot.
    """

    def setUp(self):
        """Create simulation with real driver and request."""
        self.driver = create_mock_driver(1, x=1.0, y=2.0)
        self.gen_mock = Mock()
        self.policy_mock = Mock()
        
        self.sim = DeliverySimulation(
            drivers=[self.driver],
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=None,
            timeout=20
        )

    def test_snapshot_has_required_keys(self):
        """Snapshot contains all required keys."""
        snapshot = self.sim.get_snapshot()
        self.assertIn("time", snapshot)
        self.assertIn("drivers", snapshot)
        self.assertIn("pickups", snapshot)
        self.assertIn("dropoffs", snapshot)
        self.assertIn("statistics", snapshot)

    def test_snapshot_time_correct(self):
        """Snapshot time matches simulation time."""
        self.sim.time = 5
        snapshot = self.sim.get_snapshot()
        self.assertEqual(snapshot["time"], 5)

    def test_snapshot_driver_info(self):
        """Driver snapshot includes required fields."""
        snapshot = self.sim.get_snapshot()
        self.assertEqual(len(snapshot["drivers"]), 1)
        driver_snap = snapshot["drivers"][0]
        
        self.assertEqual(driver_snap["id"], 1)
        self.assertEqual(driver_snap["x"], 1.0)
        self.assertEqual(driver_snap["y"], 2.0)
        self.assertIn("status", driver_snap)
        self.assertIn("rid", driver_snap)
        self.assertIn("tx", driver_snap)
        self.assertIn("ty", driver_snap)

    def test_snapshot_empty_pickups_initially(self):
        """No pickup locations initially."""
        snapshot = self.sim.get_snapshot()
        self.assertEqual(snapshot["pickups"], [])

    def test_snapshot_empty_dropoffs_initially(self):
        """No dropoff locations initially."""
        snapshot = self.sim.get_snapshot()
        self.assertEqual(snapshot["dropoffs"], [])

    def test_snapshot_statistics_keys(self):
        """Statistics dict has required keys."""
        snapshot = self.sim.get_snapshot()
        stats = snapshot["statistics"]
        self.assertIn("served", stats)
        self.assertIn("expired", stats)
        self.assertIn("avg_wait", stats)

    def test_snapshot_initial_statistics(self):
        """Initial statistics are zero."""
        snapshot = self.sim.get_snapshot()
        stats = snapshot["statistics"]
        self.assertEqual(stats["served"], 0)
        self.assertEqual(stats["expired"], 0)
        self.assertEqual(stats["avg_wait"], 0.0)

    def test_snapshot_with_waiting_request(self):
        """Waiting request appears in pickups."""
        request = create_mock_request(1, px=3.0, py=4.0, dx=5.0, dy=6.0)
        self.sim.requests.append(request)
        
        snapshot = self.sim.get_snapshot()
        self.assertEqual(len(snapshot["pickups"]), 1)
        self.assertEqual(snapshot["pickups"][0]["x"], 3.0)
        self.assertEqual(snapshot["pickups"][0]["y"], 4.0)

    def test_snapshot_filters_expired_requests(self):
        """Expired requests not in snapshot."""
        request = create_mock_request(1)
        request.mark_expired(5)
        self.sim.requests.append(request)
        
        snapshot = self.sim.get_snapshot()
        self.assertEqual(len(snapshot["pickups"]), 0)
        self.assertEqual(len(snapshot["dropoffs"]), 0)

    def test_snapshot_with_picked_request(self):
        """Picked request appears in dropoffs."""
        request = create_mock_request(1, dx=7.0, dy=8.0)
        request.status = "PICKED"
        self.sim.requests.append(request)
        
        snapshot = self.sim.get_snapshot()
        self.assertEqual(len(snapshot["dropoffs"]), 1)
        self.assertEqual(snapshot["dropoffs"][0]["x"], 7.0)
        self.assertEqual(snapshot["dropoffs"][0]["y"], 8.0)

    def test_snapshot_multiple_drivers(self):
        """Snapshot includes all drivers."""
        driver2 = create_mock_driver(2, x=5.0, y=6.0)
        self.sim.drivers.append(driver2)
        
        snapshot = self.sim.get_snapshot()
        self.assertEqual(len(snapshot["drivers"]), 2)
        self.assertEqual(snapshot["drivers"][0]["id"], 1)
        self.assertEqual(snapshot["drivers"][1]["id"], 2)

    def test_snapshot_statistics_after_serving(self):
        """Statistics update after serving requests."""
        self.sim.served_count = 3
        self.sim.expired_count = 2
        self.sim.avg_wait = 5.5
        
        snapshot = self.sim.get_snapshot()
        stats = snapshot["statistics"]
        self.assertEqual(stats["served"], 3)
        self.assertEqual(stats["expired"], 2)
        self.assertEqual(stats["avg_wait"], 5.5)

    def test_snapshot_driver_rid_none_initially(self):
        """Driver rid is None when no current request."""
        snapshot = self.sim.get_snapshot()
        self.assertIsNone(snapshot["drivers"][0]["rid"])

    def test_snapshot_is_json_serializable(self):
        """Snapshot can be serialized to JSON."""
        import json
        snapshot = self.sim.get_snapshot()
        json_str = json.dumps(snapshot)
        self.assertIsInstance(json_str, str)


# ====================================================================
# INTEGRATION TESTS
# ====================================================================

class TestDeliverySimulationIntegration(unittest.TestCase):
    """Integration tests with real Driver/Request and mocked policy."""

    def setUp(self):
        """Create simulation with real drivers and requests."""
        self.drivers = [create_mock_driver(1, x=0.0, y=0.0)]
        self.gen_mock = Mock()
        self.gen_mock.maybe_generate = Mock(return_value=[])
        self.policy_mock = Mock()
        self.policy_mock.assign = Mock(return_value=[])
        
        self.sim = DeliverySimulation(
            drivers=self.drivers,
            dispatch_policy=self.policy_mock,
            request_generator=self.gen_mock,
            mutation_rule=None,
            timeout=5
        )

    def test_simulation_with_no_proposals(self):
        """Simulation runs with policy returning no proposals."""
        self.policy_mock.assign.return_value = []
        self.gen_mock.maybe_generate.return_value = []
        
        self.sim.tick()
        
        self.assertEqual(self.sim.time, 1)
        self.policy_mock.assign.assert_called_once()

    def test_simulation_multiple_ticks_no_requests(self):
        """Simulation runs multiple ticks without requests."""
        self.policy_mock.assign.return_value = []
        self.gen_mock.maybe_generate.return_value = []
        
        for _ in range(3):
            self.sim.tick()
        
        self.assertEqual(self.sim.time, 3)
        self.assertEqual(self.sim.served_count, 0)

    def test_simulation_tracks_requests_count(self):
        """Simulation maintains requests list."""
        request = create_mock_request(1)
        self.sim.requests.append(request)
        
        self.assertEqual(len(self.sim.requests), 1)

    def test_simulation_policy_receives_correct_args(self):
        """Policy.assign() called with correct arguments."""
        self.policy_mock.assign.return_value = []
        self.gen_mock.maybe_generate.return_value = []
        
        self.sim.tick()
        
        self.policy_mock.assign.assert_called_once()
        call_args = self.policy_mock.assign.call_args[0]
        self.assertEqual(call_args[0], self.drivers)
        self.assertEqual(call_args[2], 0)  # time=0 initially

    def test_simulation_generator_receives_correct_time(self):
        """Generator.maybe_generate() called with correct time."""
        self.policy_mock.assign.return_value = []
        self.gen_mock.maybe_generate.return_value = []
        
        self.sim.tick()
        self.sim.tick()
        
        calls = self.gen_mock.maybe_generate.call_args_list
        self.assertEqual(calls[0][0][0], 0)
        self.assertEqual(calls[1][0][0], 1)

    def test_simulation_maintains_state_across_ticks(self):
        """State persists across multiple ticks."""
        self.policy_mock.assign.return_value = []
        self.gen_mock.maybe_generate.return_value = []
        
        self.sim.tick()
        self.sim.tick()
        self.sim.tick()
        
        self.assertEqual(self.sim.time, 3)
        self.assertEqual(len(self.sim.drivers), 1)


# ====================================================================
# ERROR HANDLING TESTS
# ====================================================================

class TestDeliverySimulationErrors(unittest.TestCase):
    """Test error handling and validation."""

    def test_init_with_none_drivers(self):
        """None drivers should raise error."""
        with self.assertRaises((ValueError, TypeError, AttributeError)):
            DeliverySimulation(
                drivers=None,
                dispatch_policy=Mock(),
                request_generator=Mock(),
                mutation_rule=None
            )

    def test_single_driver_allowed(self):
        """Single driver in list is valid."""
        driver = create_mock_driver(1)
        sim = DeliverySimulation(
            drivers=[driver],
            dispatch_policy=Mock(),
            request_generator=Mock(),
            mutation_rule=None
        )
        self.assertEqual(len(sim.drivers), 1)

    def test_large_timeout_allowed(self):
        """Large timeout value is allowed."""
        drivers = [create_mock_driver(1)]
        sim = DeliverySimulation(
            drivers=drivers,
            dispatch_policy=Mock(),
            request_generator=Mock(),
            mutation_rule=None,
            timeout=1000
        )
        self.assertEqual(sim.timeout, 1000)

    def test_timeout_boundary_one(self):
        """Timeout of 1 is valid minimum."""
        drivers = [create_mock_driver(1)]
        sim = DeliverySimulation(
            drivers=drivers,
            dispatch_policy=Mock(),
            request_generator=Mock(),
            mutation_rule=None,
            timeout=1
        )
        self.assertEqual(sim.timeout, 1)


if __name__ == '__main__':
    unittest.main()
