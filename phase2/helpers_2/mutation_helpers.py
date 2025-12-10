"""
Helper functions for mutation rules and behaviour adaptation.
Centralizes mutation logic used by mutation rules and engine.
"""

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from phase2.driver import Driver
    from phase2.behaviours import DriverBehaviour


def get_driver_history_window(driver: "Driver", window: int) -> List[dict]:
    """
    Extract recent completed trips from driver's history.
    
    Safely retrieves the last N entries from driver.history, handling
    cases where history is shorter than requested window.
    
    Args:
        driver: Driver with trip history
        window: Number of recent trips to retrieve
        
    Returns:
        list: Up to window most recent history entries (may be fewer if 
              driver completed < window trips)
        
    Example:
        >>> driver.history = [
        ...     {"request_id": 1, "fare": 5.0, "time": 10},
        ...     {"request_id": 2, "fare": 3.5, "time": 25},
        ... ]
        >>> get_driver_history_window(driver, 5)
        [{"request_id": 1, "fare": 5.0, "time": 10},
         {"request_id": 2, "fare": 3.5, "time": 25}]
    """
    return driver.history[-window:] if window > 0 else []


def calculate_average_fare(history: List[dict]) -> Optional[float]:
    """
    Calculate average fare from history entries.
    
    Extracts 'fare' field from each entry and computes mean. Returns None
    if history is empty to allow graceful handling of insufficient data.
    
    Args:
        history: List of trip history entries (each with 'fare' key)
        
    Returns:
        float: Average fare, or None if history is empty
        
    Example:
        >>> history = [
        ...     {"request_id": 1, "fare": 5.0},
        ...     {"request_id": 2, "fare": 3.5},
        ...     {"request_id": 3, "fare": 6.0},
        ... ]
        >>> calculate_average_fare(history)
        4.833...
    """
    if not history:
        return None
    total = sum(entry.get("fare", 0.0) for entry in history)
    return total / len(history)


def should_mutate_performance(avg_fare: Optional[float], threshold: float) -> bool:
    """
    Determine if driver should mutate due to poor earnings performance.
    
    Compares average fare to threshold. Returns False if history is
    insufficient (avg_fare is None), otherwise checks if avg_fare below
    threshold to trigger adaptation to greedier strategy.
    
    Args:
        avg_fare: Average fare from recent trips, or None if insufficient data
        threshold: Minimum acceptable average fare
        
    Returns:
        bool: True if avg_fare < threshold and avg_fare is not None, False otherwise
        
    Example:
        >>> should_mutate_performance(3.5, 5.0)
        True  # Low earnings, should switch to greedy
        
        >>> should_mutate_performance(6.0, 5.0)
        False  # Earnings good, stay with current strategy
        
        >>> should_mutate_performance(None, 5.0)
        False  # Not enough history, no mutation yet
    """
    if avg_fare is None:
        return False
    return avg_fare < threshold


def get_behaviour_name(behaviour: "DriverBehaviour") -> str:
    """
    Get human-readable name of driver's current behaviour.
    
    Extracts the class name without module prefix. Useful for logging,
    statistics, and debugging to understand driver strategies.
    
    Args:
        behaviour: Driver behaviour instance
        
    Returns:
        str: Class name (e.g., "GreedyDistanceBehaviour", "LazyBehaviour")
        
    Example:
        >>> behaviour = GreedyDistanceBehaviour(max_distance=10.0)
        >>> get_behaviour_name(behaviour)
        "GreedyDistanceBehaviour"
    """
    return type(behaviour).__name__ if behaviour else "None"


def count_recent_trips(driver: "Driver", max_time_ago: int) -> int:
    """
    Count recent trips completed within time window.
    
    Filters driver.history to count trips completed in last max_time_ago
    ticks. Useful for identifying recently active drivers or computing
    performance over specific time intervals.
    
    Args:
        driver: Driver with trip history
        max_time_ago: Time window in ticks (only count trips from last max_time_ago ticks)
        
    Returns:
        int: Number of trips completed within the time window
        
    Example:
        >>> driver.history = [
        ...     {"request_id": 1, "time": 50},
        ...     {"request_id": 2, "time": 75},
        ...     {"request_id": 3, "time": 100},
        ... ]
        >>> count_recent_trips(driver, max_time_ago=30)
        1  # Only trip at time 100 is within last 30 ticks
    """
    current_time = driver.history[-1].get("time", 0) if driver.history else 0
    cutoff_time = current_time - max_time_ago
    return sum(1 for entry in driver.history if entry.get("time", 0) >= cutoff_time)


