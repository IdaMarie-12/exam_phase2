"""
Helper functions for driver behaviour decision-making.
Centralizes common decision patterns used across behaviour strategies.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.driver import Driver
    from phase2.offer import Offer

# Constants for lazy behaviour
LAZY_MAX_DISTANCE = 5.0  # Lazy drivers accept pickups within this distance


def is_driver_idle(driver: "Driver") -> bool:
    """
    Check if driver is currently idle.
    
    Args:
        driver: The driver to check
        
    Returns:
        bool: True if driver.status == "IDLE", False otherwise
        
    Example:
        >>> driver.status = "IDLE"
        >>> is_driver_idle(driver)
        True
        >>> driver.status = "TO_PICKUP"
        >>> is_driver_idle(driver)
        False
    """
    return driver.status == "IDLE"


def get_pickup_distance(driver: "Driver", offer: "Offer") -> float:
    """
    Calculate distance from driver to pickup location.
    
    Args:
        driver: Current driver position
        offer: Offer containing request with pickup location
        
    Returns:
        float: Distance to pickup (>= 0)
        
    Example:
        >>> driver.position = Point(0, 0)
        >>> offer.request.pickup = Point(3, 4)
        >>> get_pickup_distance(driver, offer)
        5.0
    """
    return driver.position.distance_to(offer.request.pickup)


def check_idle_duration(driver: "Driver", time: int, min_idle_ticks: int) -> bool:
    """
    Check if driver has been idle for at least min_idle_ticks.
    
    Args:
        driver: Driver with idle_since attribute
        time: Current simulation time
        min_idle_ticks: Minimum required idle duration
        
    Returns:
        bool: True if idle_since is set and idle duration >= min_idle_ticks, False otherwise
        
    Example:
        >>> driver.idle_since = 90
        >>> check_idle_duration(driver, time=100, min_idle_ticks=10)
        True
        >>> check_idle_duration(driver, time=95, min_idle_ticks=10)
        False
    """
    idle_since = getattr(driver, "idle_since", None)
    if idle_since is None:
        return False
    return (time - idle_since) >= min_idle_ticks


def check_reward_efficiency(offer: "Offer", threshold: float) -> bool:
    """
    Check if offer's reward-per-time ratio meets or exceeds threshold.
    
    Handles invalid travel times by returning False.
    
    Args:
        offer: Offer with estimated_reward and estimated_travel_time
        threshold: Minimum acceptable reward-per-time ratio
        
    Returns:
        bool: True if reward/travel_time >= threshold, False otherwise (incl. invalid data)
        
    Example:
        >>> offer.estimated_reward = 10.0
        >>> offer.estimated_travel_time = 20.0
        >>> check_reward_efficiency(offer, threshold=0.4)
        True
        >>> check_reward_efficiency(offer, threshold=0.6)
        False
        >>> 
        >>> # Invalid travel time
        >>> offer.estimated_travel_time = 0
        >>> check_reward_efficiency(offer, threshold=0.5)
        False
    """
    if offer.estimated_travel_time <= 0:
        return False
    return (offer.estimated_reward / offer.estimated_travel_time) >= threshold


def check_distance_threshold(distance: float, threshold: float) -> bool:
    """
    Check if distance is within acceptable threshold.
    
    Args:
        distance: Distance to check
        threshold: Maximum acceptable distance
        
    Returns:
        bool: True if distance <= threshold, False otherwise
        
    Example:
        >>> check_distance_threshold(3.5, threshold=5.0)
        True
        >>> check_distance_threshold(5.5, threshold=5.0)
        False
    """
    return distance <= threshold


def validate_behaviour_params(param_name: str, param_value: float, min_value: float = 0.0, strict: bool = False) -> None:
    """
    Validate behaviour parameter value.
    
    Args:
        param_name: Name of parameter (for error message)
        param_value: Value to validate
        min_value: Minimum acceptable value (default 0.0)
        strict: If True, use > instead of >= (default False)
        
    Raises:
        ValueError: If parameter is invalid
        
    Example:
        >>> validate_behaviour_params("max_distance", 5.0, min_value=0.0)  # OK
        >>> validate_behaviour_params("max_distance", -1.0, min_value=0.0, strict=True)  # ValueError
    """
    if strict and param_value <= min_value:
        raise ValueError(f"{param_name} must be > {min_value}, got {param_value}")
    elif not strict and param_value < min_value:
        raise ValueError(f"{param_name} must be >= {min_value}, got {param_value}")
