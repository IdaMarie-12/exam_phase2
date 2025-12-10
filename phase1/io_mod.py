"""
io_mod.py - Input/Output module for loading and generating simulation entities.

This module provides functions to:
1. Load drivers and requests from CSV files
2. Generate random drivers and requests (with Poisson-distributed request arrival)
3. Support initialization of simulation data

The module does NOT use the csv standard library module. Instead, it manually
parses CSV files using helpers from helpers_1/load_helper.py for validation.

Generation uses Poisson distribution for realistic request arrival patterns.
"""

from helpers_1.load_helper import (
    read_csv_lines,
    parse_csv_line,
    parse_driver_row,
    parse_request_row,
)
from helpers_1.generate_helper import (
    generate_request_count,
    create_driver_dict,
    create_request_dict,
)


def load_drivers(path: str) -> list[dict]:
    """
    Load driver records from a CSV file.
    
    The CSV file should have two columns (x, y) representing initial positions.
    
    Parameters:
        path (str): Path to the drivers CSV file
        
    Returns:
        list[dict]: List of driver dictionaries with keys:
            - x, y: Initial position
            - speed: Default speed (1.0)
            - vx, vy: Initial velocities (0.0)
            - target_id: Initially None
            
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If any row has invalid data or format
        
    Example:
        >>> drivers = load_drivers('data/drivers.csv')
        >>> len(drivers)
        10
        >>> drivers[0]['x']
        11.0
    """
    lines = read_csv_lines(path)
    drivers = []
    
    for line_num, line in enumerate(lines, start=2):  # Start at 2 (line 1 is skipped for header)
        row = parse_csv_line(line)
        
        if not row:  # Skip empty rows
            continue
        
        driver = parse_driver_row(row, line_num)
        drivers.append(driver)
    
    return drivers


def load_requests(path: str) -> list[dict]:
    """
    Load request records from a CSV file.
    
    The CSV file should have five columns (t, px, py, dx, dy) representing:
        - t: Time when request appears
        - px, py: Pickup location
        - dx, dy: Delivery location
    
    Parameters:
        path (str): Path to the requests CSV file
        
    Returns:
        list[dict]: List of request dictionaries with keys:
            - id: Request ID (index)
            - t: Appearance time
            - px, py: Pickup coordinates
            - dx, dy: Delivery coordinates
            - status: Initially "waiting"
            - driver_id: Initially None
            - t_wait: Initially 0
            
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If any row has invalid data or format
        
    Example:
        >>> requests = load_requests('data/requests.csv')
        >>> requests[0]['t']
        0
        >>> requests[0]['px']
        1.0
    """
    lines = read_csv_lines(path)
    requests = []
    
    for idx, line in enumerate(lines):
        line_num = idx + 2  # Actual line number in file (line 1 is header)
        row = parse_csv_line(line)
        
        if not row:  # Skip empty rows
            continue
        
        request_data = parse_request_row(row, line_num)
        
        request = {
            "id": idx,
            "t": request_data["t"],
            "px": request_data["px"],
            "py": request_data["py"],
            "dx": request_data["dx"],
            "dy": request_data["dy"],
            "status": "waiting",
            "driver_id": None,
            "t_wait": 0
        }
        requests.append(request)
    
    return requests


def generate_drivers(n: int, width: int, height: int) -> list[dict]:
    """
    Generate n random drivers uniformly distributed within the grid.
    
    Each driver is assigned a unique ID and random initial position and speed.
    Drivers are created with zero velocity and no assigned target, ready to
    accept delivery requests.
    
    Parameters:
        n (int): Number of drivers to generate
        width (int): Width of the simulation grid (max x-coordinate)
        height (int): Height of the simulation grid (max y-coordinate)
        
    Returns:
        list[dict]: List of n driver dictionaries with keys:
            - id: Unique integer identifier (0 to n-1)
            - x, y: Random initial position within [0, width] × [0, height]
            - speed: Random speed between 0.8 and 1.6 units/tick
            - vx, vy: Initial velocities (0.0)
            - target_id: Initially None (no assigned request)
            
    Raises:
        ValueError: If n < 0
        
    Example:
        >>> drivers = generate_drivers(5, 50, 30)
        >>> len(drivers)
        5
        >>> all(0 <= d['x'] <= 50 for d in drivers)
        True
        >>> all(0.8 <= d['speed'] <= 1.6 for d in drivers)
        True
    """
    if n < 0:
        raise ValueError(f"Number of drivers must be non-negative, got {n}")
    
    drivers = []
    for driver_id in range(n):
        driver = create_driver_dict(driver_id, width, height)
        drivers.append(driver)
    
    return drivers


def generate_requests(start_t: int, out_list: list[dict], req_rate: float,
                     width: int, height: int) -> None:
    """
    Generate new requests at the given time step and append them to out_list.
    
    New requests are generated stochastically using a Poisson distribution with
    rate parameter req_rate. This models realistic food delivery systems where
    orders arrive randomly over time with an average rate of req_rate orders
    per time unit (minute).
    
    On average, the function generates req_rate requests per call. Actual count
    varies stochastically (sometimes 0, sometimes 2-3, averaging to req_rate).
    
    This function is called by simulate_step() at each time step to continuously
    generate new requests during simulation, replacing those from a finite CSV
    file when the file is exhausted.
    
    Parameters:
        start_t (int): Current simulation time (tick/minute when requests are created)
        out_list (list[dict]): List to append newly created requests to (modified in-place)
        req_rate (float): Expected average number of new requests per time step (λ for Poisson)
                         - 0.5 → ~0.5 requests per step
                         - 2.0 → ~2 requests per step
                         - 5.0 → ~5 requests per step
        width (int): Grid width (for random position generation)
        height (int): Grid height (for random position generation)
        
    Returns:
        None (modifies out_list in-place by appending new Request dictionaries)
        
    Raises:
        ValueError: If req_rate < 0
        
    Example:
        >>> requests = []
        >>> generate_requests(0, requests, 2.0, 50, 30)
        >>> len(requests) > 0  # Typically 1-3 for req_rate=2.0
        True
        >>> requests[0]['t']
        0
        >>> 0 <= requests[0]['px'] <= 50
        True
        
    Notes:
        - Poisson distribution ensures realistic arrival patterns
        - Over 100 steps with req_rate=2.0, ~200 requests total
        - Request ID format: "{start_t}_{counter}" for uniqueness
        - All generated requests start with status "waiting" and no driver assigned
    """
    if req_rate < 0:
        raise ValueError(f"Request rate must be non-negative, got {req_rate}")
    
    # Generate number of requests using Poisson distribution
    num_requests = generate_request_count(req_rate)
    
    # Create each request with random pickup and delivery locations
    for i in range(num_requests):
        request = create_request_dict(f"{start_t}_{i}", start_t, width, height)
        out_list.append(request)