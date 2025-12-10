"""
io_mod.py - Input/Output helpers for the dispatch simulation.

Responsibilities
----------------
* Load drivers and requests from CSV files using the custom parsers in
    ``helpers_1.load_helper`` (no stdlib ``csv``).
* Generate synthetic drivers/requests for procedural runs.
* Keep validation in the helpers so bad files fail fast (missing/invalid/out-of-bounds).

Notes
-----
* Driver CSV: two numeric columns (x, y) within the grid bounds expected by the helpers.
* Request CSV: five numeric columns (t, px, py, dx, dy) within bounds; times are integers.
* Generation uses Poisson arrivals for requests to mimic stochastic demand.
"""

import random

from .helpers_1.load_helper import (
    read_csv_lines,
    parse_csv_line,
    parse_driver_row,
    parse_request_row,
)
from .helpers_1.generate_helper import (
    generate_request_count,
    create_driver_dict,
    create_request_dict,
)

def load_drivers(path: str) -> list[dict]:
    """Load drivers from CSV.

    Expected CSV format: two numeric columns (x, y). Bounds and types are
    enforced by ``parse_driver_row``; out-of-bounds or invalid values raise.

    Args:
        path: Filesystem path to a drivers CSV.

    Returns:
        A list of driver dicts with parsed fields and an added sequential ``id``.
    """
    rows = read_csv_lines(path)

    drivers: list[dict] = []
    for line_num, line in enumerate(rows, start=2):
        row = parse_csv_line(line)
        if not row:
            continue

        driver = parse_driver_row(row, line_num)
        driver.setdefault("id", len(drivers))
        drivers.append(driver)

    return drivers


def load_requests(path: str) -> list[dict]:
    """Load requests from CSV.

    Expected CSV format: five numeric columns (t, px, py, dx, dy). Validation
    and bounds checking are handled by ``parse_request_row`` and will raise on
    bad input.

    Args:
        path: Filesystem path to a requests CSV.

    Returns:
        A list of request dicts with parsed fields plus a sequential ``id``.
    """
    rows = read_csv_lines(path)

    try:
        requests: list[dict] = []
        for idx, line in enumerate(rows):
            line_num = idx + 2  # Actual line number in file (line 1 is header)
            row = parse_csv_line(line)
            if not row:
                continue

            req = parse_request_row(row, line_num)
            requests.append({"id": idx, **req})
    except Exception as exc:
        print(f"Error processing requests from {path}: {exc}")
        raise

    return requests


def generate_drivers(n: int, width: int, height: int) -> list[dict]:
    """Generate ``n`` random drivers uniformly within the grid.

    Args:
        n: Number of drivers to create (must be non-negative).
        width: Grid width (max x, inclusive upper bound).
        height: Grid height (max y, inclusive upper bound).

    Returns:
        List of driver dicts with unique ``id`` and random positions in bounds.

    Raises:
        ValueError: If ``n`` is negative.
    """
    if n < 0:
        raise ValueError(f"Number of drivers must be non-negative, got {n}")
    
    drivers: list[dict] = []
    used_positions: set[tuple[int, int]] = set()

    for driver_id in range(n):
        while True:
            x = random.randint(0, max(0, width - 1))
            y = random.randint(0, max(0, height - 1))
            pos = (x, y)
            if pos in used_positions:
                continue
            used_positions.add(pos)
            driver = create_driver_dict(driver_id, width, height)
            driver["x"] = float(x)
            driver["y"] = float(y)
            driver.setdefault("vx", 0.0)
            driver.setdefault("vy", 0.0)
            driver.setdefault("tx", None)
            driver.setdefault("ty", None)
            driver.setdefault("target_id", None)
            driver.setdefault("status", "idle")
            driver.setdefault("request_id", None)
            drivers.append(driver)
            break

    return drivers


def generate_requests(start_t: int, out_list: list[dict], req_rate: float,
                     width: int, height: int) -> None:
    """Append stochastically generated requests to ``out_list`` at time ``start_t``.

    Uses a Poisson draw (``generate_request_count``) with rate ``req_rate`` to
    decide how many requests to create, then builds each via
    ``create_request_dict`` using random positions in the given grid.

    Args:
        start_t: Current simulation tick; stamped into each request.
        out_list: Mutable list to extend with new request dicts.
        req_rate: Expected requests per tick (λ for the Poisson sampler).
        width: Grid width for random positions.
        height: Grid height for random positions.

    Raises:
        ValueError: If ``req_rate`` is negative.
    """
    if req_rate < 0:
        raise ValueError(f"Request rate must be non-negative, got {req_rate}")
    
    num_requests = generate_request_count(req_rate)

    for i in range(num_requests):
        request = create_request_dict(f"{start_t}_{i}", start_t, width, height)
        request.setdefault("status", "waiting")
        request.setdefault("driver_id", None)
        request.setdefault("t_wait", 0)
        out_list.append(request)