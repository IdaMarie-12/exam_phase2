from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .driver import Driver
    from .request import Request


@dataclass
class Offer:
    """
    Dispatch proposal from policy to a driver for a delivery.
    
    An Offer represents a delivery proposal created by the dispatch policy.
    It contains all information a driver's behaviour needs to decide whether
    to accept or reject the delivery:
    - Which driver and request are involved
    - Estimated travel time to reach pickup
    - Estimated reward for completing delivery
    - Metadata about when and by whom the offer was created
    
    Offers are immutable once created (dataclass frozen=False for simplicity).
    They serve as the interface between dispatch logic and driver decision-making.
    
    Attributes:
        driver: The driver being offered the delivery
        request: The delivery request being proposed
        estimated_travel_time: Time to reach pickup (distance / speed)
        estimated_reward: Expected earnings (typically pickup-to-dropoff distance)
        created_at: Timestamp when offer was created (for tracking)
        policy_name: Name of dispatch policy that created offer (for metrics)
        
    Key Calculations:
        - reward_per_time: Earnings efficiency = reward / travel_time
        - pickup_distance: Distance from driver to pickup location
        
    Example:
        >>> offer = Offer(driver, request, travel_time=5.0, reward=10.0)
        >>> offer.reward_per_time()
        2.0
        >>> offer.pickup_distance()
        3.5
        >>> if driver.behaviour.decide(driver, offer, time=100):
        ...     # Driver accepted the offer - engine will assign request
        
    Lifecycle:
        1. Policy creates offer: Offer(driver, request, travel_time, reward)
        2. Engine presents to driver: driver.behaviour.decide()
        3. If accepted: Engine calls driver.assign_request()
        4. If rejected: Offer is discarded, next offer tried
    """

    driver: Driver
    request: Request
    estimated_travel_time: float
    estimated_reward: float
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    policy_name: Optional[str] = None

    def reward_per_time(self) -> float:
        """
        Calculate reward earned per unit time for this offer.
        
        Formula: estimated_reward / estimated_travel_time
        
        Used by earnings-focused behaviours to evaluate offer attractiveness.
        Returns 0.0 for invalid travel times (prevents division by zero).
        
        Returns:
            float: Earnings per time unit (>= 0.0)
            
        Example:
            >>> offer = Offer(..., estimated_travel_time=10.0, estimated_reward=5.0)
            >>> offer.reward_per_time()
            0.5
            >>> 
            >>> offer2 = Offer(..., estimated_travel_time=0.0, estimated_reward=5.0)
            >>> offer2.reward_per_time()  # Invalid travel time
            0.0
        """
        if self.estimated_travel_time <= 0.0:
            return 0.0
        return self.estimated_reward / self.estimated_travel_time

    def pickup_distance(self) -> float:
        """
        Calculate distance from driver's current position to pickup location.
        
        Used by distance-based behaviours to evaluate offer attractiveness.
        This is the actual distance the driver must travel to reach the customer.
        
        Returns:
            float: Distance from driver to pickup (>= 0.0)
            
        Example:
            >>> driver.position = Point(0, 0)
            >>> offer.request.pickup = Point(3, 4)
            >>> offer.pickup_distance()
            5.0
        """
        return self.driver.position.distance_to(self.request.pickup)

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert offer to dictionary for serialization and analysis.
        
        Useful for:
        - Logging offer decisions to files
        - Analyzing offer patterns
        - Comparing driver behaviours across offers
        - Metrics collection
        
        Returns:
            Dict[str, Any]: Serializable dictionary with all offer details
            
        Example:
            >>> offer_dict = offer.as_dict()
            >>> offer_dict["driver_id"]
            1
            >>> offer_dict["reward_per_time"]
            2.0
        """
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
        """
        Return concise string representation for debugging.
        
        Shows key metrics in compact format for quick inspection of offers.
        
        Returns:
            str: Formatted representation
            
        Example:
            >>> offer = Offer(driver_1, request_42, 5.0, 10.0)
            >>> repr(offer)
            'Offer(driver_id=1, request_id=42, travel_time=5.00, reward=10.00)'
        """
        return (
            f"Offer(driver_id={self.driver.id}, request_id={self.request.id}, "
            f"travel_time={self.estimated_travel_time:.2f}, "
            f"reward={self.estimated_reward:.2f})"
        )
