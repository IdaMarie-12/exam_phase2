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
    """Load drivers from a CSV file."""

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
    """Load requests from a CSV file. ests CSV."""

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
    """Generate n random drivers within the grid."""
    
    n = int(n)
    
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
            driver.setdefault("vy", 0.0)
            driver.setdefault("tx", None)
            driver.setdefault("status", "idle")
            driver.setdefault("request_id", None)
            drivers.append(driver)
            break

    return drivers


def generate_requests(start_t: int, out_list: list[dict], req_rate: float,width: int, height: int) -> None:
    """Generate requests using Poisson sampling and append to out_list at start_t."""
    if req_rate < 0:
        raise ValueError(f"Request rate must be non-negative, got {req_rate}")
    
    num_requests = generate_request_count(req_rate)

    for i in range(num_requests):
        request = create_request_dict(f"{start_t}_{i}", start_t, width, height)
        request.setdefault("status", "waiting")
        request.setdefault("driver_id", None)
        request.setdefault("t_wait", 0)
        out_list.append(request)