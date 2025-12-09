"""
load_helper.py - Helper functions for loading and parsing CSV files without using the csv module.

This module provides utility functions for:
1. Reading and parsing CSV files manually (without csv module)
2. Validating data types and constraints
3. Error handling with informative messages
"""

import os
from typing import Any


def file_exists(path: str) -> None:
    """
    Verify that a file exists at the given path.
    
    Parameters:
        path (str): Path to the file
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File does not exist: {path}")


def parse_csv_line(line: str) -> list[str]:
    """
    Parse a single CSV line into fields, handling quotes and commas.
    
    Parameters:
        line (str): A single line from CSV file
        
    Returns:
        list[str]: List of field values (stripped of whitespace)
    """
    # Split by comma and strip whitespace from each field
    fields = [field.strip() for field in line.split(',')]
    return [f for f in fields if f]  # Remove empty fields


def read_csv_lines(path: str) -> list[str]:
    """
    Read all non-comment lines from a CSV file.
    
    Parameters:
        path (str): Path to the CSV file
        
    Returns:
        list[str]: List of lines (excluding comments and empty lines)
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    file_exists(path)
    
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments (lines starting with #) and empty lines
            if line and not line.startswith('#'):
                lines.append(line)
    
    return lines


def parse_float(value: str, field_name: str, line_num: int) -> float:
    """
    Parse a string value as a float with error handling.
    
    Parameters:
        value (str): The value to parse
        field_name (str): Name of the field (for error messages)
        line_num (int): Line number in file (for error messages)
        
    Returns:
        float: The parsed value
        
    Raises:
        ValueError: If conversion fails or value is invalid
    """
    try:
        return float(value)
    except ValueError:
        raise ValueError(
            f"Line {line_num}: '{field_name}' must be a number, got '{value}'"
        )


def parse_int(value: str, field_name: str, line_num: int) -> int:
    """
    Parse a string value as an integer with error handling.
    
    Parameters:
        value (str): The value to parse
        field_name (str): Name of the field (for error messages)
        line_num (int): Line number in file (for error messages)
        
    Returns:
        int: The parsed value
        
    Raises:
        ValueError: If conversion fails
    """
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Line {line_num}: '{field_name}' must be an integer, got '{value}'"
        )


def validate_coordinate(value: float, field_name: str, line_num: int, 
                       min_val: float = 0, max_val: float = 50) -> float:
    """
    Validate that a coordinate is within acceptable bounds.
    
    Parameters:
        value (float): The coordinate value
        field_name (str): Name of the field (e.g., 'px', 'py')
        line_num (int): Line number in file (for error messages)
        min_val (float): Minimum allowed value (default 0)
        max_val (float): Maximum allowed value (default 50)
        
    Returns:
        float: The validated value
        
    Raises:
        ValueError: If value is outside bounds
    """
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"Line {line_num}: '{field_name}' = {value} is out of bounds [{min_val}, {max_val}]"
        )
    return value


def validate_time(value: float, line_num: int) -> float:
    """
    Validate that a time value is non-negative.
    
    Parameters:
        value (float): The time value
        line_num (int): Line number in file (for error messages)
        
    Returns:
        float: The validated value
        
    Raises:
        ValueError: If value is negative
    """
    if value < 0:
        raise ValueError(
            f"Line {line_num}: Time 't' must be non-negative, got {value}"
        )
    return value


def validate_row_length(row: list[str], expected_length: int, 
                       line_num: int, file_type: str) -> None:
    """
    Validate that a row has the expected number of fields.
    
    Parameters:
        row (list[str]): The parsed row
        expected_length (int): Expected number of fields
        line_num (int): Line number in file (for error messages)
        file_type (str): Type of file ('driver' or 'request')
        
    Raises:
        ValueError: If row doesn't have enough fields
    """
    if len(row) < expected_length:
        raise ValueError(
            f"Line {line_num}: {file_type.upper()} row has {len(row)} fields, "
            f"expected at least {expected_length}. Row: {', '.join(row)}"
        )


def parse_driver_row(row: list[str], line_num: int) -> dict[str, Any]:
    """
    Parse and validate a single driver row from CSV.
    
    Parameters:
        row (list[str]): Parsed CSV row with [x, y, ...]
        line_num (int): Line number in file (for error messages)
        
    Returns:
        dict: Driver dictionary with validated fields
        
    Raises:
        ValueError: If any field is invalid
    """
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
    """
    Parse and validate a single request row from CSV.
    
    Parameters:
        row (list[str]): Parsed CSV row with [t, px, py, dx, dy, ...]
        line_num (int): Line number in file (for error messages)
        
    Returns:
        dict: Request dictionary with validated fields
        
    Raises:
        ValueError: If any field is invalid or out of bounds
    """
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
