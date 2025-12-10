"""
Helper functions for request generation and analysis.
Centralizes generation utilities used by RequestGenerator and simulation engine.
"""

from typing import TYPE_CHECKING, Optional, List, Tuple

if TYPE_CHECKING:
    from phase2.request import Request
    from phase2.generator import RequestGenerator


def validate_generator_params(rate: float, width: int, height: int) -> Tuple[bool, Optional[str]]:
    """
    Validate request generator parameters.
    
    Checks that rate, width, and height are within valid ranges for
    realistic simulation. Returns (valid, error_message).
    
    Args:
        rate: Expected requests per tick (Poisson λ)
        width: Map width in units
        height: Map height in units
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
            - (True, None) if all parameters valid
            - (False, "error message") if validation fails
            
    Validation Rules:
        - rate >= 0 (can be 0 for no generation)
        - rate <= 100 (sanity check, beyond is unrealistic)
        - width > 0 (must have positive bounds)
        - width <= 10000 (sanity check)
        - height > 0 (must have positive bounds)
        - height <= 10000 (sanity check)
        
    Example:
        >>> valid, msg = validate_generator_params(2.0, 50, 50)
        >>> valid
        True
        >>> msg is None
        True
        
        >>> valid, msg = validate_generator_params(-1.0, 50, 50)
        >>> valid
        False
        >>> "rate" in msg
        True
    """
    if rate < 0:
        return False, f"rate must be >= 0, got {rate}"
    if rate > 100:
        return False, f"rate unusually high: {rate} (sanity check)"
    if width <= 0:
        return False, f"width must be > 0, got {width}"
    if width > 10000:
        return False, f"width unusually large: {width} (sanity check)"
    if height <= 0:
        return False, f"height must be > 0, got {height}"
    if height > 10000:
        return False, f"height unusually large: {height} (sanity check)"
    return True, None


def estimate_request_count(rate: float, num_ticks: int) -> float:
    """
    Estimate total requests over N ticks.
    
    For Poisson(rate), expected value is rate*num_ticks.
    Useful for pre-simulation planning and resource allocation.
    
    Args:
        rate: Requests per tick (Poisson λ)
        num_ticks: Number of ticks to simulate
        
    Returns:
        float: Expected total requests (rate * num_ticks)
        
    Example:
        >>> estimate_request_count(2.0, 100)
        200.0
        >>> estimate_request_count(0.5, 1000)
        500.0
    """
    if num_ticks < 0:
        return 0.0
    return float(rate * num_ticks)


def calculate_generation_statistics(requests: List["Request"]) -> dict:
    """
    Compute statistics from generated requests.
    
    Analyzes list of requests to produce summary statistics:
    creation time distribution, location clustering, etc.
    
    Args:
        requests: List of Request objects
        
    Returns:
        dict with keys:
            - 'count': Total requests
            - 'creation_times': List of all creation times (for histogram)
            - 'min_creation_time': Earliest request
            - 'max_creation_time': Latest request
            - 'avg_creation_time': Average creation time
            - 'request_ids': List of all request IDs
            
    Example:
        >>> # After generating requests
        >>> stats = calculate_generation_statistics(requests)
        >>> stats['count']
        150
        >>> stats['max_creation_time']
        100
    """
    if not requests:
        return {
            'count': 0,
            'creation_times': [],
            'min_creation_time': None,
            'max_creation_time': None,
            'avg_creation_time': None,
            'request_ids': [],
        }
    
    creation_times = [r.creation_time for r in requests]
    request_ids = [r.id for r in requests]
    
    avg_time = sum(creation_times) / len(creation_times) if creation_times else 0.0
    
    return {
        'count': len(requests),
        'creation_times': creation_times,
        'min_creation_time': min(creation_times),
        'max_creation_time': max(creation_times),
        'avg_creation_time': avg_time,
        'request_ids': request_ids,
    }


def get_requests_by_time(requests: List["Request"], time: int) -> List["Request"]:
    """
    Filter requests created at specific time.
    
    Helper to find all requests that appeared at a given simulation tick.
    Useful for analyzing generation patterns per tick.
    
    Args:
        requests: List of Request objects
        time: Target creation time
        
    Returns:
        List of requests with creation_time == time
        
    Example:
        >>> # Get all requests created at tick 10
        >>> tick_10_requests = get_requests_by_time(all_requests, 10)
        >>> len(tick_10_requests)
        3
    """
    return [r for r in requests if r.creation_time == time]


def get_requests_in_timerange(requests: List["Request"], start_time: int, end_time: int) -> List["Request"]:
    """
    Filter requests created within time range [start_time, end_time].
    
    Helper for analyzing generation patterns over intervals.
    
    Args:
        requests: List of Request objects
        start_time: Inclusive start time
        end_time: Inclusive end time
        
    Returns:
        List of requests with creation_time in [start_time, end_time]
        
    Example:
        >>> # Get requests from ticks 0-50
        >>> early_requests = get_requests_in_timerange(all_requests, 0, 50)
        >>> len(early_requests)
        100
    """
    return [r for r in requests if start_time <= r.creation_time <= end_time]


