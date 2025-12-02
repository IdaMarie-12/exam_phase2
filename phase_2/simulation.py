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
 """ This class orchestrates the entire simulation.
Attributes:
– time: int– drivers: list[Driver]
– requests: list[Request] (including active and completed)
– dispatch_policy: DispatchPolicy
– request_generator: RequestGenerator
– mutation_rule: MutationRule
– timeout: int (maximum allowed waiting time before expiration)
– statistics such asserved_count,expired_count,a"""

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

        """ Advance the simulation by one time step."""
        # 1. Generate new requests.
        # 2. Update waiting times and mark expired requests.
        # 3. Compute proposed assignments via dispatch_policy.
        # 4. Convert proposals to offers, ask driver behaviours to accept/reject.
        # 5. Resolve conflicts and finalise assignments.
        # 6. Move drivers and handle pickup/dropoff events.
        # 7. Apply mutation_rule to each driver.
        # 8. Increment time.

        raise NotImplementedError

    # Compute reward
    def compute_reward(self, req: Request) -> float:
        """ Compute the reward for a delivered request. """
        raise NotImplementedError

    # Snapshot & Metrics
       def get_snapshot(self) -> dict:
        """Return a dictionary containing:
        - list of driver positions and headings,
        - list of pickup positions (for WAITING/ASSIGNED requests),
        - list of dropoff positions (for PICKED requests),
        - statistics (served, expired, average waiting time).
        Used by the GUI adapter."""

    def get_metrics(self) -> Dict[str, Any]:
        """ Return per-tick metrics for the GUI. """
        return {
            "served": self.last_served,
            "expired": self.last_expired,
            "avg_wait": self.total_wait_to_pickup
        }
