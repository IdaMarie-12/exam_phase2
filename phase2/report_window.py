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
    Generate comprehensive post-simulation report with multiple windows.
    
    Opens THREE matplotlib windows automatically:
        1. Metrics Report - Time-series plots (served/expired, wait time, pending, utilization)
        2. Behaviour Analysis - Driver behaviour distribution and statistics
        3. Mutation Analysis - Active mutation rule and performance impact
    
    All windows are opened non-blocking, allowing all three to display simultaneously.
    
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
        >>> # All three windows open automatically
    """
    if not HAS_MATPLOTLIB:
        raise RuntimeError("matplotlib not installed. Cannot generate plots.")
    
    # ====================================================================
    # WINDOW 1: Metrics Plots
    # ====================================================================
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle('Post-Simulation Metrics Report', fontsize=16, fontweight='bold')
    
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
    
    # Open blocking so windows stay open
    plt.show()
    
    # ====================================================================
    # WINDOW 2: Behaviour Analysis
    # ====================================================================
    _show_behaviour_window(simulation)
    
    # ====================================================================
    # WINDOW 3: Mutation Analysis
    # ====================================================================
    _show_mutation_window(simulation)


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


# ====================================================================
# BEHAVIOUR & MUTATION ANALYSIS WINDOWS
# ====================================================================

def _show_behaviour_window(simulation) -> None:
    """
    Create and display a window with behaviour analysis plots and statistics.
    
    Shows:
        - Behaviour distribution pie chart
        - Behaviour count bar chart
        - Behaviour statistics table
    """
    if not HAS_MATPLOTLIB:
        return
    
    from collections import Counter
    
    fig = plt.figure(figsize=(12, 8))
    fig.suptitle('Driver Behaviour Analysis', fontsize=14, fontweight='bold')
    
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Count behaviour types
    behaviour_counts = Counter()
    for driver in simulation.drivers:
        behaviour_type = driver.behaviour.__class__.__name__
        behaviour_counts[behaviour_type] += 1
    
    if not behaviour_counts:
        fig.text(0.5, 0.5, 'No driver behaviour data available', 
                ha='center', va='center', fontsize=12)
        plt.show()
        return
    
    # Plot 1: Pie chart of behaviour distribution
    ax1 = fig.add_subplot(gs[0, 0])
    colours = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700']
    ax1.pie(behaviour_counts.values(), labels=behaviour_counts.keys(), 
            autopct='%1.1f%%', colors=colours, startangle=90)
    ax1.set_title('Behaviour Distribution')
    
    # Plot 2: Bar chart of behaviour counts
    ax2 = fig.add_subplot(gs[0, 1])
    behaviours = list(behaviour_counts.keys())
    counts = list(behaviour_counts.values())
    bars = ax2.bar(range(len(behaviours)), counts, color=colours[:len(behaviours)])
    ax2.set_xticks(range(len(behaviours)))
    ax2.set_xticklabels(behaviours, rotation=45, ha='right')
    ax2.set_ylabel('Number of Drivers')
    ax2.set_title('Driver Count by Behaviour')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    # Plot 3: Behaviour statistics table
    ax3 = fig.add_subplot(gs[1, :])
    ax3.axis('off')
    
    total_drivers = len(simulation.drivers)
    stats_text = "BEHAVIOUR STATISTICS\n" + "=" * 50 + "\n\n"
    stats_text += f"Total Drivers: {total_drivers}\n\n"
    stats_text += "Behaviour Type Distribution:\n"
    
    for behaviour_type, count in sorted(behaviour_counts.items()):
        percentage = (count / total_drivers * 100) if total_drivers > 0 else 0
        stats_text += f"  • {behaviour_type:25s}: {count:3d} drivers ({percentage:5.1f}%)\n"
    
    ax3.text(0.1, 0.95, stats_text, transform=ax3.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    # Open blocking so windows stay open
    plt.show()


def _show_mutation_window(simulation) -> None:
    """
    Create and display a window with mutation rule analysis.
    
    Shows:
        - Active mutation rule and configuration
        - Rule trigger conditions
        - Performance impact metrics
    """
    if not HAS_MATPLOTLIB:
        return
    
    fig = plt.figure(figsize=(12, 6))
    fig.suptitle('Mutation Rule Analysis', fontsize=14, fontweight='bold')
    
    gs = gridspec.GridSpec(1, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Plot 1: Rule information
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    
    if not hasattr(simulation, 'mutation_rule') or simulation.mutation_rule is None:
        ax1.text(0.5, 0.5, 'No mutation rule configured',
                transform=ax1.transAxes, ha='center', va='center',
                fontsize=12, color='gray')
    else:
        rule = simulation.mutation_rule
        rule_type = rule.__class__.__name__
        
        rule_text = f"MUTATION RULE CONFIGURATION\n" + "=" * 45 + "\n\n"
        rule_text += f"Active Rule: {rule_type}\n\n"
        
        if rule_type == "PerformanceBasedMutation":
            if hasattr(rule, 'window'):
                rule_text += f"Observation Window:  {rule.window} ticks\n"
            if hasattr(rule, 'earnings_threshold'):
                rule_text += f"Earnings Threshold:  {rule.earnings_threshold:.2f}\n"
            if hasattr(rule, 'mutation_count'):
                rule_text += f"Mutations Performed: {rule.mutation_count}\n"
            rule_text += "\nTrigger Condition:\n"
            rule_text += "  Drivers with earnings below threshold\n"
            rule_text += "  switch to higher-earning behaviours\n"
            
        elif rule_type == "ExplorationMutation":
            if hasattr(rule, 'mutation_probability'):
                rule_text += f"Mutation Probability: {rule.mutation_probability:.3f}\n"
            if hasattr(rule, 'mutation_count'):
                rule_text += f"Mutations Performed: {rule.mutation_count}\n"
            rule_text += "\nTrigger Condition:\n"
            rule_text += "  Random exploration with fixed probability\n"
            rule_text += "  each simulation tick\n"
        else:
            rule_text += f"Custom Rule: {rule_type}\n"
        
        ax1.text(0.1, 0.95, rule_text, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    
    # Plot 2: Impact metrics
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    
    total_requests = simulation.served_count + simulation.expired_count
    service_level = (simulation.served_count / total_requests * 100) if total_requests > 0 else 0
    
    impact_text = "PERFORMANCE IMPACT\n" + "=" * 45 + "\n\n"
    impact_text += f"Final Service Level:  {service_level:.1f}%\n"
    impact_text += f"  • Served:           {simulation.served_count}\n"
    impact_text += f"  • Expired:          {simulation.expired_count}\n"
    impact_text += f"  • Total Requests:   {total_requests}\n\n"
    impact_text += f"Average Wait Time:    {simulation.avg_wait:.2f} ticks\n"
    impact_text += f"Simulation Duration:  {simulation.time} ticks\n"
    impact_text += f"Total Drivers:        {len(simulation.drivers)}\n"
    
    ax2.text(0.1, 0.95, impact_text, transform=ax2.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    
    # Open blocking so windows stay open
    plt.show()



