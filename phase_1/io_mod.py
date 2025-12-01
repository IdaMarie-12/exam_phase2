import random
import os
from typing import TextIO

"""
# CSV_validate function 
"""


def CSV_validate(path: str, file_type: str):
    """
    Validate and load a CSV file as either driver data or request data.
    Returns a list of row dictionaries if the file follows the expected format.
    Raises FileNotFoundError or ValueError if the file is invalid.

    """

    # Ensures file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"File does not exist: {path}")

    data = []  # Creates empty list to store validated rows

    with open(path, newline='',
              encoding='utf-8') as csvfile:  # Open the CSV file with UTF-8 encoding and no extra newline characters
        reader = csv.reader(csvfile)  # Create CSV reader to iterate over rows
        header = next(reader)  # Skippes the header row (first row)

        for line_num, row in enumerate(reader,
                                       start=2):  # Loop through all rows starting from line 2 because the header is on line 1
            if not row or all(cell.strip() == "" for cell in row):
                continue

            # # If the file_type is 'driver', validate driver rows
            if file_type == "driver":
                if len(row) < 2 or row[0].strip() == "" or row[1].strip() == "":
                    raise ValueError(
                        f"Missing px/py on line {line_num}: {row}")  # Check that driver row has at least x and y values
                try:
                    x = float(row[0])  # Convertes x and y to numbers (floats)
                    y = float(row[1])
                except ValueError:  # Raises error if conversion fails
                    raise ValueError(f"Invalid number on line {line_num}: {row}")
                if x < 0 or y < 0:  # Check that coordinates are not negative
                    raise ValueError(f"Negative coordinates on line {line_num}: ({x}, {y})")

                # Stores validated driver data in dictionary and add to list
                data.append({
                    "x": x,
                    "y": y,
                    "speed": 1.0,
                    "vx": 0.0,
                    "vy": 0.0,
                    "target_id": None
                })

            # If file_type is 'request', validates request rows
            elif file_type == "request":
                if len(row) < 5:
                    raise ValueError(
                        f"Missing columns on line {line_num}: {row}")  # Checkes that row has at least t, px, py, dx, dy
                try:
                    t = float(row[0])  # Convert request values to floats
                    px = float(row[1])
                    py = float(row[2])
                    dx = float(row[3])
                    dy = float(row[4])
                except ValueError:
                    raise ValueError(f"Invalid number on line {line_num}: {row}")

                if t < 0:  # Checkes that time is not negative
                    raise ValueError(f"Request time {t} out of bounds on line {line_num}")

                for coord, name in zip([px, py, dx, dy], ["px", "py", "dx", "dy"]):
                    if not (0 <= coord <= 50):  # Checkes that each coordinate lies between 0 and 50
                        raise ValueError(f"{name} coordinate {coord} out of bounds (0-50) on line {line_num}")

                # Stores validated request row in dictionary and addes to list
                data.append({
                    "t": t,
                    "px": px,
                    "py": py,
                    "dx": dx,
                    "dy": dy
                })

            # Ensures the file_type is valid
            else:
                raise ValueError("file_type must be 'driver' or 'request'")

    return data  # Returns the completed data list


"""
# load drivers
"""
import csv


def load_drivers(path: str) -> list[dict]:
    """
    Loads driver records from a CSV file.
    Assumes file has been validated already.
    """
    # validates data
    CSV_validate("data/drivers.csv", "driver")

    drivers = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)

        driver_id = 1
        for line_num, row in enumerate(reader, start=2):  # start=2 because header is line 1
            # Skippes completely empty lines or lines where all cells are blank
            if not row or all(cell.strip() == "" for cell in row):
                continue

            # Converts to float
            x = float(row[0])
            y = float(row[1])

            # A driver dictionary with default speed and velocities
            driver = {
                "driver_id": driver_id,
                "x": x,  # Driver a spatial position (x,y)
                "y": y,
                "speed": 1.0,  # Default speed for all drivers
                "vx": 0.0,  # Initial velocity along x-axis
                "vy": 0.0,  # Initial velocity along y-axis
                "target_id": None  # No target assigned initially
            }

            # Adds the driver to the list and increment driver_id
            drivers.append(driver)
            driver_id += 1

    return drivers


"""
load_requests
"""


def load_requests(path: str) -> list[dict]:
    """
    Loads requests from a CSV file.
    Assumes file has been validated already.
    """
    # validate data
    CSV_validate("data/requests.csv", "request")

    requests = []
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the fist line in CSV-file
        for idx, row in enumerate(reader):
            t = float(row[0])
            px = float(row[1])
            py = float(row[2])
            dx = float(row[3])
            dy = float(row[4])

            # Create a dictionary with data from the row
            request = {
                "id": idx,
                "px": float(row[1]),  # Pickup x-coordinate
                "py": float(row[2]),  # Pickup y-coordinate
                "dx": float(row[3]),  # Dropoff x-coordinate
                "dy": float(row[4]),  # Dropoff y-coordinate
                "t": int(row[0]),  # Request time
                "t_wait": 0,  # Waiting time
                "status": "waiting",  # Request status
                "driver_id": None  # No driver assigned yet
            }
            requests.append(request)  # Add request to the list
    return requests  # Return the whole list of requests


"""
# generate drivers
"""


def generate_drivers(n: int, width: int, height: int) -> list[dict]:
    """ Generate n random drivers uniformly distributed within the grid.

    Parameters:
        n (int): number of drivers to create
        width (int): width of the simulation grid
        height (int): height of the simulation grid

    Returns:
        list[dict]: list of driver dictionaries, one per driver

    """

    drivers = []

    for i in range(n):
        drivers.append({
            "driver_id": i,  # driver id = index og generation
            "x": random.uniform(0, width),  # assign random x coordinate
            "y": random.uniform(0, height),  # assign random x coordinate
            "vx": 0.0,  # assign vx = 0.0, no movement when first generated
            "vy": 0.0,  # assign vy = 0.0, no movement when first generated
            "speed": random.uniform(0.8, 1.6),  # assign random speed between 0.8 and 1.6 unit/time
            "tx": None,  # no tx coordinate yet, driver has no target from the beginning
            "ty": None,  # no ty coordinate yet, driver has no target from the beginning
            "target_id": None  # no target_id coordinate yet, driver has no target from the beginning
        })

    return drivers


"""
# generate requests
"""


def generate_requests(start_t: int, out_list: list[dict], width: int, height: int, req_rate: float = 3.0) -> None:
    """
    Generate new requests at the given time step and append them to out_list.

    Parameters:
        start_t (int): current simulation time (minutes)
        out_list (list[dict]): list to append newly created requests to
        width (int): grid width
        height (int): grid height

    Return:
        None (modifies out_list)

    """

    for i in range(int(req_rate)):
        out_list.append({
            "id": f"{start_t}_{i}",  # request id, with start time and the index of generation
            "px": random.uniform(0, width),  # random px coordinate
            "py": random.uniform(0, height),  # random py coordinate
            "dx": random.uniform(0, width),  # random dx coordinate
            "dy": random.uniform(0, height),  # random dy coordinate
            "t": start_t,  # time of request generated
            "t_wait": 0.0,  # initial waiting time is 0.0 units of time
            "status": "waiting",  # status is "waiting" from start
            "driver_id": None  # No driver id, request have not been assigned a driver yet
        })