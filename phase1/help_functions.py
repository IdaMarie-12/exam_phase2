import math
from typing import List, Dict, Tuple, Optional

# -----------------
# Helper functions
# -----------------

# distance between two points
def distance(a: Tuple[float, float], b:Tuple[float, float]) -> float:
    """ Compute the Euclidean distance between two points (x, y)

    Parameters:
        a: First point (x, y)
        b: Second point (x, y)

    Returns:
        float: Euclidean distance

    Example:
        >>> distance((0, 0), (3, 4))
        5.0
    """

    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.hypot(dx, dy)

# Move driver one step for each unit of time
def move_driver_towards(driver: Dict, target: Tuple[float, float], speed: float) -> None:
    """ Move driver one step toward the target by speed distance. Prevents overshooting the target.

    Parameters:
        driver (Dict): Driver dictionary
        target (Tuple[float, float]): Target position
        speed (float): Speed of the driver

    Updates:
        driver['x'], driver['y'] (new position)
        driver['vx'], driver['vy'] (new movement vector)

    Returns:
        None
    """
    dx = target[0] - driver['x']
    dy = target[1] - driver['y']
    dist = math.hypot(dx, dy)

    # Already at target
    if dist == 0:
        driver['vx'], driver['vy'] = 0.0, 0.0
        return

    # Prevent overshoot
    step = min(speed, dist)
    ux, uy = dx / dist, dy / dist
    vx, vy = ux * step, uy * step

    # Update position and velocity
    driver['x'] += vx
    driver['y'] += vy
    driver['vx'], driver['vy'] = vx, vy


# Check if driver is at target
def at_target(driver: Dict, target: Tuple[float, float], tolerance: float = 0.5) -> bool:
    """ Check if driver is at target location (within tolerance)

    Parameters:
        driver (Dict): Driver dictionary
        target (Tuple[float, float]): Target position
        tolerance (float): Tolerance

    Returns:
        bool: True if driver is at target, False otherwise
    """
    return (
            abs(driver['x'] - target[0]) < tolerance
            and abs(driver['y'] - target[1]) < tolerance
    )


# Reset driver after completing a delivery
def clear_driver_target(driver: Dict) -> None:
    """ Reset driver after completing a delivery:
        - Stop velocity (vx, vy = 0)
        - Clear target (tx, ty = None)
        - Mark as unassigned (target_id = None)

    Parameter:
        driver (Dict): Driver dictionary
    """
    driver['vx'] = 0.0
    driver['vy'] = 0.0
    driver['tx'] = None
    driver['ty'] = None
    driver['target_id'] = None

# Find nearest driver
def find_nearest_avb_driver(drivers: List[Dict], point: Tuple[float, float]) -> Optional[Dict]:
    """ Find the nearest driver who is free (target_id = None) to a given point.

    Parameters:
        drivers (List[Dict]): List of drivers
        point (Tuple[float, float]): Point to find nearest driver to

    Returns:
        Optional[Dict]: Driver match
        None if no match found
    """
    free_drivers = [d for d in drivers if d.get('target_id') is None]
    if not free_drivers:
        return None
    return min(free_drivers, key=lambda d: distance((d['x'], d['y']), point))