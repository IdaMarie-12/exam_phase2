import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import math
from phase2.point import Point, EPSILON


class TestPointBasic(unittest.TestCase):
    """Test basic Point instantiation and properties."""

    def test_creation_with_positive_coords(self):
        """Create point with positive coordinates."""
        p = Point(3, 4)
        self.assertEqual(p.x, 3)
        self.assertEqual(p.y, 4)

    def test_creation_with_negative_coords(self):
        """Create point with negative coordinates."""
        p = Point(-5, -10)
        self.assertEqual(p.x, -5)
        self.assertEqual(p.y, -10)

    def test_creation_with_floats(self):
        """Create point with floating-point coordinates."""
        p = Point(1.5, 2.7)
        self.assertEqual(p.x, 1.5)
        self.assertEqual(p.y, 2.7)

    def test_point_is_immutable(self):
        """Point is frozen (immutable) dataclass."""
        p = Point(1, 2)
        with self.assertRaises(AttributeError):
            p.x = 5  # Can't change frozen dataclass


# ====================================================================
# TEST: distance_to() Method
# ====================================================================

class TestPointDistance(unittest.TestCase):
    """Test distance_to() method - Euclidean distance calculation."""

    def test_distance_horizontal(self):
        """Distance between points on horizontal line (x-axis)."""
        p1 = Point(0, 0)
        p2 = Point(3, 0)
        self.assertEqual(p1.distance_to(p2), 3.0)

    def test_distance_vertical(self):
        """Distance between points on vertical line (y-axis)."""
        p1 = Point(0, 0)
        p2 = Point(0, 4)
        self.assertEqual(p1.distance_to(p2), 4.0)

    def test_distance_diagonal_3_4_5_triangle(self):
        """Classic 3-4-5 Pythagorean triangle."""
        p1 = Point(0, 0)
        p2 = Point(3, 4)
        self.assertEqual(p1.distance_to(p2), 5.0)

    def test_distance_negative_coordinates(self):
        """Distance calculation with negative coordinates."""
        p1 = Point(-3, -4)
        p2 = Point(0, 0)
        self.assertEqual(p1.distance_to(p2), 5.0)

    def test_distance_very_large_values(self):
        """Distance with very large coordinates."""
        p1 = Point(1000000, 1000000)
        p2 = Point(1000003, 1000004)
        self.assertEqual(p1.distance_to(p2), 5.0)

    def test_distance_type_error_with_string(self):
        """TypeError when distance_to() called with string."""
        p = Point(0, 0)
        with self.assertRaises(TypeError):
            p.distance_to("not a point")


# ====================================================================
# TEST: __add__() Method (Vector Addition)
# ====================================================================

class TestPointAddition(unittest.TestCase):
    """Test __add__() method - vector addition (p1 + p2)."""

    def test_add_positive_coordinates(self):
        """Add two points with positive coordinates."""
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        result = p1 + p2
        self.assertEqual(result, Point(4, 6))

    def test_add_with_negative(self):
        """Add points with negative coordinates."""
        p1 = Point(5, 5)
        p2 = Point(-2, -3)
        result = p1 + p2
        self.assertEqual(result, Point(3, 2))

    def test_add_to_zero_vector(self):
        """Adding zero vector (0,0) doesn't change point."""
        p = Point(3, 4)
        result = p + Point(0, 0)
        self.assertEqual(result, p)

    def test_add_creates_new_point(self):
        """Addition creates new Point, doesn't modify originals."""
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        result = p1 + p2
        # Originals unchanged
        self.assertEqual(p1, Point(1, 2))
        self.assertEqual(p2, Point(3, 4))
        self.assertEqual(result, Point(4, 6))

    def test_add_type_error_with_int(self):
        """TypeError when adding int to Point."""
        p = Point(0, 0)
        with self.assertRaises(TypeError):
            p + 5


# ====================================================================
# TEST: __sub__() Method (Vector Subtraction)
# ====================================================================

class TestPointSubtraction(unittest.TestCase):
    """Test __sub__() method - vector subtraction (p1 - p2)."""

    def test_sub_resulting_negative(self):
        """Subtraction can result in negative coordinates."""
        p1 = Point(2, 3)
        p2 = Point(5, 7)
        result = p1 - p2
        self.assertEqual(result, Point(-3, -4))

    def test_sub_from_itself(self):
        """Subtracting point from itself gives zero vector."""
        p = Point(5, 5)
        result = p - p
        self.assertEqual(result, Point(0, 0))

    def test_sub_type_error_with_int(self):
        """TypeError when subtracting int from Point."""
        p = Point(0, 0)
        with self.assertRaises(TypeError):
            p - 5