def get_generation_rate_actual(requests: List["Request"], window_size: int) -> List[Tuple[int, float]]:
    """
    Calculate actual generation rate per time window.
    
    Divides time into windows and counts requests per window to show
    actual vs theoretical generation rates. Useful for validating that
    Poisson distribution is working as expected.
    
    Args:
        requests: List of Request objects
        window_size: Time window size (ticks)
        
    Returns:
        List of (window_start_time, rate) tuples
            where rate = requests_in_window / window_size
            
    Example:
        >>> # 100 requests generated over 100 ticks
        >>> rates = get_generation_rate_actual(requests, window_size=10)
        >>> len(rates)
        10
        >>> rates[0]  # First 10 ticks
        (0, 1.2)  # ~1.2 requests per tick
    """
    if not requests or window_size <= 0:
        return []
    
    max_time = max(r.creation_time for r in requests)
    rates = []
    
    for window_start in range(0, max_time + 1, window_size):
        window_end = window_start + window_size - 1
        window_requests = get_requests_in_timerange(requests, window_start, window_end)
        rate = len(window_requests) / window_size
        rates.append((window_start, rate))
    
    return rates


def compare_actual_vs_expected_rate(requests: List["Request"], expected_rate: float, 
                                   window_size: int = 10) -> dict:
    """
    Compare actual generation rate with theoretical rate.
    
    Analyzes how well actual Poisson generation matches the configured
    expected rate. Helps validate generator correctness.
    
    Args:
        requests: List of generated Request objects
        expected_rate: Configured rate parameter (Poisson λ)
        window_size: Time window for analysis (ticks)
        
    Returns:
        dict with comparison metrics:
            - 'expected_rate': Configured rate
            - 'actual_avg_rate': Observed average rate
            - 'total_requests': Count of all requests
            - 'time_span': Total simulation time
            - 'variance': Variance of rates per window
            - 'percent_error': % difference from expected
            
    Example:
        >>> comparison = compare_actual_vs_expected_rate(requests, 2.0, 10)
        >>> comparison['expected_rate']
        2.0
        >>> comparison['actual_avg_rate']
        1.95  # Close to expected
    """
    if not requests:
        return {
            'expected_rate': expected_rate,
            'actual_avg_rate': 0.0,
            'total_requests': 0,
            'time_span': 0,
            'variance': 0.0,
            'percent_error': 0.0,
        }
    
    rates = get_generation_rate_actual(requests, window_size)
    if not rates:
        return {
            'expected_rate': expected_rate,
            'actual_avg_rate': 0.0,
            'total_requests': len(requests),
            'time_span': 0,
            'variance': 0.0,
            'percent_error': 0.0,
        }
    
    actual_rates = [rate for _, rate in rates]
    actual_avg = sum(actual_rates) / len(actual_rates)
    
    # Calculate variance
    variance = sum((r - actual_avg) ** 2 for r in actual_rates) / len(actual_rates)
    
    # Calculate percent error
    if expected_rate > 0:
        percent_error = ((actual_avg - expected_rate) / expected_rate) * 100.0
    else:
        percent_error = 0.0
    
    return {
        'expected_rate': expected_rate,
        'actual_avg_rate': actual_avg,
        'total_requests': len(requests),
        'time_span': max(r.creation_time for r in requests) - min(r.creation_time for r in requests) + 1,
        'variance': variance,
        'percent_error': percent_error,
    }


def get_request_location_bounds(requests: List["Request"]) -> dict:
    """
    Find bounds of pickup and dropoff locations.
    
    Analyzes spatial distribution of requests to ensure they're using
    the full map and locations are realistic.
    
    Args:
        requests: List of Request objects
        
    Returns:
        dict with location statistics:
            - 'pickup_min_x', 'pickup_max_x': X bounds for pickups
            - 'pickup_min_y', 'pickup_max_y': Y bounds for pickups
            - 'dropoff_min_x', 'dropoff_max_x': X bounds for dropoffs
            - 'dropoff_min_y', 'dropoff_max_y': Y bounds for dropoffs
            
    Example:
        >>> bounds = get_request_location_bounds(requests)
        >>> bounds['pickup_max_x']
        49.8  # Using map width ~50
    """
    if not requests:
        return {
            'pickup_min_x': None, 'pickup_max_x': None,
            'pickup_min_y': None, 'pickup_max_y': None,
            'dropoff_min_x': None, 'dropoff_max_x': None,
            'dropoff_min_y': None, 'dropoff_max_y': None,
        }
    
    pickup_xs = [r.pickup.x for r in requests]
    pickup_ys = [r.pickup.y for r in requests]
    dropoff_xs = [r.dropoff.x for r in requests]
    dropoff_ys = [r.dropoff.y for r in requests]
    
    return {
        'pickup_min_x': min(pickup_xs),
        'pickup_max_x': max(pickup_xs),
        'pickup_min_y': min(pickup_ys),
        'pickup_max_y': max(pickup_ys),
        'dropoff_min_x': min(dropoff_xs),
        'dropoff_max_x': max(dropoff_xs),
        'dropoff_min_y': min(dropoff_ys),
        'dropoff_max_y': max(dropoff_ys),
    }
