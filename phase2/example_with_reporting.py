"""
Example: Running Phase 2 Simulation with Post-Simulation Reporting

This example shows how to:
1. Initialize and run a complete simulation
2. Track metrics during simulation
3. Generate comprehensive plots after simulation completes

Usage:
    python -m phase2.example_with_reporting

Or integrate into your main application:
    from phase2.example_with_reporting import run_simulation_with_report
    run_simulation_with_report(num_ticks=1000)
"""

from phase2.simulation import DeliverySimulation
from phase2.point import Point
from phase2.driver import Driver
from phase2.generator import RequestGenerator
from phase2.policies import GlobalGreedy
from phase2.behaviours import LazyBehaviour, GreedyDistanceBehaviour
from phase2.mutation import PerformanceBasedMutation
from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
from phase2.report_window import generate_report


def create_example_simulation(num_drivers: int = 20, 
                            width: int = 50, 
                            height: int = 30,
                            req_rate: float = 2.0,
                            timeout: int = 20) -> DeliverySimulation:
    """
    Create a sample delivery simulation for demonstration.
    
    Args:
        num_drivers: Number of drivers to simulate
        width: Grid width
        height: Grid height
        req_rate: Request generation rate (Poisson λ)
        timeout: Request timeout in ticks
        
    Returns:
        Initialized DeliverySimulation instance
    """
    # Create drivers with mixed behaviours
    drivers = []
    for i in range(num_drivers):
        if i % 2 == 0:
            behaviour = LazyBehaviour(idle_ticks_needed=3, max_distance=5.0)
        else:
            behaviour = GreedyDistanceBehaviour(max_distance=10.0)
        
        driver = Driver(
            id=i + 1,
            position=Point(width // 2 + (i % 5) * 2, height // 2 + (i // 5) * 2),
            speed=1.5,
            behaviour=behaviour,
        )
        drivers.append(driver)
    
    # Create simulation
    policy = GlobalGreedy()
    generator = RequestGenerator(rate=req_rate, width=width, height=height)
    mutation_rule = PerformanceBasedMutation(window=5, earnings_threshold=5.0)
    
    sim = DeliverySimulation(
        drivers=drivers,
        dispatch_policy=policy,
        request_generator=generator,
        mutation_rule=mutation_rule,
        timeout=timeout,
    )
    
    return sim


def run_simulation_with_report(num_ticks: int = 1000,
                              num_drivers: int = 20,
                              show_plots: bool = True) -> None:
    """
    Run complete simulation with post-simulation reporting.
    
    This function:
    1. Creates a sample simulation
    2. Runs it for num_ticks timesteps
    3. Records metrics at each timestep
    4. Generates and displays comprehensive plots
    
    Args:
        num_ticks: Number of simulation ticks to run
        num_drivers: Number of drivers in simulation
        show_plots: Whether to display plots after simulation
        
    Example:
        >>> run_simulation_with_report(num_ticks=500, num_drivers=15)
    """
    print("=" * 60)
    print("PHASE 2 DELIVERY SIMULATION WITH REPORTING")
    print("=" * 60)
    print()
    
    # Create simulation
    print("Creating simulation...")
    sim = create_example_simulation(num_drivers=num_drivers)
    print(f"  ✓ {len(sim.drivers)} drivers created")
    
    # Initialize time-series tracking
    print("Initializing metrics tracking...")
    time_series = SimulationTimeSeries()
    
    # Run simulation
    print(f"Running simulation for {num_ticks} ticks...")
    print()
    
    checkpoint_interval = max(1, num_ticks // 10)
    
    for tick in range(num_ticks):
        sim.tick()
        time_series.record_tick(sim)
        
        # Progress checkpoint
        if (tick + 1) % checkpoint_interval == 0:
            progress = ((tick + 1) / num_ticks) * 100
            served = sim.served_count
            expired = sim.expired_count
            print(f"  [{progress:5.1f}%] Served: {served:4d} | Expired: {expired:4d} | Avg Wait: {sim.avg_wait:6.2f}")
    
    print()
    print("=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)
    
    # Get final summary
    summary = time_series.get_final_summary()
    print()
    print("FINAL STATISTICS:")
    print(f"  Total Time:        {summary['total_time']} ticks")
    print(f"  Total Requests:    {summary['total_requests']}")
    print(f"    - Served:        {summary['final_served']}")
    print(f"    - Expired:       {summary['final_expired']}")
    print(f"  Service Level:     {summary['service_level']:.1f}%")
    print(f"  Average Wait Time: {summary['final_avg_wait']:.2f} ticks")
    print()
    
    # Generate report with plots
    if show_plots:
        print("Generating post-simulation report...")
        print("  (Plots will display in separate window)")
        print()
        
        try:
            generate_report(sim, time_series)
        except RuntimeError as e:
            print(f"  ✗ Error: {e}")
            print("  (Install matplotlib to view plots: pip install matplotlib)")
    
    print("Done!")


if __name__ == "__main__":
    run_simulation_with_report(num_ticks=500, num_drivers=15)
