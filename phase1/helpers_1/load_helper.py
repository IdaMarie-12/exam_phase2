import os
from typing import Any


def file_exists(path: str) -> None:
    """Raise FileNotFoundError if file does not exist at path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File does not exist: {path}")


def parse_csv_line(line: str) -> list[str]:
    """Parse a CSV line into a list of fields."""
    fields = [field.strip() for field in line.split(',')]
    return [f for f in fields if f]


def read_csv_lines(path: str) -> list[str]:
    """Read all non-comment lines from a CSV file."""
    file_exists(path)
    
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                lines.append(line)
    
    return lines


def parse_float(value: str, field_name: str, line_num: int) -> float:
    """Parse a string as float, raise ValueError on failure."""
    try:
        return float(value)
    except ValueError:
        raise ValueError(
            f"Line {line_num}: '{field_name}' must be a number, got '{value}'"
        )


def validate_coordinate(value: float, field_name: str, line_num: int, min_val: float = 0, max_val: float = 50) -> float:
    """Validate coordinate is within bounds."""
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"Line {line_num}: '{field_name}' = {value} is out of bounds [{min_val}, {max_val}]"
        )
    return value


def validate_time(value: float, line_num: int) -> float:
    """Validate time is non-negative."""
    if value < 0:
        raise ValueError(
            f"Line {line_num}: Time 't' must be non-negative, got {value}"
        )
    return value


def validate_row_length(row: list[str], expected_length: int, line_num: int, file_type: str) -> None:
    """Validate row has expected number of fields."""
    if len(row) < expected_length:
        raise ValueError(
            f"Line {line_num}: {file_type.upper()} row has {len(row)} fields, "
            f"expected at least {expected_length}. Row: {', '.join(row)}"
        )


def parse_driver_row(row: list[str], line_num: int) -> dict[str, Any]:
    """Parse and validate a driver row from CSV."""
    validate_row_length(row, 2, line_num, 'driver')
    
    x = parse_float(row[0], 'x', line_num)
    y = parse_float(row[1], 'y', line_num)
    
    x = validate_coordinate(x, 'x', line_num)
    y = validate_coordinate(y, 'y', line_num)
    
    return {
        "x": x,
        "y": y,
        "speed": 1.0,
        "vx": 0.0,
        "vy": 0.0,
        "target_id": None
    }


def parse_request_row(row: list[str], line_num: int) -> dict[str, Any]:
    """Parse and validate a request row from CSV."""
    validate_row_length(row, 5, line_num, 'request')
    
    t = parse_float(row[0], 't', line_num)
    px = parse_float(row[1], 'px', line_num)
    py = parse_float(row[2], 'py', line_num)
    dx = parse_float(row[3], 'dx', line_num)
    dy = parse_float(row[4], 'dy', line_num)
    
    t = validate_time(t, line_num)
    px = validate_coordinate(px, 'px', line_num)
    py = validate_coordinate(py, 'py', line_num)
    dx = validate_coordinate(dx, 'dx', line_num)
    dy = validate_coordinate(dy, 'dy', line_num)
    
    return {
        "t": int(t),
        "px": px,
        "py": py,
        "dx": dx,
        "dy": dy
    }
