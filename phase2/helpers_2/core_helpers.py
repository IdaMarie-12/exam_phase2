from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phase2.point import Point

# Constants
EPSILON = 1e-9


def is_at_target(current: "Point", target: "Point", tolerance: float = EPSILON) -> bool:
    """Return True if current is at target within tolerance."""
    return current.distance_to(target) <= tolerance


def move_towards(current: "Point", target: "Point", distance: float) -> "Point":
    """Move current towards target by distance."""
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


def record_assignment_start(history: list, request_id: int, current_time: int) -> None:
    """Record start of delivery trip in history."""
    history.append({
        "request_id": request_id,
        "start_time": current_time,
    })


def record_completion(history: list, request_id: int, creation_time: int,
                     time: int, fare: float, wait: int) -> None:
    """Record trip completion with metrics in history."""
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
    """Return average fare from history."""
    if not history:
        return None
    fares = [entry.get("fare", 0.0) for entry in history]
    return sum(fares) / len(fares) if fares else None


def get_behaviour_name(behaviour) -> str:
    """Return class name of behaviour instance."""
    return type(behaviour).__name__
