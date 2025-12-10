from __future__ import annotations  # Allows using the class name "Point" as a string in type hints
from dataclasses import dataclass  # Automatically generates __init__, __repr__, and other methods
import math  # Provides mathematical functions such as hypot()

# Epsilon for floating-point comparisons
EPSILON = 1e-9


@dataclass(frozen=True)
class Point:
    """A 2D point representing a position on the map with vector operations.
    
    Immutable and hashable. Supports distance_to(), +, -, *, and in-place operators.
    """
    x: float  # x-coordinate
    y: float  # y-coordinate


    def distance_to(self, other: "Point") -> float:
        """Return Euclidean distance to another point.
        
        Raises TypeError if other is not a Point instance.
        """
        if not isinstance(other, Point):
            raise TypeError(f"distance_to() requires a Point, got {type(other).__name__}")
        
        # Difference in x-direction
        dx = self.x - other.x

        # Difference in y-direction
        dy = self.y - other.y

        # math.hypot(dx, dy) = sqrt(dx*dx + dy*dy) Pythagorean theorem
        return math.hypot(dx, dy)


    def __add__(self, other: "Point") -> "Point":
        """Add two points (vector addition). Raises TypeError if other is not a Point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"unsupported operand type(s) for +: 'Point' and '{type(other).__name__}'")
        return Point(self.x + other.x, self.y + other.y)


    def __sub__(self, other: "Point") -> "Point":
        """Subtract two points (vector subtraction). Raises TypeError if other is not a Point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"unsupported operand type(s) for -: 'Point' and '{type(other).__name__}'")
        return Point(self.x - other.x, self.y - other.y)


    def __iadd__(self, other: "Point") -> "Point":
        """In-place addition (+=). Returns new Point (immutable). Raises TypeError if other is not a Point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"unsupported operand type(s) for +=: 'Point' and '{type(other).__name__}'")
        return Point(self.x + other.x, self.y + other.y)


    def __isub__(self, other: "Point") -> "Point":
        """In-place subtraction (-=). Returns new Point (immutable). Raises TypeError if other is not a Point.
        """
        if not isinstance(other, Point):
            raise TypeError(f"unsupported operand type(s) for -=: 'Point' and '{type(other).__name__}'")
        return Point(self.x - other.x, self.y - other.y)


    def __mul__(self, scalar: float) -> "Point":
        """Multiply point by scalar (int or float). Raises TypeError if scalar is not numeric.
        """
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"can't multiply sequence by non-int of type '{type(scalar).__name__}'")
        return Point(self.x * scalar, self.y * scalar)


    def __rmul__(self, scalar: float) -> "Point":
        """Right multiply point by scalar (int or float). Enables scalar * point syntax.
        """
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"can't multiply sequence by non-int of type '{type(scalar).__name__}'")
        # Reuse __mul__ to avoid repeating logic
        return self.__mul__(scalar)
    
    
    def __eq__(self, other: object) -> bool:
        """Check equality with epsilon tolerance for floating-point precision.
        
        Two points are equal if coordinates differ by less than EPSILON.
        """
        if not isinstance(other, Point):
            return NotImplemented
        return (abs(self.x - other.x) < EPSILON and 
                abs(self.y - other.y) < EPSILON)
    
    
    def __hash__(self) -> int:
        """Hash point for use in sets and dict keys by rounding to EPSILON grid.
        
        Hashing lets Python find data quickly, epsilon tolerance prevents duplicates.
        """
        # Round to grid cells of size EPSILON to group similar points
        return hash((round(self.x / EPSILON), round(self.y / EPSILON)))
    
    
    def __repr__(self) -> str:
        """Return readable representation for debugging."""
        return f"Point({self.x:.1f}, {self.y:.1f})"

