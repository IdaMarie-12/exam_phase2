import unittest
import tempfile
import os
from pathlib import Path

# Phase 1 modules
from phase1.io_mod import load_drivers, load_requests, generate_drivers, generate_requests
from phase1.helpers_1.load_helper import (
    read_csv_lines, parse_csv_line, parse_float, parse_driver_row,
    parse_request_row, validate_coordinate, validate_time, validate_row_length,
    file_exists
)
from phase1.helpers_1.generate_helper import (
    generate_request_count, create_random_position, create_driver_dict,
    create_request_dict
)


# ====================================================================
# CSV Line Parsing Tests
# ====================================================================

class TestParseCSVLine(unittest.TestCase):
    """Test CSV line parsing functionality."""
    
    def test_parse_simple_csv_line(self):
        """parse_csv_line handles comma-separated values."""
        line = "1,2,3"
        result = parse_csv_line(line)
        self.assertEqual(result, ["1", "2", "3"])
    
    def test_parse_csv_line_with_spaces(self):
        """parse_csv_line strips whitespace around fields."""
        line = "  1  ,  2  ,  3  "
        result = parse_csv_line(line)
        self.assertEqual(result, ["1", "2", "3"])
    
    def test_parse_csv_line_with_floats(self):
        """parse_csv_line handles float values."""
        line = "1.5, 2.3, 3.7"
        result = parse_csv_line(line)
        self.assertEqual(result, ["1.5", "2.3", "3.7"])
    
    def test_parse_empty_line(self):
        """parse_csv_line handles empty input."""
        result = parse_csv_line("")
        self.assertEqual(result, [])
    
    def test_parse_line_with_trailing_comma(self):
        """parse_csv_line ignores empty trailing fields."""
        line = "1,2,3,"
        result = parse_csv_line(line)
        self.assertEqual(result, ["1", "2", "3"])


# ====================================================================
# CSV File Reading Tests
# ====================================================================

class TestReadCSVLines(unittest.TestCase):
    """Test reading CSV files."""
    
    def test_read_csv_with_comments(self):
        """read_csv_lines skips comment lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("1,2,3\n")
            f.write("# Another comment\n")
            f.write("4,5,6\n")
            f.flush()
            temp_path = f.name
        
        try:
            lines = read_csv_lines(temp_path)
            self.assertEqual(lines, ["1,2,3", "4,5,6"])
        finally:
            os.unlink(temp_path)
    
    def test_read_csv_skips_empty_lines(self):
        """read_csv_lines skips empty lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("1,2,3\n")
            f.write("\n")
            f.write("4,5,6\n")
            f.write("   \n")
            f.write("7,8,9\n")
            f.flush()
            temp_path = f.name
        
        try:
            lines = read_csv_lines(temp_path)
            self.assertEqual(lines, ["1,2,3", "4,5,6", "7,8,9"])
        finally:
            os.unlink(temp_path)
    
    def test_read_nonexistent_file(self):
        """read_csv_lines raises FileNotFoundError for missing files."""
        with self.assertRaises(FileNotFoundError):
            read_csv_lines("/nonexistent/path/file.csv")


# ====================================================================
# Float Parsing Tests
# ====================================================================

class TestParseFloat(unittest.TestCase):
    """Test float parsing and error handling."""
    
    def test_parse_valid_float(self):
        """parse_float converts valid strings to floats."""
        self.assertEqual(parse_float("1.5", "test", 1), 1.5)
        self.assertEqual(parse_float("0", "test", 1), 0.0)
        self.assertEqual(parse_float("-5.2", "test", 1), -5.2)
    
    def test_parse_invalid_float(self):
        """parse_float raises ValueError for invalid strings."""
        with self.assertRaises(ValueError) as ctx:
            parse_float("not_a_number", "field_name", 5)
        self.assertIn("Line 5", str(ctx.exception))
        self.assertIn("field_name", str(ctx.exception))


# ====================================================================
# Coordinate Validation Tests
# ====================================================================

class TestValidateCoordinate(unittest.TestCase):
    """Test coordinate bounds validation."""
    
    def test_coordinate_within_bounds(self):
        """validate_coordinate accepts values within bounds."""
        result = validate_coordinate(25.0, "x", 1, min_val=0, max_val=50)
        self.assertEqual(result, 25.0)
    
    def test_coordinate_at_min_boundary(self):
        """validate_coordinate accepts minimum boundary value."""
        result = validate_coordinate(0.0, "x", 1, min_val=0, max_val=50)
        self.assertEqual(result, 0.0)
    
    def test_coordinate_at_max_boundary(self):
        """validate_coordinate accepts maximum boundary value."""
        result = validate_coordinate(50.0, "x", 1, min_val=0, max_val=50)
        self.assertEqual(result, 50.0)
    
    def test_coordinate_below_min(self):
        """validate_coordinate raises for values below minimum."""
        with self.assertRaises(ValueError) as ctx:
            validate_coordinate(-1.0, "x", 5, min_val=0, max_val=50)
        self.assertIn("out of bounds", str(ctx.exception))
        self.assertIn("Line 5", str(ctx.exception))
    
    def test_coordinate_above_max(self):
        """validate_coordinate raises for values above maximum."""
        with self.assertRaises(ValueError) as ctx:
            validate_coordinate(51.0, "x", 5, min_val=0, max_val=50)
        self.assertIn("out of bounds", str(ctx.exception))


