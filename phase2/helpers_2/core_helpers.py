"""
Core helper utilities for Phase 2 simulation.
Only includes functions directly used by Phase 2 classes.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.point import Point

# Constants
EPSILON = 1e-9


def is_at_target(current: "Point", target: "Point", tolerance: float = EPSILON) -> bool:
    """
    Check if current position is at (or very close to) target using epsilon tolerance.
    
    Used by Driver.step() to detect arrival at pickup/dropoff with floating-point safety.
    
    Args:
        current: Current position
        target: Target position  
        tolerance: Distance tolerance (default 1e-9)
        
    Returns:
        bool: True if distance <= tolerance
        
    Example:
        >>> is_at_target(Point(5.0, 5.0), Point(5.0, 5.0 + 1e-10))
        True
    """
    return current.distance_to(target) <= tolerance


def move_towards(current: "Point", target: "Point", distance: float) -> "Point":
    """
    Move point towards target by given distance, preventing overshoot.
    
    Used by Driver.step() to update position towards pickup/dropoff.
    Returns new Point without modifying the original (safe with frozen=True).
    
    Args:
        current: Starting position
        target: Target position
        distance: Distance to move
        
    Returns:
        Point: New position after movement
        
    Raises:
        ValueError: If distance < 0
        
    Example:
        >>> move_towards(Point(0, 0), Point(10, 0), 5.0)
        Point(5.0, 0.0)
    """
    from phase2.point import Point  # Import here to avoid circular import
    
    if distance < 0:
        raise ValueError(f"Distance must be non-negative, got {distance}")
    
    total_dist = current.distance_to(target)
    
    # Already at target
    if total_dist < EPSILON:
        return Point(current.x, current.y)
    
    # Fraction of distance to move (clamped to 1.0 to prevent overshoot)
    frac = min(1.0, distance / total_dist)
    
    # Linear interpolation
    dx = (target.x - current.x) * frac
    dy = (target.y - current.y) * frac
    
    return Point(current.x + dx, current.y + dy)


def calculate_points(fare: float, wait_time: int) -> float:
    """
    Calculate driver points earned from a trip.
    Formula: points = max(0, fare - 0.1 * wait_time)
    
    Used by Driver.complete_dropoff() to calculate points for mutation.
    
    Args:
        fare: Trip fare (distance)
        wait_time: Request wait time (ticks)
        
    Returns:
        float: Points earned (>= 0)
        
    Example:
        >>> calculate_points(10.0, 5)
        9.5
        >>> calculate_points(2.0, 50)  # Penalized too long
        0.0
    """
    return max(0.0, fare - 0.1 * wait_time)


def record_assignment_start(history: list, request_id: int, current_time: int) -> None:
    """
    Record the start of a new delivery trip in history.
    
    Called when a request is assigned to track when the driver
    begins working on this delivery.
    
    Args:
        history: Driver's history list to append to
        request_id: ID of the request being assigned
        current_time: Time when assignment occurs
        
    Example:
        >>> history = []
        >>> record_assignment_start(history, 42, 100)
        >>> history[0]["request_id"]
        42
    """
    history.append({
        "request_id": request_id,
        "start_time": current_time,
    })


def record_completion(history: list, request_id: int, creation_time: int,
                     time: int, fare: float, wait: int, points: float) -> None:
    """
    Record trip completion with full trip metrics in history.
    
    Adds a comprehensive record of the completed delivery including
    fare earned, wait time, points earned, and timing information.
    
    Args:
        history: Driver's history list to append to
        request_id: ID of the completed request
        creation_time: Time when request was created
        time: Time when dropoff was completed
        fare: Amount earned (pickup-to-dropoff distance)
        wait: Wait time for customer pickup
        points: Points earned (max(0, fare - 0.1 * wait))
        
    Example:
        >>> history = []
        >>> record_completion(history, 42, 0, 100, 15.0, 5, 14.5)
        >>> history[0]["fare"]
        15.0
    """
    history.append({
        "time": time,
        "fare": fare,
        "wait": wait,
        "points": points,
        "request_id": request_id,
        "start_time": creation_time,
    })


def finalize_trip(earnings: list, points_list: list, fare: float, points: float) -> None:
    """
    Update aggregates for trip finalization.
    
    Updates driver's total earnings and points by appending values to
    the respective lists (allows functional style updates).
    
    Args:
        earnings: List to accumulate earnings (typically [total_earnings])
        points_list: List to accumulate points (typically [total_points])
        fare: Fare amount to add to earnings
        points: Points amount to add to total
        
    Example:
        >>> earnings = [100.0]
        >>> points_list = [50.0]
        >>> finalize_trip(earnings, points_list, 15.0, 10.5)
        >>> earnings[0]
        115.0
        >>> points_list[0]
        60.5
    """
    earnings[0] += fare
    points_list[0] += points
