from __future__ import annotations  # Allows using the class name "Point" as a string in type hints
from dataclasses import dataclass  # Automatically generates __init__, __repr__, and other methods
import math  # Provides mathematical functions such as hypot()

# Epsilon for floating-point comparisons
EPSILON = 1e-9


@dataclass(frozen=True)
class Point:
    """
    A 2D point in Cartesian space supporting vector operations.
    
    Points are immutable (frozen), making them hashable and safe for
    use in sets and as dictionary keys. Supports distance calculation,
    vector addition/subtraction, and scalar multiplication.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.

    The class supports:
        - computing the distance between two points
        - adding and subtracting points
        - multiplying a point by a scalar (int or float)
        - using operators such as +, -, *, and scalar * point
        - equality comparison with floating-point tolerance
        - hashing (enabling use in sets and as dict keys)
        
    Example:
        >>> p1 = Point(3.0, 4.0)
        >>> p2 = Point(6.0, 8.0)
        >>> p1.distance_to(p2)
        5.0
        >>> p1 + p2
        Point(x=9.0, y=12.0)
    """
    x: float  # x-coordinate
    y: float  # y-coordinate


    def distance_to(self, other: "Point") -> float:
        """
        Compute Euclidean distance to another point.
        
        Args:
            other: The target point
            
        Returns:
            float: Distance between self and other
            
        Example:
            >>> Point(0, 0).distance_to(Point(3, 4))
            5.0
        """
        # Difference in x-direction
        dx = self.x - other.x

        # Difference in y-direction
        dy = self.y - other.y

        # math.hypot(dx, dy) = sqrt(dx*dx + dy*dy)
        return math.hypot(dx, dy)


    def __add__(self, other: "Point") -> "Point":
        """Add two points (vector addition)."""
        return Point(self.x + other.x, self.y + other.y)


    def __sub__(self, other: "Point") -> "Point":
        """Subtract two points (vector subtraction)."""
        return Point(self.x - other.x, self.y - other.y)


    def __mul__(self, scalar: float) -> "Point":
        """Multiply point by scalar (element-wise)."""
        return Point(self.x * scalar, self.y * scalar)


    def __rmul__(self, scalar: float) -> "Point":
        """Right multiply point by scalar (enables scalar * point)."""
        # Reuse __mul__ to avoid repeating logic
        return self.__mul__(scalar)
    
    
    def __eq__(self, other: object) -> bool:
        """
        Check equality with epsilon tolerance for floating-point precision.
        
        Two points are equal if their coordinates are within EPSILON of each other.
        This prevents issues with floating-point arithmetic like 0.1 + 0.2 != 0.3.
        
        Args:
            other: Object to compare with
            
        Returns:
            bool: True if points are approximately equal, False otherwise
            
        Example:
            >>> Point(0.1, 0.2) == Point(0.1 + 1e-10, 0.2 + 1e-10)
            True
        """
        if not isinstance(other, Point):
            return NotImplemented
        return (abs(self.x - other.x) < EPSILON and 
                abs(self.y - other.y) < EPSILON)
    
    
    def __hash__(self) -> int:
        """
        Hash the point for use in sets and as dictionary keys.
        
        Since Point is frozen (immutable), it's safe to hash.
        Rounds coordinates to avoid floating-point precision issues.
        
        Example:
            >>> points = {Point(1.0, 2.0), Point(1.0, 2.0)}
            >>> len(points)
            1
        """
        # Round to grid cells of size EPSILON to group similar points
        return hash((round(self.x / EPSILON), round(self.y / EPSILON)))
    
    
    def __repr__(self) -> str:
        """Return readable representation for debugging."""
        return f"Point({self.x:.1f}, {self.y:.1f})"