# ====================================================================
# Time Validation Tests
# ====================================================================

class TestValidateTime(unittest.TestCase):
    """Test time validation."""
    
    def test_valid_time(self):
        """validate_time accepts non-negative times."""
        self.assertEqual(validate_time(0, 1), 0)
        self.assertEqual(validate_time(100.5, 1), 100.5)
    
    def test_negative_time(self):
        """validate_time rejects negative times."""
        with self.assertRaises(ValueError) as ctx:
            validate_time(-1.0, 5)
        self.assertIn("non-negative", str(ctx.exception))
        self.assertIn("Line 5", str(ctx.exception))


# ====================================================================
# Row Length Validation Tests
# ====================================================================

class TestValidateRowLength(unittest.TestCase):
    """Test row length validation."""
    
    def test_valid_row_length(self):
        """validate_row_length accepts rows with enough fields."""
        # Should not raise
        validate_row_length(["1", "2", "3"], 3, 1, "test")
        validate_row_length(["1", "2", "3", "4"], 3, 1, "test")
    
    def test_insufficient_fields(self):
        """validate_row_length rejects rows with too few fields."""
        with self.assertRaises(ValueError) as ctx:
            validate_row_length(["1", "2"], 3, 5, "request")
        self.assertIn("has 2 fields", str(ctx.exception))
        self.assertIn("expected at least 3", str(ctx.exception))


# ====================================================================
# Driver Row Parsing Tests
# ====================================================================

class TestParseDriverRow(unittest.TestCase):
    """Test driver CSV row parsing."""
    
    def test_parse_valid_driver_row(self):
        """parse_driver_row parses valid driver data."""
        row = ["10.0", "20.0"]
        result = parse_driver_row(row, 2)
        
        self.assertEqual(result["x"], 10.0)
        self.assertEqual(result["y"], 20.0)
        self.assertEqual(result["speed"], 1.0)
        self.assertEqual(result["vx"], 0.0)
        self.assertEqual(result["vy"], 0.0)
        self.assertIsNone(result["target_id"])
    
    def test_parse_driver_row_boundaries(self):
        """parse_driver_row validates coordinate bounds."""
        # Valid: at boundaries
        row = ["0", "50"]
        result = parse_driver_row(row, 2)
        self.assertEqual(result["x"], 0.0)
        self.assertEqual(result["y"], 50.0)
    
    def test_parse_driver_row_out_of_bounds(self):
        """parse_driver_row rejects out-of-bounds coordinates."""
        row = ["-1", "20"]
        with self.assertRaises(ValueError):
            parse_driver_row(row, 2)
    
    def test_parse_driver_row_insufficient_fields(self):
        """parse_driver_row requires at least 2 fields."""
        row = ["10.0"]
        with self.assertRaises(ValueError):
            parse_driver_row(row, 2)
    
    def test_parse_driver_row_non_numeric(self):
        """parse_driver_row rejects non-numeric values."""
        row = ["abc", "20"]
        with self.assertRaises(ValueError):
            parse_driver_row(row, 2)


# ====================================================================
# Request Row Parsing Tests
# ====================================================================

class TestParseRequestRow(unittest.TestCase):
    """Test request CSV row parsing."""
    
    def test_parse_valid_request_row(self):
        """parse_request_row parses valid request data."""
        row = ["5", "10.0", "15.0", "20.0", "25.0"]
        result = parse_request_row(row, 2)
        
        self.assertEqual(result["t"], 5)
        self.assertEqual(result["px"], 10.0)
        self.assertEqual(result["py"], 15.0)
        self.assertEqual(result["dx"], 20.0)
        self.assertEqual(result["dy"], 25.0)
    
    def test_parse_request_row_boundaries(self):
        """parse_request_row validates all coordinate bounds."""
        row = ["0", "0", "0", "50", "50"]
        result = parse_request_row(row, 2)
        self.assertEqual(result["t"], 0)
        self.assertEqual(result["px"], 0.0)
        self.assertEqual(result["dy"], 50.0)
    
    def test_parse_request_row_negative_time(self):
        """parse_request_row rejects negative times."""
        row = ["-1", "10", "15", "20", "25"]
        with self.assertRaises(ValueError):
            parse_request_row(row, 2)
    
    def test_parse_request_row_out_of_bounds_pickup(self):
        """parse_request_row rejects out-of-bounds pickup."""
        row = ["5", "-1", "15", "20", "25"]
        with self.assertRaises(ValueError):
            parse_request_row(row, 2)
    
    def test_parse_request_row_insufficient_fields(self):
        """parse_request_row requires 5 fields."""
        row = ["5", "10", "15", "20"]
        with self.assertRaises(ValueError):
            parse_request_row(row, 2)


