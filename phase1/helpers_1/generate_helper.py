"""
generate_helper.py - Helper functions for generating random drivers and requests.

This module provides utility functions for stochastic generation of simulation entities:
1. Poisson-distributed request generation
2. Random driver creation
3. Random request creation
"""

import random
import math
from typing import Any


def generate_request_count(req_rate: float) -> int:
    """
    Generate the number of requests to create at this time step using Poisson distribution.
    
    This mimics real-world event arrival patterns where requests arrive stochastically
    over time, with an average rate of req_rate requests per time unit.
    
    Parameters:
        req_rate (float): Expected average number of requests per time step (λ parameter)
        
    Returns:
        int: Number of requests to generate (usually 0, 1, or 2 for typical req_rate)
        
    Implementation Notes:
        - Uses Knuth's algorithm for Poisson distribution
        - For small req_rate (< 30), this is efficient and accurate
        - On average, over many steps, generates req_rate requests per step
        
    Example:
        >>> random.seed(42)
        >>> counts = [generate_request_count(2.0) for _ in range(100)]
        >>> sum(counts) / len(counts)  # Should be approximately 2.0
        1.98
    """
    # Implement Poisson distribution using Knuth's algorithm
    # Since Python's random module doesn't have poisson, we implement it manually
    L = math.exp(-req_rate)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def create_random_position(width: float, height: float) -> tuple[float, float]:
    """
    Generate a random position uniformly within the grid bounds.
    
    Parameters:
        width (float): Maximum x-coordinate (grid width)
        height (float): Maximum y-coordinate (grid height)
        
    Returns:
        tuple[float, float]: (x, y) position where 0 <= x <= width, 0 <= y <= height
        
    Example:
        >>> random.seed(42)
        >>> x, y = create_random_position(50, 30)
        >>> 0 <= x <= 50 and 0 <= y <= 30
        True
    """
    x = random.uniform(0, width)
    y = random.uniform(0, height)
    return (x, y)


def create_driver_dict(driver_id: int, width: float, height: float) -> dict[str, Any]:
    """
    Create a single driver dictionary with random initial position and speed.
    
    Drivers are created with:
    - Random position uniformly in the grid
    - Random speed between 0.8 and 1.6 units/tick (realistic delivery speeds)
    - Zero initial velocity
    - No assigned target
    
    Parameters:
        driver_id (int): Unique driver identifier
        width (float): Grid width
        height (float): Grid height
        
    Returns:
        dict[str, Any]: Driver dictionary with keys:
            - id: Unique identifier (matches Phase 1 spec)
            - x, y: Initial position
            - speed: Random speed in [0.8, 1.6]
            - vx, vy: Initial velocities (0.0)
            - target_id: Initially None
            
    Example:
        >>> driver = create_driver_dict(0, 50, 30)
        >>> driver['id']
        0
        >>> 0.8 <= driver['speed'] <= 1.6
        True
    """
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


def create_request_dict(request_id: int | str, time: int, width: float, 
                       height: float) -> dict[str, Any]:
    """
    Create a single request dictionary with random pickup and delivery locations.
    
    Requests are created with:
    - Random pickup location uniformly in the grid
    - Random delivery location uniformly in the grid (can be same as pickup)
    - Creation time (when request appears in system)
    - Initial status "waiting"
    - No assigned driver
    
    Parameters:
        request_id (int | str): Unique request identifier (usually timestamp_counter)
        time (int): Current simulation time (when request appears)
        width (float): Grid width
        height (float): Grid height
        
    Returns:
        dict[str, Any]: Request dictionary with keys:
            - id: Request identifier
            - t: Appearance time (creation time)
            - px, py: Pickup location
            - dx, dy: Delivery location
            - status: Initially "waiting"
            - driver_id: Initially None
            - t_wait: Initially 0 (time spent waiting)
            
    Example:
        >>> request = create_request_dict("0_0", 0, 50, 30)
        >>> request['t']
        0
        >>> 0 <= request['px'] <= 50
        True
    """
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
