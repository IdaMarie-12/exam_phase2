from __future__ import annotations

from typing import List, Dict, Any

from .model import (
    Driver,
    Request,
    Point,
    request_waiting,
    request_assigned,
    request_picked,
    target_tolerance,
)
from .policies import DispatchPolicy, Offer
from .request_gen import RequestGenerator
from .mutation import MutationRule

import math

#-----------------------------------
# Reward & Surge Constants
#-----------------------------------

base_fare = 3.0
distance_fare = 0.5 # per unit of trip distance
waiting_penalty_coef = 0.1 # per tick wait_to_pickup
surge_cap = 3.0 # maximum surge multiplier

#-----------------------------------
# Delivery Simulation
#-----------------------------------
@dataclass
class DeliverySimulation:
    """ Core simulation engine orchestrating drivers, requests and policies. """

    def __init__(self, drivers: List[Driver], requests: List[Request], dispatch_policy: DispatchPolicy, request_generator: RequestGenerator, mutation_rule: MutationRule, timeout: int, width: int, height: int) -> None:
        """ Initialize the simulation engine. """

        self.drivers = drivers
        self.requests = requests
        self.dispatch_policy = dispatch_policy
        self.request_generator = request_generator
        self.mutation_rule = mutation_rule
        self.timeout = timeout
        self.width = width
        self.height = height
        self.time: int = 0

        # Global stats
        self.served.count: int = 0
        self.expired_count: int = 0
        self.total_wait_to_pickup: int = 0
        self.total_time_in_system: float = 0
        self.total.earnings: float = 0

        # Per-tick stats
        self.last_surge_factor: float = 1.0
        self.last_served: int = 0
        self.last_expired: int = 0
        self.last_total_wait_to_pickup: int = 0

        # Time series for plotting
        self.metrics_history: List[Dict[str, Any]] = []

    # Tick progression
    def tick(self) -> None:
        """ Tick the simulation engine by one time step. """

        #  1) time++
        #  2) generate requests
        #  3) expire old waiting requests
        #  4) compute surge factor
        #  5) collect waiting + idle
        #  6) policy.assign(...)
        #  7) build Offers
        #  8) behaviors decide; collect accepted offers
        #  9) resolve conflicts
        # 10) assign requests to drivers
        # 11) move drivers + handle pickup/dropoff and reward
        # 12) apply mutation
        # 13) update averages
        # 14) append to metrics_history

        raise NotImplementedError

    # Compute reward
    def compute_reward(self, req: Request) -> float:
        """ Compute the reward for a delivered request. """
        raise NotImplementedError

    # Snapshot & Metrics
    def get_snapshot(self) -> Dict[str, Any]:
        """ Return a phase 1 like snapshot for the GUI. """

        #  convert Driver objects to dicts with x,y,driver_id,target_id,...
        #  pending = active requests (WAITING/ASSIGNED/PICKED)
        #  dropoffs = coordinates of delivered requests

        raise NotImplementedError

    def get_metrics(self) -> Dict[str, Any]:
        """ Return per-tick metrics for the GUI. """
        return {
            "served": self.last_served,
            "expired": self.last_expired,
            "avg_wait": self.total_wait_to_pickup
        }