# ====================================================================
# TEST: __mul__() and __rmul__() Methods (Scalar Multiplication)
# ====================================================================

class TestPointMultiplication(unittest.TestCase):
    """Test __mul__() and __rmul__() - scalar multiplication."""

    def test_mul_by_zero(self):
        """Multiply by zero gives zero vector."""
        p = Point(5, 10)
        result = p * 0
        self.assertEqual(result, Point(0, 0))

    def test_mul_by_negative(self):
        """Multiply by negative reverses direction."""
        p = Point(2, 3)
        result = p * -1
        self.assertEqual(result, Point(-2, -3))

    def test_rmul_scalar_first(self):
        """Right multiplication: scalar * point == point * scalar."""
        p = Point(2, 3)
        self.assertEqual(3 * p, p * 3)

    def test_mul_type_error_with_string(self):
        """TypeError when multiplying by string."""
        p = Point(2, 3)
        with self.assertRaises(TypeError):
            p * "scale"


# ====================================================================
# TEST: __iadd__() and __isub__() Methods (In-place Operations)
# ====================================================================

class TestPointInPlace(unittest.TestCase):
    """Test __iadd__() and __isub__() - in-place operations."""

    def test_iadd_modifies_variable(self):
        """p += other creates new Point and reassigns variable."""
        p = Point(1, 2)
        original_id = id(p)
        p += Point(3, 4)
        self.assertEqual(p, Point(4, 6))
        # New object created (immutable)
        self.assertNotEqual(id(p), original_id)

    def test_isub_modifies_variable(self):
        """p -= other creates new Point and reassigns variable."""
        p = Point(5, 7)
        p -= Point(2, 3)
        self.assertEqual(p, Point(3, 4))

    def test_iadd_multiple_times(self):
        """Multiple += operations work correctly."""
        p = Point(1, 1)
        p += Point(1, 1)  # p = (2, 2)
        p += Point(1, 1)  # p = (3, 3)
        self.assertEqual(p, Point(3, 3))

    def test_isub_multiple_times(self):
        """Multiple -= operations work correctly."""
        p = Point(10, 10)
        p -= Point(2, 2)  # p = (8, 8)
        p -= Point(3, 3)  # p = (5, 5)
        self.assertEqual(p, Point(5, 5))

    def test_iadd_type_error(self):
        """TypeError when += with non-Point."""
        p = Point(0, 0)
        with self.assertRaises(TypeError):
            p += 5

    def test_isub_type_error(self):
        """TypeError when -= with non-Point."""
        p = Point(0, 0)
        with self.assertRaises(TypeError):
            p -= 5


# ====================================================================
# TEST: __eq__() Method (Equality)
# ====================================================================

class TestPointEquality(unittest.TestCase):
    """Test __eq__() - equality comparison with epsilon tolerance."""

    def test_eq_same_values(self):
        """Points with same coordinates are equal."""
        p1 = Point(3, 4)
        p2 = Point(3, 4)
        self.assertEqual(p1, p2)

    def test_eq_different_values(self):
        """Points with different coordinates are not equal."""
        p1 = Point(3, 4)
        p2 = Point(5, 7)
        self.assertNotEqual(p1, p2)

    def test_eq_within_epsilon(self):
        """Points within EPSILON are considered equal."""
        p1 = Point(1.0, 2.0)
        p2 = Point(1.0 + EPSILON/2, 2.0 + EPSILON/2)
        self.assertEqual(p1, p2)

    def test_eq_outside_epsilon(self):
        """Points beyond EPSILON are not equal."""
        p1 = Point(1.0, 2.0)
        p2 = Point(1.0 + EPSILON*2, 2.0)
        self.assertNotEqual(p1, p2)

    def test_eq_with_non_point(self):
        """Comparing with non-Point returns False."""
        p = Point(0, 0)
        self.assertNotEqual(p, (0, 0))
        self.assertNotEqual(p, None)


# ====================================================================
# TEST: __hash__() Method (Hashability)
# ====================================================================

