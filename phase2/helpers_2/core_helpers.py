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
    if distance < 0:
        raise ValueError(f"Distance must be non-negative, got {distance}")
    
    total_dist = current.distance_to(target)
    
    # Already at target
    if total_dist < EPSILON:
        return current
    
    # Fraction of distance to move (clamped to 1.0 to prevent overshoot)
    frac = min(1.0, distance / total_dist)
    
    # Linear interpolation: direction vector scaled by fraction
    # Start with current position and accumulate displacement using __iadd__
    result = current
    result += frac * (target - current)
    
    return result


def compute_relative_position(current: "Point", reference: "Point") -> "Point":
    """
    Compute relative position by subtracting a reference point from current position.
    
    Useful for computing displacement vectors or position deltas in coordinate systems.
    This demonstrates __isub__ for position offset computation.
    
    Returns new Point without modifying the original (safe with frozen=True).
    
    Args:
        current: Current position
        reference: Reference position to subtract from current
        
    Returns:
        Point: Displacement vector (current - reference)
        
    Example:
        >>> compute_relative_position(Point(5, 5), Point(2, 3))
        Point(3.0, 2.0)
    """
    # Compute displacement: subtract reference from current using __isub__
    # This shows __isub__ in a realistic context: computing position deltas
    result = current
    result -= reference
    
    return result


def distance_between(point_a: "Point", point_b: "Point") -> float:
    """
    Compute distance between two points using relative position calculation.
    
    Demonstrates using __isub__ to compute displacement, then measuring its magnitude.
    Useful for conflict resolution and nearest-neighbor matching in dispatch algorithms.
    
    Args:
        point_a: First position
        point_b: Second position
        
    Returns:
        float: Euclidean distance between points
        
    Example:
        >>> distance_between(Point(0, 0), Point(3, 4))
        5.0
    """
    # Compute displacement vector using __isub__
    displacement = compute_relative_position(point_a, point_b)
    
    # Measure magnitude of displacement (distance from origin)
    return displacement.distance_to(point_b.__class__(0, 0))


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
                     time: int, fare: float, wait: int) -> None:
    """
    Record trip completion with trip metrics in history.
    
    Args:
        history: Driver's history list to append to
        request_id: ID of the completed request
        creation_time: Time when request was created
        time: Time when dropoff was completed
        fare: Amount earned (pickup-to-dropoff distance)
        wait: Wait time for customer pickup
    """
    history.append({
        "time": time,
        "fare": fare,
        "wait": wait,
        "request_id": request_id,
        "start_time": creation_time,
    })


# ============================================================
# Mutation helpers (used by mutation.py)
# ============================================================

def get_driver_history_window(history: list, window: int) -> list:
    """Return last window entries from history."""
    return history[-window:] if history else []


def calculate_average_fare(history: list) -> float | None:
    """Calculate average fare from history entries. Returns None if empty or no completed trips.
    Only counts entries with actual fare values (completed trips, not pickups)."""
    if not history:
        return None
    # Only include entries that have a fare (completed deliveries, not pickups)
    fares = [entry.get("fare") for entry in history if entry.get("fare") is not None]
    return sum(fares) / len(fares) if fares else None


def get_behaviour_name(behaviour) -> str:
    """Return the class name of a behaviour instance."""
    return type(behaviour).__name__
