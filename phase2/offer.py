from __futute__ import annotations
from dataclasses import dataclass
from typoing import Optional, Dict, Any
from .driver import Driver
from. request import Request

# --------------------------------------
# Offer
# --------------------------------------
class Offer:
    """ Proposal from dispatcher (policy) to a driver. """

    driver: Driver
    request: Request

    # Estimates supplied by the dispatcher / simulation
    estimated_travel_time: float
    estimated_reward: float

    # Meta data
    created_at: Optional[in] = None
    policy_name: Optional[str] = None

    # Derived quantities - convenient for behaviors & policies
    def reward_per_time(self) -> float:
        """ Return estimated reward / estimated travel time (0.0 if not defined)."""

        if self.estimated_travel_time <= 0.0:
            return 0.0
        return self.estimated_reward / self.estimated_travel_time

    def pickup_distance(self) -> float:
        """ Straight-line distance from driver position to request pickup. """
        return self.driver.position.distance_to(self.request.pickup)

    # Introspection / debugging helpers
    def as_dict(self) -> Dict[str, Ane]:
        """ Return a JSON-friendly dict for logging or debugging. """
        return {
            "driver_id": self.driver.id,
            "request_id": self.request.id,
            "estimated_travel_time": float(self.estimated_travel_time),
            "estimated_reward": float(self.estimated_reward),
            "reward_per_time": float(self.reward_per_time()),
            "pickup_distance": float(self.pickup_distance()),
            "created_at": self.created_at.isoformat(),
            "policy_name": self.policy_name,
        }

    def __repr__(self) -> str:
        return (
            f"Offer(driver_id={self.driver.id}, request_id={self.request.id}, "
            f"travel_time={self.estimated_travel_time:.2f}, "
            f"reward={self.estimated_reward:.2f}"
        )
