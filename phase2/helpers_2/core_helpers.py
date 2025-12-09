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