class TestPointHashable(unittest.TestCase):
    """Test __hash__() - making Point usable in sets and dicts."""

    def test_hash_enables_set(self):
        """Points can be added to sets."""
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        s = {p1, p2}
        self.assertEqual(len(s), 2)

    def test_hash_enables_dict_key(self):
        """Points can be used as dict keys."""
        p1 = Point(1, 2)
        d = {p1: "location1"}
        self.assertEqual(d[p1], "location1")

    def test_hash_consistency(self):
        """Same point always produces same hash."""
        p = Point(5, 5)
        hash1 = hash(p)
        hash2 = hash(p)
        self.assertEqual(hash1, hash2)

    def test_hash_equal_points_same_hash(self):
        """Equal points produce same hash."""
        p1 = Point(1, 2)
        p2 = Point(1, 2)
        self.assertEqual(hash(p1), hash(p2))

    def test_set_deduplication_exact(self):
        """Set deduplicates identical points."""
        p1 = Point(1, 2)
        p2 = Point(1, 2)
        s = {p1, p2}
        self.assertEqual(len(s), 1)

    def test_dict_retrieval_exact(self):
        """Dict retrieval with identical key."""
        p1 = Point(1, 2)
        p2 = Point(1, 2)
        d = {p1: "value"}
        self.assertEqual(d[p2], "value")


# ====================================================================
# TEST: __repr__() Method (String Representation)
# ====================================================================

class TestPointRepr(unittest.TestCase):
    """Test __repr__() - human-readable representation."""

    def test_repr_format(self):
        """Repr has correct format Point(x, y)."""
        p = Point(1.234, 2.567)
        repr_str = repr(p)
        self.assertIn("Point", repr_str)
        self.assertIn("1.2", repr_str)  # Rounded to 1 decimal

    def test_repr_contains_coordinates(self):
        """Repr includes x and y coordinates."""
        p = Point(3, 4)
        repr_str = repr(p)
        self.assertIn("3", repr_str)
        self.assertIn("4", repr_str)

    def test_repr_integer_coordinates(self):
        """Repr with integer coordinates."""
        p = Point(5, 7)
        repr_str = repr(p)
        self.assertIn("Point(", repr_str)
        self.assertIn("5.0", repr_str)
        self.assertIn("7.0", repr_str)

    def test_repr_negative_coordinates(self):
        """Repr with negative coordinates."""
        p = Point(-3, -4)
        repr_str = repr(p)
        self.assertIn("-3", repr_str)
        self.assertIn("-4", repr_str)

    def test_repr_float_coordinates(self):
        """Repr with floating-point coordinates."""
        p = Point(1.5, 2.7)
        repr_str = repr(p)
        # Should show rounded to 1 decimal
        self.assertIn("Point(", repr_str)


# ====================================================================
# INTEGRATION TESTS: Multiple Operations Combined
# ====================================================================

class TestPointIntegration(unittest.TestCase):
    """Integration tests combining multiple Point operations."""

    def test_distance_after_addition(self):
        """Distance calculation after vector addition."""
        p1 = Point(0, 0)
        p2 = Point(3, 4)
        p3 = p1 + p2  # (3, 4)
        
        # Distance from origin to result should be 5
        distance = Point(0, 0).distance_to(p3)
        self.assertEqual(distance, 5.0)

    def test_scalar_multiplication_then_distance(self):
        """Distance after scalar multiplication."""
        p1 = Point(3, 4)  # Distance from origin = 5
        p2 = p1 * 2  # (6, 8) - Distance from origin = 10
        
        distance = Point(0, 0).distance_to(p2)
        self.assertEqual(distance, 10.0)

    def test_complex_vector_operation(self):
        """Complex combination of operations."""
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        p3 = Point(1, 1)
        
        # (p1 + p2) * 2 - p3 = (4, 6) * 2 - (1, 1) = (8, 12) - (1, 1) = (7, 11)
        result = (p1 + p2) * 2 - p3
        expected = Point(7, 11)
        self.assertEqual(result, expected)

    def test_points_in_set_for_pathfinding(self):
        """Practical: Using points in set for pathfinding."""
        visited = {Point(0, 0), Point(3, 4), Point(6, 8)}
        current = Point(3, 4)
        
        # Check if location was already visited
        self.assertIn(current, visited)


if __name__ == "__main__":
    unittest.main()