def is_high_performer(driver: "Driver", window: int, threshold: float) -> bool:
    """
    Determine if driver is high performer based on average earnings.
    
    Convenience function combining get_driver_history_window(),
    calculate_average_fare(), and threshold comparison. Returns True if
    driver has sufficient history and average earnings meet/exceed threshold.
    
    Args:
        driver: Driver to evaluate
        window: Number of recent trips to consider
        threshold: Minimum average fare for high performer status
        
    Returns:
        bool: True if avg_fare >= threshold, False otherwise (including no history)
        
    Example:
        >>> is_high_performer(driver, window=5, threshold=5.0)
        True  # Driver earning well
        
        >>> is_high_performer(driver, window=5, threshold=5.0)
        False  # Driver struggling or insufficient history
    """
    history = get_driver_history_window(driver, window)
    avg_fare = calculate_average_fare(history)
    if avg_fare is None:
        return False
    return avg_fare >= threshold


def is_low_performer(driver: "Driver", window: int, threshold: float) -> bool:
    """
    Determine if driver is low performer based on average earnings.
    
    Complement of is_high_performer(). Returns True if driver has
    sufficient history and average earnings fall below threshold,
    indicating need for strategy adaptation.
    
    Args:
        driver: Driver to evaluate
        window: Number of recent trips to consider
        threshold: Maximum average fare for low performer status
        
    Returns:
        bool: True if avg_fare < threshold, False otherwise (including no history)
        
    Example:
        >>> is_low_performer(driver, window=5, threshold=5.0)
        True  # Driver should switch to greedier strategy
        
        >>> is_low_performer(driver, window=5, threshold=5.0)
        False  # Driver doing well or insufficient history
    """
    history = get_driver_history_window(driver, window)
    avg_fare = calculate_average_fare(history)
    if avg_fare is None:
        return False
    return avg_fare < threshold


def get_earnings_statistics(driver: "Driver") -> dict:
    """
    Compute comprehensive earnings statistics for driver.
    
    Analyzes entire driver history to produce summary statistics useful
    for mutation decisions and performance evaluation. Handles empty
    history gracefully.
    
    Args:
        driver: Driver with trip history
        
    Returns:
        dict with keys:
            - 'total_earnings': Sum of all fares
            - 'trip_count': Number of completed trips
            - 'average_fare': Mean fare per trip
            - 'min_fare': Minimum fare (None if no trips)
            - 'max_fare': Maximum fare (None if no trips)
            - 'std_dev': Standard deviation (0.0 if < 2 trips)
            
    Example:
        >>> driver.history = [
        ...     {"fare": 5.0},
        ...     {"fare": 3.5},
        ...     {"fare": 6.0},
        ... ]
        >>> stats = get_earnings_statistics(driver)
        >>> stats['total_earnings']
        14.5
        >>> stats['average_fare']
        4.833...
    """
    if not driver.history:
        return {
            'total_earnings': 0.0,
            'trip_count': 0,
            'average_fare': None,
            'min_fare': None,
            'max_fare': None,
            'std_dev': 0.0,
        }
    
    fares = [entry.get("fare", 0.0) for entry in driver.history]
    total = sum(fares)
    count = len(fares)
    avg = total / count if count > 0 else 0.0
    
    # Calculate standard deviation
    variance = sum((f - avg) ** 2 for f in fares) / count if count > 0 else 0.0
    std_dev = variance ** 0.5
    
    return {
        'total_earnings': total,
        'trip_count': count,
        'average_fare': avg,
        'min_fare': min(fares) if fares else None,
        'max_fare': max(fares) if fares else None,
        'std_dev': std_dev,
    }