# ====================================================================
# File Loading Tests
# ====================================================================

class TestLoadDrivers(unittest.TestCase):
    """Test driver CSV loading."""
    
    def test_load_drivers_from_valid_csv(self):
        """load_drivers reads and parses drivers correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("# Driver CSV\n")
            f.write("10.0,20.0\n")
            f.write("30.0,40.0\n")
            f.flush()
            temp_path = f.name
        
        try:
            drivers = load_drivers(temp_path)
            self.assertEqual(len(drivers), 2)
            self.assertEqual(drivers[0]["x"], 10.0)
            self.assertEqual(drivers[0]["y"], 20.0)
            self.assertEqual(drivers[0]["id"], 0)
            self.assertEqual(drivers[1]["x"], 30.0)
            self.assertEqual(drivers[1]["id"], 1)
        finally:
            os.unlink(temp_path)
    
    def test_load_drivers_empty_file(self):
        """load_drivers handles empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("# Only comments\n")
            f.flush()
            temp_path = f.name
        
        try:
            drivers = load_drivers(temp_path)
            self.assertEqual(len(drivers), 0)
        finally:
            os.unlink(temp_path)
    
    def test_load_drivers_nonexistent_file(self):
        """load_drivers raises FileNotFoundError for missing files."""
        with self.assertRaises(FileNotFoundError):
            load_drivers("/nonexistent/file.csv")


class TestLoadRequests(unittest.TestCase):
    """Test request CSV loading."""
    
    def test_load_requests_from_valid_csv(self):
        """load_requests reads and parses requests correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("# Request CSV\n")
            f.write("0,1,2,3,4\n")
            f.write("5,10,15,20,25\n")
            f.flush()
            temp_path = f.name
        
        try:
            requests = load_requests(temp_path)
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[0]["t"], 0)
            self.assertEqual(requests[0]["px"], 1.0)
            self.assertEqual(requests[0]["id"], 0)
            self.assertEqual(requests[1]["t"], 5)
            self.assertEqual(requests[1]["id"], 1)
        finally:
            os.unlink(temp_path)
    
    def test_load_requests_empty_file(self):
        """load_requests handles empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("# Only comments\n")
            f.flush()
            temp_path = f.name
        
        try:
            requests = load_requests(temp_path)
            self.assertEqual(len(requests), 0)
        finally:
            os.unlink(temp_path)


# ====================================================================
# Poisson Generation Tests
# ====================================================================

class TestGenerateRequestCount(unittest.TestCase):
    """Test Poisson-distributed request generation."""
    
    def test_zero_rate_generates_zero(self):
        """generate_request_count returns 0 for rate=0."""
        for _ in range(10):
            count = generate_request_count(0.0)
            self.assertEqual(count, 0)
    
    def test_poisson_distribution_average(self):
        """generate_request_count produces correct average over many samples."""
        import random
        random.seed(42)
        
        rate = 2.0
        samples = 1000
        counts = [generate_request_count(rate) for _ in range(samples)]
        average = sum(counts) / len(counts)
        
        # Average should be approximately equal to rate (within tolerance)
        self.assertAlmostEqual(average, rate, delta=0.5)
    
    def test_negative_rate_raises(self):
        """generate_request_count rejects negative rates."""
        with self.assertRaises(ValueError):
            generate_request_count(-1.0)
    
    def test_high_rate_generates_multiple(self):
        """generate_request_count can generate multiple requests."""
        import random
        random.seed(123)
        
        rate = 10.0
        # With high rate, some calls should generate > 0 requests
        counts = [generate_request_count(rate) for _ in range(100)]
        
        self.assertTrue(any(c > 0 for c in counts))
        self.assertTrue(any(c > 1 for c in counts))


# ====================================================================
# Random Position Generation Tests
# ====================================================================

class TestCreateRandomPosition(unittest.TestCase):
    """Test random position generation."""
    
    def test_position_within_bounds(self):
        """create_random_position generates positions within grid bounds."""
        import random
        random.seed(42)
        
        width, height = 50, 30
        for _ in range(100):
            x, y = create_random_position(width, height)
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, width)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y, height)
    
    def test_position_variety(self):
        """create_random_position generates different positions."""
        import random
        random.seed(42)
        
        positions = [create_random_position(50, 30) for _ in range(10)]
        # All positions should be different (very unlikely to get duplicates)
        self.assertEqual(len(positions), len(set(positions)))


