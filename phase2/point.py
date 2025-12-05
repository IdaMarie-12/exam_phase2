from __future__ import annotations   # Allows using the class name "Point" as a string in type hints
from dataclasses import dataclass    # Automatically generates __init__, __repr__, and other methods
import math                           # Provides mathematical functions such as hypot()


@dataclass
class Point:
    x: float   # x-coordinate
    y: float   # y-coordinate
"""
    A class that represents a point in a two-dimensional coordinate system.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.

    The class supports:
        - computing the distance between two points
        - adding and subtracting points
        - multiplying a point by a scalar (int or float)
        - using operators such as +, -, +=, -=, *, and scalar * point
    """

    def distance_to(self, other: "Point") -> float:
        # Difference in x-direction
        dx = self.x - other.x

        # Difference in y-direction
        dy = self.y - other.y

        # math.hypot(dx, dy) = sqrt(dx*dx + dy*dy)
        return math.hypot(dx, dy)


    def __add__(self, other: "Point") -> "Point":
        # Creates and returns a new Point
        return Point(self.x + other.x, self.y + other.y)


    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)
        

    def __iadd__(self, other: "Point") -> "Point":
        # Modify coordinates directly
        self.x += other.x
        self.y += other.y
        # Return the same object instance
        return self


    def __isub__(self, other: "Point") -> "Point":
        self.x -= other.x
        self.y -= other.y
        return self


    def __mul__(self, scalar: float) -> "Point":
        return Point(self.x * scalar, self.y * scalar)



    def __rmul__(self, scalar: float) -> "Point":
        # Reuse __mul__ to avoid repeating logic
        return self.__mul__(scalar)


