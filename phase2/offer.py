from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .driver import Driver
from .request import Request
from datetime import datetime

@dataclass
class Offer:
    """Proposal from dispatcher (policy) to a driver."""
    driver: Driver
    request: Request
    estimated_travel_time: float
    estimated_reward: float
    created_at: Optional[datetime] = None
    policy_name: Optional[str] = None

    def reward_per_time(self) -> float:
        if self.estimated_travel_time <= 0.0:
            return 0.0
        return self.estimated_reward / self.estimated_travel_time

    def pickup_distance(self) -> float:
        return self.driver.position.distance_to(self.request.pickup)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "driver_id": self.driver.id,
            "request_id": self.request.id,
            "estimated_travel_time": float(self.estimated_travel_time),
            "estimated_reward": float(self.estimated_reward),
            "reward_per_time": float(self.reward_per_time()),
            "pickup_distance": float(self.pickup_distance()),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "policy_name": self.policy_name,
        }

    def __repr__(self) -> str:
        return (
            f"Offer(driver_id={self.driver.id}, request_id={self.request.id}, "
            f"travel_time={self.estimated_travel_time:.2f}, "
            f"reward={self.estimated_reward:.2f})"
        )