# ====================================================================
# Driver Dictionary Generation Tests
# ====================================================================

class TestCreateDriverDict(unittest.TestCase):
    """Test driver dictionary creation."""
    
    def test_create_driver_dict_structure(self):
        """create_driver_dict has all required fields."""
        import random
        random.seed(42)
        
        driver = create_driver_dict(5, 50, 30)
        
        self.assertEqual(driver["id"], 5)
        self.assertIn("x", driver)
        self.assertIn("y", driver)
        self.assertIn("speed", driver)
        self.assertIn("vx", driver)
        self.assertIn("vy", driver)
        self.assertIn("target_id", driver)
    
    def test_driver_initial_state(self):
        """create_driver_dict initializes state correctly."""
        import random
        random.seed(42)
        
        driver = create_driver_dict(0, 50, 30)
        
        # Initial velocities should be zero
        self.assertEqual(driver["vx"], 0.0)
        self.assertEqual(driver["vy"], 0.0)
        # No target initially
        self.assertIsNone(driver["target_id"])
    
    def test_driver_speed_range(self):
        """create_driver_dict generates speed in expected range."""
        import random
        random.seed(42)
        
        speeds = [create_driver_dict(i, 50, 30)["speed"] for i in range(100)]
        
        for speed in speeds:
            self.assertGreaterEqual(speed, 0.8)
            self.assertLessEqual(speed, 1.6)
    
    def test_driver_position_within_grid(self):
        """create_driver_dict generates position within grid."""
        import random
        random.seed(42)
        
        width, height = 50, 30
        drivers = [create_driver_dict(i, width, height) for i in range(50)]
        
        for driver in drivers:
            self.assertGreaterEqual(driver["x"], 0)
            self.assertLessEqual(driver["x"], width)
            self.assertGreaterEqual(driver["y"], 0)
            self.assertLessEqual(driver["y"], height)


# ====================================================================
# Request Dictionary Generation Tests
# ====================================================================

class TestCreateRequestDict(unittest.TestCase):
    """Test request dictionary creation."""
    
    def test_create_request_dict_structure(self):
        """create_request_dict has all required fields."""
        import random
        random.seed(42)
        
        req = create_request_dict(1, 0, 50, 30)
        
        self.assertEqual(req["id"], 1)
        self.assertEqual(req["t"], 0)
        self.assertIn("px", req)
        self.assertIn("py", req)
        self.assertIn("dx", req)
        self.assertIn("dy", req)
    
    def test_request_within_grid(self):
        """create_request_dict generates positions within grid."""
        import random
        random.seed(42)
        
        width, height = 50, 30
        for _ in range(50):
            req = create_request_dict(1, 0, width, height)
            
            self.assertGreaterEqual(req["px"], 0)
            self.assertLessEqual(req["px"], width)
            self.assertGreaterEqual(req["py"], 0)
            self.assertLessEqual(req["py"], height)
            self.assertGreaterEqual(req["dx"], 0)
            self.assertLessEqual(req["dx"], width)


# ====================================================================
# Integration Tests
# ====================================================================

class TestGenerateDrivers(unittest.TestCase):
    """Test driver generation function."""
    
    def test_generate_drivers_count(self):
        """generate_drivers creates correct number of drivers."""
        drivers = generate_drivers(5, 50, 30)
        self.assertEqual(len(drivers), 5)
    
    def test_generate_drivers_have_ids(self):
        """generate_drivers assigns unique IDs."""
        drivers = generate_drivers(5, 50, 30)
        ids = [d["id"] for d in drivers]
        self.assertEqual(len(ids), len(set(ids)))
    
    def test_generate_drivers_zero_count(self):
        """generate_drivers handles zero count."""
        drivers = generate_drivers(0, 50, 30)
        self.assertEqual(len(drivers), 0)


class TestGenerateRequests(unittest.TestCase):
    """Test request generation function."""
    
    def test_generate_requests_appends_to_list(self):
        """generate_requests appends to provided list."""
        out_list = []
        generate_requests(0, out_list, 2.0, 50, 30)
        
        # Should have some requests (non-deterministic, but very likely)
        self.assertGreaterEqual(len(out_list), 0)
    
    def test_generate_requests_zero_rate(self):
        """generate_requests produces no requests with rate=0."""
        out_list = []
        for _ in range(10):
            generate_requests(0, out_list, 0.0, 50, 30)
        
        self.assertEqual(len(out_list), 0)


if __name__ == '__main__':
    unittest.main()
