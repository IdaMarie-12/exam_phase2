"""
Post-Simulation Reporting Module

Displays comprehensive metrics and plots after simulation completes.

Features:
    - Time-series plots of key metrics (served, expired, wait time, utilization)
    - Summary statistics window
    - Policy performance comparison
    - Request distribution analysis
    - Trend visualization

Usage:
    >>> from phase2.report_window import generate_report
    >>> from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
    >>> 
    >>> series = SimulationTimeSeries()
    >>> for _ in range(1000):
    ...     sim.tick()
    ...     series.record_tick(sim)
    >>> 
    >>> # After simulation completes
    >>> generate_report(sim, series)

Notes:
    - Call generate_report() after simulation.tick() loop
    - Requires matplotlib for plotting
    - Displays multiple time-series plots showing evolution of metrics
"""

from typing import Optional
from .helpers_2.metrics_helpers import SimulationTimeSeries

try:
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None


# ====================================================================
# MAIN REPORT GENERATION
# ====================================================================

def generate_report(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """
    Generate comprehensive post-simulation report with plots.
    
    Creates a multi-panel figure showing:
        1. Served vs Expired Requests (cumulative over time)
        2. Average Wait Time Evolution
        3. Pending Requests Over Time
        4. Driver Utilization Trend
        5. Summary Statistics Panel
    
    Args:
        simulation: Completed DeliverySimulation instance
        time_series: SimulationTimeSeries tracking recorded metrics.
                    If None, only static final metrics displayed.
                    
    Raises:
        RuntimeError: If matplotlib not installed
        
    Example:
        >>> sim = DeliverySimulation(drivers, policy, gen, mutation, timeout=20)
        >>> series = SimulationTimeSeries()
        >>> 
        >>> for tick in range(1000):
        ...     sim.tick()
        ...     series.record_tick(sim)
        >>> 
        >>> generate_report(sim, series)
        >>> plt.show()
    """
    if not HAS_MATPLOTLIB:
        raise RuntimeError("matplotlib not installed. Cannot generate plots.")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle('Post-Simulation Analysis Report', fontsize=16, fontweight='bold')
    
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Plot 1: Served vs Expired (cumulative)
    ax1 = fig.add_subplot(gs[0, :])
    _plot_requests_evolution(ax1, time_series)
    
    # Plot 2: Average Wait Time
    ax2 = fig.add_subplot(gs[1, 0])
    _plot_wait_time_evolution(ax2, time_series)
    
    # Plot 3: Pending Requests
    ax3 = fig.add_subplot(gs[1, 1])
    _plot_pending_evolution(ax3, time_series)
    
    # Plot 4: Driver Utilization
    ax4 = fig.add_subplot(gs[2, 0])
    _plot_utilization_evolution(ax4, time_series)
    
    # Plot 5: Summary Statistics
    ax5 = fig.add_subplot(gs[2, 1])
    _plot_summary_statistics(ax5, simulation, time_series)
    
    plt.show()


# ====================================================================
# INDIVIDUAL PLOT FUNCTIONS
# ====================================================================

def _plot_requests_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """
    Plot cumulative served and expired requests over time.
    
    Shows trend of request completion vs timeout.
    """
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_title('Served vs Expired Requests')
        return
    
    data = time_series.get_data()
    ax.plot(data['times'], data['served'], label='Served', linewidth=2, color='green', marker='o', markersize=2)
    ax.plot(data['times'], data['expired'], label='Expired', linewidth=2, color='red', marker='s', markersize=2)
    ax.fill_between(data['times'], data['served'], alpha=0.2, color='green')
    ax.fill_between(data['times'], data['expired'], alpha=0.2, color='red')
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Cumulative Count')
    ax.set_title('Request Fulfillment Evolution')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)


def _plot_wait_time_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """
    Plot average wait time trend over simulation.
    
    Shows whether wait times improve or degrade over time.
    """
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Average Wait Time')
        return
    
    data = time_series.get_data()
    ax.plot(data['times'], data['avg_wait'], linewidth=2, color='steelblue', marker='.')
    ax.fill_between(data['times'], data['avg_wait'], alpha=0.2, color='steelblue')
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Average Wait (ticks)')
    ax.set_title('Average Wait Time Trend')
    ax.grid(True, alpha=0.3)


def _plot_pending_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """
    Plot number of pending (unserved) requests over time.
    
    Shows system load and queue management efficiency.
    """
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Pending Requests')
        return
    
    data = time_series.get_data()
    ax.fill_between(data['times'], data['pending'], alpha=0.3, color='orange')
    ax.plot(data['times'], data['pending'], linewidth=2, color='darkorange', marker='.')
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Pending Count')
    ax.set_title('Pending Requests Over Time')
    ax.grid(True, alpha=0.3)


def _plot_utilization_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """
    Plot driver utilization (% busy) over time.
    
    Shows how well the fleet is engaged throughout simulation.
    """
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Driver Utilization')
        return
    
    data = time_series.get_data()
    ax.fill_between(data['times'], data['utilization'], alpha=0.3, color='purple')
    ax.plot(data['times'], data['utilization'], linewidth=2, color='indigo', marker='.')
    ax.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Max')
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Utilization (%)')
    ax.set_title('Driver Utilization Trend')
    ax.set_ylim([0, 110])
    ax.grid(True, alpha=0.3)


def _plot_summary_statistics(ax, simulation, time_series: Optional[SimulationTimeSeries]) -> None:
    """
    Display summary statistics as text in axes.
    
    Shows final metrics in readable format.
    """
    ax.axis('off')
    
    # Get final summary
    if time_series:
        summary = time_series.get_final_summary()
    else:
        summary = _get_static_summary(simulation)
    
    # Format text
    stats_text = f"""
FINAL SIMULATION SUMMARY
{'=' * 40}

Total Time:            {summary.get('total_time', 0)} ticks
Total Requests:        {summary.get('total_requests', 0)}
  • Served:            {summary.get('final_served', 0)}
  • Expired:           {summary.get('final_expired', 0)}

Service Level:         {summary.get('service_level', 0):.1f}%
Average Wait Time:     {summary.get('final_avg_wait', 0):.2f} ticks

Total Drivers:         {len(simulation.drivers)}
Total Requests:        {len(simulation.requests)}
"""
    
    ax.text(0.1, 0.95, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


def _get_static_summary(simulation) -> dict:
    """
    Generate summary from simulation object alone (no time-series).
    
    Used when time_series is None.
    """
    total_requests = simulation.served_count + simulation.expired_count
    service_level = (simulation.served_count / total_requests * 100.0) if total_requests > 0 else 0.0
    
    return {
        'total_time': simulation.time,
        'total_requests': total_requests,
        'final_served': simulation.served_count,
        'final_expired': simulation.expired_count,
        'service_level': service_level,
        'final_avg_wait': simulation.avg_wait,
    }


# ====================================================================
# CONVENIENCE FUNCTION FOR QUICK REPORTING
# ====================================================================

def quick_report(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """
    Quick alias for generate_report().
    
    Args:
        simulation: Completed DeliverySimulation instance
        time_series: Optional SimulationTimeSeries with recorded metrics
    """
    generate_report(simulation, time_series)
