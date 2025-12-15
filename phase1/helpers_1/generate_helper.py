import random
import math
from typing import Any, Union, Tuple, Dict


def generate_request_count(req_rate: float) -> int:
    """Return number of requests to generate using Poisson distribution (Knuth's algorithm)."""
    if req_rate < 0:
        raise ValueError(f"req_rate must be non-negative, got {req_rate}")
    
    # For very small rates, use a simpler approach
    if req_rate == 0:
        return 0
    
    # Knuth's algorithm
    L = math.exp(-req_rate)
    k = 0
    p = 1.0
    
    while p > L:
        k += 1
        p *= random.random()
    
    return k - 1


def create_random_position(width: float, height: float) -> Tuple[float, float]:
    """Generate a random (x, y) position within grid bounds. """
    x = random.uniform(0, width)
    y = random.uniform(0, height)
    return (x, y)


def create_driver_dict(driver_id: int, width: float, height: float) -> Dict[str, Any]:
    """Create a driver dict with random position and speed."""
    x, y = create_random_position(width, height)
    speed = random.uniform(0.8, 1.6)
    
    return {
        "id": driver_id,
        "x": x,
        "y": y,
        "speed": speed,
        "vx": 0.0,
        "vy": 0.0,
        "target_id": None
    }


def create_request_dict(request_id: Union[int, str], time: int, width: float, 
                       height: float) -> Dict[str, Any]:
    """Create a request dict with random pickup/dropoff and time."""
    px, py = create_random_position(width, height)
    dx, dy = create_random_position(width, height)
    
    return {
        "id": request_id,
        "t": time,
        "px": px,
        "py": py,
        "dx": dx,
        "dy": dy,
        "status": "waiting",
        "driver_id": None,
        "t_wait": 0
    }
