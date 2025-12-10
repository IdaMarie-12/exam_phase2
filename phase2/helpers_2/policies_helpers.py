"""
Helper functions for dispatch policies and assignment analysis.
Centralizes policy utilities used by policies and simulation engine.
"""

from typing import TYPE_CHECKING, Optional, List, Tuple, Set

if TYPE_CHECKING:
    from phase2.driver import Driver
    from phase2.request import Request


def get_idle_drivers(drivers: List["Driver"]) -> List["Driver"]:
    """
    Filter drivers with idle status.
    
    Extracts only drivers available for new assignments. Used by policies
    to identify which drivers can be offered requests.
    
    Args:
        drivers: List of all drivers in simulation
        
    Returns:
        list: Drivers with status == IDLE
        
    Example:
        >>> drivers = [
        ...     Driver(1, ..., status='IDLE'),
        ...     Driver(2, ..., status='TO_PICKUP'),
        ...     Driver(3, ..., status='IDLE'),
        ... ]
        >>> idle = get_idle_drivers(drivers)
        >>> len(idle)
        2
    """
    return [d for d in drivers if getattr(d, "status", None) == d.IDLE]


def get_waiting_requests(requests: List["Request"]) -> List["Request"]:
    """
    Filter requests with waiting status.
    
    Extracts only requests awaiting assignment. Used by policies to identify
    which requests need drivers.
    
    Args:
        requests: List of all requests in simulation
        
    Returns:
        list: Requests with status == WAITING
        
    Example:
        >>> requests = [
        ...     Request(1, ..., status='WAITING'),
        ...     Request(2, ..., status='ASSIGNED'),
        ...     Request(3, ..., status='WAITING'),
        ... ]
        >>> waiting = get_waiting_requests(requests)
        >>> len(waiting)
        2
    """
    return [r for r in requests if getattr(r, "status", None) == r.WAITING]


def calculate_all_distances(
    drivers: List["Driver"],
    requests: List["Request"]
) -> List[Tuple[float, "Driver", "Request"]]:
    """
    Calculate distances for all driver-request pairs.
    
    Creates list of (distance, driver, request) tuples for all possible
    combinations. Used by GlobalGreedy policy for sorting.
    
    Args:
        drivers: List of drivers to consider
        requests: List of requests to consider
        
    Returns:
        list: Tuples of (distance, driver, request) for each pair
        
    Example:
        >>> drivers = [Driver(1, Point(0, 0)), Driver(2, Point(10, 0))]
        >>> requests = [Request(1, Point(5, 0), ...), Request(2, Point(15, 0), ...)]
        >>> pairs = calculate_all_distances(drivers, requests)
        >>> len(pairs)
        4  # 2 drivers × 2 requests
        >>> pairs[0]  # Closest pair
        (5.0, driver1, request1)
    """
    pairs: List[Tuple[float, "Driver", "Request"]] = []
    for driver in drivers:
        for request in requests:
            distance = driver.position.distance_to(request.pickup)
            pairs.append((distance, driver, request))
    return pairs


def sort_pairs_by_distance(
    pairs: List[Tuple[float, "Driver", "Request"]]
) -> List[Tuple[float, "Driver", "Request"]]:
    """
    Sort distance pairs in ascending order.
    
    Helper for GlobalGreedy policy: sorts all (distance, driver, request)
    tuples so closest pairs come first.
    
    Args:
        pairs: List of (distance, driver, request) tuples
        
    Returns:
        list: Same pairs sorted by distance (ascending)
        
    Example:
        >>> pairs = [(10.0, d1, r1), (2.0, d2, r2), (5.0, d3, r3)]
        >>> sorted_pairs = sort_pairs_by_distance(pairs)
        >>> sorted_pairs[0][0]
        2.0
    """
    return sorted(pairs, key=lambda x: x[0])


