"""
Helper functions for offer creation and analysis.
Centralizes offer calculation logic used by dispatch policies and engine.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from phase2.driver import Driver
    from phase2.request import Request
    from phase2.offer import Offer

# Constants for offer calculations
MIN_SPEED = 1e-6  # Minimum speed to prevent division by zero
EPSILON = 1e-9    # Floating-point tolerance


def calculate_travel_time(driver: "Driver", request: "Request") -> float:
    """
    Calculate estimated travel time from driver to pickup location.
    
    Formula: distance_to_pickup / driver_speed
    
    Args:
        driver: Driver with current position and speed
        request: Request with pickup location
        
    Returns:
        float: Estimated travel time (>= 0)
        
    Raises:
        Implicitly handles zero/negative speed by using MIN_SPEED
        
    Example:
        >>> driver.position = Point(0, 0)
        >>> driver.speed = 2.0
        >>> request.pickup = Point(10, 0)
        >>> calculate_travel_time(driver, request)
        5.0
    """
    distance = driver.position.distance_to(request.pickup)
    speed = max(driver.speed, MIN_SPEED)  # Prevent division by zero
    return distance / speed


def calculate_reward(request: "Request") -> float:
    """
    Calculate estimated reward for completing this delivery.
    
    Formula: distance from pickup to dropoff (straight-line distance)
    
    The reward model assumes earnings are proportional to delivery distance.
    This incentivizes drivers to accept longer deliveries but also ensures
    consistency with the points calculation in driver rewards.
    
    Args:
        request: Request with pickup and dropoff locations
        
    Returns:
        float: Estimated reward (>= 0)
        
    Example:
        >>> request.pickup = Point(0, 0)
        >>> request.dropoff = Point(10, 0)
        >>> calculate_reward(request)
        10.0
    """
    return request.pickup.distance_to(request.dropoff)


def calculate_offer_metrics(driver: "Driver", request: "Request", 
                            policy_name: Optional[str] = None) -> dict:
    """
    Calculate all metrics needed for offer creation.
    
    Combines travel_time and reward calculations into single operation.
    Used by dispatch policies to quickly create offers.
    
    Args:
        driver: Driver making the delivery
        request: Request to be delivered
        policy_name: Optional name of dispatch policy (for tracking)
        
    Returns:
        dict: Contains:
            - travel_time: Estimated time to pickup
            - reward: Estimated earnings
            - reward_per_time: Efficiency ratio
            - pickup_distance: Distance to pickup
            - policy_name: Policy that created offer (if provided)
            
    Example:
        >>> metrics = calculate_offer_metrics(driver, request, "NearestNeighbor")
        >>> metrics["travel_time"]
        5.0
        >>> metrics["reward"]
        10.0
        >>> metrics["reward_per_time"]
        2.0
    """
    travel_time = calculate_travel_time(driver, request)
    reward = calculate_reward(request)
    pickup_distance = driver.position.distance_to(request.pickup)
    
    # Calculate reward per time (with safety check)
    reward_per_time = 0.0 if travel_time <= EPSILON else reward / travel_time
    
    return {
        "travel_time": travel_time,
        "reward": reward,
        "reward_per_time": reward_per_time,
        "pickup_distance": pickup_distance,
        "policy_name": policy_name,
    }


def compare_offers_by_distance(offer1: "Offer", offer2: "Offer") -> int:
    """
    Compare two offers by pickup distance (for sorting).
    
    Used by conflict resolution: when multiple drivers accept the same request,
    the driver closest to pickup gets the offer.
    
    Args:
        offer1: First offer to compare
        offer2: Second offer to compare
        
    Returns:
        int: -1 if offer1 closer, 1 if offer2 closer, 0 if equal (within EPSILON)
        
    Example:
        >>> offers = [offer_far, offer_close, offer_medium]
        >>> sorted_offers = sorted(offers, key=functools.cmp_to_key(compare_offers_by_distance))
        >>> # offer_close will be first
    """
    dist1 = offer1.pickup_distance()
    dist2 = offer2.pickup_distance()
    
    if abs(dist1 - dist2) < EPSILON:
        return 0
    return -1 if dist1 < dist2 else 1


def is_offer_valid(offer: "Offer") -> bool:
    """
    Validate that offer has reasonable metrics for decision-making.
    
    Checks:
    - Travel time is non-negative and finite
    - Reward is non-negative
    - Driver and request are available
    
    Args:
        offer: Offer to validate
        
    Returns:
        bool: True if offer is valid, False otherwise
        
    Example:
        >>> valid_offer = Offer(driver, request, 5.0, 10.0)
        >>> is_offer_valid(valid_offer)
        True
        >>> 
        >>> invalid_offer = Offer(driver, request, -1.0, 10.0)
        >>> is_offer_valid(invalid_offer)
        False
    """
    if offer.estimated_travel_time < 0 or offer.estimated_travel_time == float('inf'):
        return False
    if offer.estimated_reward < 0:
        return False
    if offer.driver is None or offer.request is None:
        return False
    return True


def filter_offers_by_efficiency(offers: list, min_ratio: float) -> list:
    """
    Filter offers to keep only those with reward/time ratio >= threshold.
    
    Useful for filtering low-efficiency offers before presenting to drivers.
    
    Args:
        offers: List of Offer objects to filter
        min_ratio: Minimum acceptable reward_per_time ratio
        
    Returns:
        list: Offers meeting efficiency threshold
        
    Example:
        >>> offers = [offer1, offer2, offer3]  # ratios: 0.5, 2.0, 1.0
        >>> efficient = filter_offers_by_efficiency(offers, min_ratio=1.0)
        >>> len(efficient)
        2  # offer2 and offer3
    """
    return [o for o in offers if o.reward_per_time() >= min_ratio]


def group_offers_by_request(offers: list) -> dict:
    """
    Group offers by request ID.
    
    Used during conflict resolution to find which drivers are competing
    for the same delivery.
    
    Args:
        offers: List of Offer objects
        
    Returns:
        dict: {request_id: [Offer, Offer, ...]}
        
    Example:
        >>> offers = [offer_r1_d1, offer_r1_d2, offer_r2_d1]
        >>> grouped = group_offers_by_request(offers)
        >>> grouped[1]  # request_id 1
        [offer_r1_d1, offer_r1_d2]
        >>> len(grouped[1])
        2  # Two drivers offered same request
    """
    grouped = {}
    for offer in offers:
        request_id = offer.request.id
        if request_id not in grouped:
            grouped[request_id] = []
        grouped[request_id].append(offer)
    return grouped


def select_closest_offer_per_request(offers: list) -> list:
    """
    From competing offers for same request, keep only closest driver.
    
    This implements conflict resolution: when multiple drivers accept the same
    request, give it to the driver nearest the pickup location.
    
    Args:
        offers: List of Offer objects (may contain duplicates by request)
        
    Returns:
        list: One offer per request (closest driver selected)
        
    Example:
        >>> offers = [offer_r1_d_far, offer_r1_d_close, offer_r2_d_any]
        >>> resolved = select_closest_offer_per_request(offers)
        >>> len(resolved)
        2
        >>> resolved[0].driver.id
        2  # The closer driver for request 1
    """
    grouped = group_offers_by_request(offers)
    final = []
    
    for request_id, same_request_offers in grouped.items():
        # Sort by pickup distance and take closest
        same_request_offers.sort(key=lambda o: o.pickup_distance())
        final.append(same_request_offers[0])
    
    return final
