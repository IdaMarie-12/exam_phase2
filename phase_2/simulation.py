from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, TYPE_CHECKING

from phase2.model import Driver, Request, REQUEST_WAITING, REQUEST_ASSIGNED, REQUEST_PICKED
from phase2.policies import DispatchPolicy, Offer
from phase2.mutation import MutationRule
from phase2.request_gen import RequestGenerator

if TYPE_CHECKING:
    from phase2.model import Point

#-----------------------------------
# Delivery Simulation
#-----------------------------------
@dataclass
class DeliverySimulation:
    """ Core simulation engine orchestrating drivers, requests and policies. """

    drivers: List[Driver]
    requests: List[Request]
    dispatch_policy: DispatchPolicy
    request_generator: RequestGenerator
    mutation_rule: MutationRule

    timeout: int
    width: int
    height: int

    time: int = 0
    served_count: int = 0
    expired_count: int = 0
    total_wait_time: float = 0.0

    metrics_history: List[Dict] = field(default_factory = list) # Optional, track per tick metrics

    def tick(self) -> None:
        """ Advance the simulation by one time step."""
        self.time += 1

        # 1. Generate new requests
        # 2. Update waiting time & expire requests
        # 3. Compute proposed assignments via dispatch_policy
        # 4. Convert assignments to offers and ask behaviors to accept/reject
        # 5. Move drivers and handle pickup/dropoff events
        # 6. Apply mutation rule to each driver
        # 7. Collect metrics for this tick