def find_closest_pair(
    pairs: List[Tuple[float, "Driver", "Request"]]
) -> Optional[Tuple[float, "Driver", "Request"]]:
    """
    Find the closest driver-request pair.
    
    Helper for NearestNeighbour policy: finds pair with minimum distance.
    Used when manually searching instead of sorting.
    
    Args:
        pairs: List of (distance, driver, request) tuples
        
    Returns:
        Tuple of (distance, driver, request) with minimum distance, or None if empty
        
    Example:
        >>> pairs = [(10.0, d1, r1), (2.0, d2, r2), (5.0, d3, r3)]
        >>> closest = find_closest_pair(pairs)
        >>> closest[0]
        2.0
        >>> closest[1] is d2
        True
    """
    if not pairs:
        return None
    return min(pairs, key=lambda x: x[0])


def select_non_conflicting_pairs(
    sorted_pairs: List[Tuple[float, "Driver", "Request"]]
) -> List[Tuple["Driver", "Request"]]:
    """
    Select pairs greedily while avoiding driver/request reuse.
    
    Implements conflict resolution: iterates through sorted pairs in order,
    selecting each pair if both driver and request are still available.
    Used by GlobalGreedy to finalize assignments.
    
    Args:
        sorted_pairs: List of (distance, driver, request) pairs, sorted by distance
        
    Returns:
        list: Selected (driver, request) pairs (distance removed)
        
    Example:
        >>> sorted_pairs = [
        ...     (1.0, d1, r1),
        ...     (2.0, d1, r2),  # d1 used, skip
        ...     (3.0, d2, r1),  # r1 used, skip
        ...     (4.0, d2, r2),  # d2 used, skip
        ... ]
        >>> selected = select_non_conflicting_pairs(sorted_pairs)
        >>> len(selected)
        1
        >>> selected[0]
        (d1, r1)
    """
    assigned_drivers: Set[int] = set()
    assigned_requests: Set[int] = set()
    result: List[Tuple["Driver", "Request"]] = []
    
    for dist, driver, request in sorted_pairs:
        if driver.id in assigned_drivers or request.id in assigned_requests:
            continue  # Skip if either already assigned
        result.append((driver, request))
        assigned_drivers.add(driver.id)
        assigned_requests.add(request.id)
    
    return result


def get_proposal_statistics(
    proposals: List[Tuple["Driver", "Request"]]
) -> dict:
    """
    Compute summary statistics for proposal set.
    
    Analyzes proposals to produce metrics useful for policy evaluation:
    coverage, average distance, total distance, etc.
    
    Args:
        proposals: List of (driver, request) proposal pairs
        
    Returns:
        dict with keys:
            - 'proposal_count': Number of proposals
            - 'total_distance': Sum of all pickup distances
            - 'average_distance': Mean distance per proposal
            - 'min_distance': Closest proposal
            - 'max_distance': Farthest proposal
            - 'driver_ids': Set of assigned driver IDs
            - 'request_ids': Set of assigned request IDs
            
    Example:
        >>> proposals = [(d1, r1), (d2, r2)]
        >>> # Calculate distances: 5.0, 3.0
        >>> stats = get_proposal_statistics(proposals)
        >>> stats['total_distance']
        8.0
        >>> stats['average_distance']
        4.0
    """
    if not proposals:
        return {
            'proposal_count': 0,
            'total_distance': 0.0,
            'average_distance': None,
            'min_distance': None,
            'max_distance': None,
            'driver_ids': set(),
            'request_ids': set(),
        }
    
    distances = [
        driver.position.distance_to(request.pickup)
        for driver, request in proposals
    ]
    
    total_dist = sum(distances)
    avg_dist = total_dist / len(distances) if distances else 0.0
    
    driver_ids = {driver.id for driver, _ in proposals}
    request_ids = {request.id for _, request in proposals}
    
    return {
        'proposal_count': len(proposals),
        'total_distance': total_dist,
        'average_distance': avg_dist,
        'min_distance': min(distances) if distances else None,
        'max_distance': max(distances) if distances else None,
        'driver_ids': driver_ids,
        'request_ids': request_ids,
    }


def count_covered_requests(
    proposals: List[Tuple["Driver", "Request"]],
    total_waiting: int
) -> float:
    """
    Calculate request coverage percentage.
    
    Computes what fraction of waiting requests received at least one proposal.
    High coverage indicates policy is finding assignments for most requests.
    
    Args:
        proposals: List of (driver, request) proposal pairs
        total_waiting: Total number of waiting requests in simulation
        
    Returns:
        float: Coverage as percentage (0-100), or 0 if no waiting requests
        
    Example:
        >>> proposals = [(d1, r1), (d2, r2), (d3, r1)]  # 2 unique requests
        >>> count_covered_requests(proposals, total_waiting=5)
        40.0  # 2 out of 5 requests got proposals
    """
    if total_waiting == 0:
        return 0.0
    covered_requests = len({request.id for _, request in proposals})
    return (covered_requests / total_waiting) * 100.0


def count_covered_drivers(
    proposals: List[Tuple["Driver", "Request"]],
    total_idle: int
) -> float:
    """
    Calculate driver utilization percentage.
    
    Computes what fraction of idle drivers received assignment proposals.
    High utilization indicates policy is activating most available drivers.
    
    Args:
        proposals: List of (driver, request) proposal pairs
        total_idle: Total number of idle drivers in simulation
        
    Returns:
        float: Utilization as percentage (0-100), or 0 if no idle drivers
        
    Example:
        >>> proposals = [(d1, r1), (d2, r2), (d1, r3)]  # 2 unique drivers
        >>> count_covered_drivers(proposals, total_idle=10)
        20.0  # 2 out of 10 idle drivers got proposals
    """
    if total_idle == 0:
        return 0.0
    covered_drivers = len({driver.id for driver, _ in proposals})
    return (covered_drivers / total_idle) * 100.0


def compare_policies_by_distance(
    proposals_nn: List[Tuple["Driver", "Request"]],
    proposals_gg: List[Tuple["Driver", "Request"]]
) -> dict:
    """
    Compare two policies' assignment quality by distance metrics.
    
    Evaluates how different policies perform on average distance and total
    distance. Useful for choosing which policy to use.
    
    Args:
        proposals_nn: Proposals from NearestNeighbour policy
        proposals_gg: Proposals from GlobalGreedy policy
        
    Returns:
        dict with comparison metrics:
            - 'nn_avg_distance': Average distance from NN policy
            - 'gg_avg_distance': Average distance from GG policy
            - 'nn_total_distance': Total distance from NN policy
            - 'gg_total_distance': Total distance from GG policy
            - 'distance_improvement': % distance saved by GG (negative = worse)
            - 'proposal_count_diff': Difference in number of proposals
            
    Example:
        >>> comparison = compare_policies_by_distance(nn_proposals, gg_proposals)
        >>> comparison['distance_improvement']
        15.0  # GG is 15% better
    """
    nn_stats = get_proposal_statistics(proposals_nn)
    gg_stats = get_proposal_statistics(proposals_gg)
    
    nn_avg = nn_stats.get('average_distance') or 0.0
    gg_avg = gg_stats.get('average_distance') or 0.0
    
    # Compute improvement (negative means worse)
    if nn_avg > 0:
        improvement = ((nn_avg - gg_avg) / nn_avg) * 100.0
    else:
        improvement = 0.0
    
    return {
        'nn_avg_distance': nn_avg,
        'gg_avg_distance': gg_avg,
        'nn_total_distance': nn_stats.get('total_distance', 0.0),
        'gg_total_distance': gg_stats.get('total_distance', 0.0),
        'distance_improvement': improvement,
        'nn_proposal_count': nn_stats.get('proposal_count', 0),
        'gg_proposal_count': gg_stats.get('proposal_count', 0),
        'proposal_count_diff': (
            gg_stats.get('proposal_count', 0) - nn_stats.get('proposal_count', 0)
        ),
    }
