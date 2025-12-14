"""Post-simulation metrics visualization with 3 interactive windows."""

from typing import Optional

from .helpers_2.metrics_helpers import (
    SimulationTimeSeries, get_behaviour_distribution, PLOT_COLOURS,
    format_summary_statistics, format_behaviour_statistics,
    format_impact_metrics, format_mutation_rule_info
)

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def generate_report(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Generate 3 matplotlib windows: metrics, behaviour analysis, and mutation analysis.
    
    Args:
        simulation: Completed DeliverySimulation instance
        time_series: Optional SimulationTimeSeries with recorded metrics
    """
    
    # ====================================================================
    # Create all 3 windows
    # ====================================================================
    _show_mutation_window(simulation, time_series) # window 3
    _show_behaviour_window(simulation, time_series) # window 2
    _show_metrics_window(simulation, time_series) # window 1
    
    # Display all windows and wait for user to close them
    print("\n Report windows opened. Close the windows to continue.")
    plt.show()


# ====================================================================
# GENERIC PLOTTING UTILITIES
# ====================================================================

def _plot_time_series(ax, times, data, label, color, title, ylabel, fill=False):
    """Plot time-series line with optional fill."""
    if times is None or len(times) == 0:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title(title)
        return
    
    ax.plot(times, data, linewidth=2, color=color, marker='.', label=label)
    if fill:
        ax.fill_between(times, data, alpha=0.2, color=color)
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)


# ====================================================================
# INDIVIDUAL PLOT FUNCTIONS
# ====================================================================

def _plot_requests_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot cumulative served and expired requests over time."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_title('Served vs Expired Requests')
        return
    
    data = time_series.get_data()
    _plot_time_series(ax, data['times'], data['served'], 'Served', 'green',
                     'Request Fulfillment Evolution', 'Cumulative Count', fill=True)
    
    # Add expired as second series
    ax.plot(data['times'], data['expired'], linewidth=2, color='red', marker='s', 
            markersize=2, label='Expired')
    ax.fill_between(data['times'], data['expired'], alpha=0.2, color='red')
    ax.legend(loc='upper left')


def _plot_wait_time_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot average wait time trend over simulation."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Average Wait Time')
        return
    
    data = time_series.get_data()
    _plot_time_series(ax, data['times'], data['avg_wait'], 'Wait Time', 'steelblue',
                     'Average Wait Time Trend', 'Average Wait (ticks)', fill=True)


def _plot_pending_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot number of pending (unserved) requests over time."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Pending Requests')
        return
    
    data = time_series.get_data()
    _plot_time_series(ax, data['times'], data['pending'], 'Pending', 'darkorange',
                     'Pending Requests Over Time', 'Pending Count', fill=True)


def _plot_utilization_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot driver utilization (% busy) over time."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Driver Utilization')
        return
    
    data = time_series.get_data()
    _plot_time_series(ax, data['times'], data['utilization'], 'Utilization', 'indigo',
                     'Driver Utilization Trend', 'Utilization (%)', fill=True)
    ax.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Max')
    ax.set_ylim([0, 110])
    ax.legend(loc='upper left')


def _plot_behaviour_distribution_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot behaviour distribution evolution as stacked area chart."""
    if time_series is None or not time_series.behaviour_distribution:
        ax.text(0.5, 0.5, 'No behaviour data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Behaviour Distribution Evolution')
        return
    
    # Collect all behaviour types across all ticks
    all_behaviours = set()
    for dist_dict in time_series.behaviour_distribution:
        all_behaviours.update(dist_dict.keys())
    
    all_behaviours = sorted(list(all_behaviours))
    
    # Build data for each behaviour type over time
    behaviour_series = {behaviour: [] for behaviour in all_behaviours}
    for dist_dict in time_series.behaviour_distribution:
        for behaviour in all_behaviours:
            behaviour_series[behaviour].append(dist_dict.get(behaviour, 0))
    
    # Plot stacked area chart (use PLOT_COLOURS constant)
    ax.stackplot(time_series.times, 
                 *[behaviour_series[b] for b in all_behaviours],
                 labels=all_behaviours,
                 colors=PLOT_COLOURS[:len(all_behaviours)],
                 alpha=0.7)
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Number of Drivers')
    ax.set_title('Behaviour Distribution Evolution')
    
    # Handle legend overflow for many behaviours
    if len(all_behaviours) > 6:
        ax.legend(loc='upper left', fontsize=8, ncol=2, framealpha=0.9)
    else:
        ax.legend(loc='upper left', fontsize=9)
    
    ax.grid(True, alpha=0.3)


def _plot_mutations_and_stagnation(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot cumulative mutations and earnings stagnation events over time."""
    if time_series is None or not time_series.behaviour_mutations:
        ax.text(0.5, 0.5, 'No mutation/stagnation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutations & Earnings Stagnation Events')
        return
    
    ax2 = ax.twinx()
    
    # Plot mutations as line
    ax.plot(time_series.times, time_series.behaviour_mutations,
            linewidth=2, color='red', marker='o', markersize=3, label='Cumulative Mutations')
    ax.fill_between(time_series.times, time_series.behaviour_mutations, 
                    alpha=0.2, color='red')
    
    # Plot earnings stagnation events as line on secondary axis
    ax2.plot(time_series.times, time_series.earnings_stagnation_events,
             linewidth=2, color='orange', marker='s', markersize=3, label='Earnings Stagnation Events')
    ax2.fill_between(time_series.times, time_series.earnings_stagnation_events,
                     alpha=0.2, color='orange')
    
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Cumulative Mutations', color='red')
    ax2.set_ylabel('Earnings Stagnation Events', color='orange')
    ax.set_title('Mutations & Earnings Stagnation Events')
    ax.tick_params(axis='y', labelcolor='red')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax.grid(True, alpha=0.3)
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')


def _plot_summary_statistics(ax, simulation, time_series: Optional[SimulationTimeSeries]) -> None:
    """Display final simulation summary statistics as text."""
    ax.axis('off')
    stats_text = format_summary_statistics(simulation, time_series)
    ax.text(0.1, 0.95, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))





# ====================================================================
# BEHAVIOUR & MUTATION ANALYSIS WINDOWS
# ====================================================================

def _show_metrics_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display window with simulation metrics plots."""
    fig1 = plt.figure(num=1, figsize=(16, 13))
    fig1.suptitle('Post-Simulation Metrics Report', fontsize=16, fontweight='bold')
    
    gs = gridspec.GridSpec(3, 2, figure=fig1, hspace=0.50, wspace=0.40, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Plot 1: Served vs Expired (cumulative)
    ax1 = fig1.add_subplot(gs[0, :])
    _plot_requests_evolution(ax1, time_series)
    
    # Plot 2: Average Wait Time
    ax2 = fig1.add_subplot(gs[1, 0])
    _plot_wait_time_evolution(ax2, time_series)
    
    # Plot 3: Pending Requests
    ax3 = fig1.add_subplot(gs[1, 1])
    _plot_pending_evolution(ax3, time_series)
    
    # Plot 4: Driver Utilization
    ax4 = fig1.add_subplot(gs[2, 0])
    _plot_utilization_evolution(ax4, time_series)
    
    # Plot 5: Summary Statistics
    ax5 = fig1.add_subplot(gs[2, 1])
    _plot_summary_statistics(ax5, simulation, time_series)



def _show_behaviour_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display window with behaviour distribution plots and statistics."""
    
    # Create figure with 3 rows if we have time-series data, 2 rows otherwise
    num_rows = 3 if (time_series and time_series.behaviour_distribution) else 2
    fig_height = 14 if num_rows == 3 else 11
    fig2 = plt.figure(num=2, figsize=(16, fig_height))
    fig2.suptitle('Driver Behaviour Analysis', fontsize=14, fontweight='bold')
    
    gs = gridspec.GridSpec(num_rows, 2, figure=fig2, hspace=0.50, wspace=0.40, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Count behaviour types using helper
    behaviour_counts = get_behaviour_distribution(simulation)
    
    if not behaviour_counts:
        fig2.text(0.5, 0.5, 'No driver behaviour data available', 
                ha='center', va='center', fontsize=12)
        return
    
    plot_idx = 0
    
    # Plot 0 (if available): Behaviour distribution evolution over time
    if time_series and time_series.behaviour_distribution:
        ax0 = fig2.add_subplot(gs[0, :])
        _plot_behaviour_distribution_evolution(ax0, time_series)
        plot_idx = 1
    
    # Plot 1: Pie chart of behaviour distribution (final)
    ax1 = fig2.add_subplot(gs[plot_idx, 0])
    ax1.pie(behaviour_counts.values(), labels=behaviour_counts.keys(), 
            autopct='%1.1f%%', colors=PLOT_COLOURS, startangle=90)
    ax1.set_title('Behaviour Distribution')
    
    # Plot 2: Bar chart of behaviour counts
    ax2 = fig2.add_subplot(gs[plot_idx, 1])
    behaviours = list(behaviour_counts.keys())
    counts = list(behaviour_counts.values())
    bars = ax2.bar(range(len(behaviours)), counts, color=PLOT_COLOURS[:len(behaviours)])
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
    ax3 = fig2.add_subplot(gs[plot_idx + 1, :])
    ax3.axis('off')
    
    stats_text = format_behaviour_statistics(simulation, time_series)
    ax3.text(0.1, 0.95, stats_text, transform=ax3.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))


def _show_mutation_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display window with mutation rule configuration and earnings stagnation analysis."""
    
    fig3 = plt.figure(num=3, figsize=(16, 12))
    fig3.suptitle('Mutation Rule & Earnings Stagnation Analysis', fontsize=14, fontweight='bold')
    
    # Create grid with 2 rows if time-series available, 1 row otherwise
    num_rows = 2 if (time_series and time_series.behaviour_mutations) else 1
    gs = gridspec.GridSpec(num_rows, 2, figure=fig3, hspace=0.50, wspace=0.40, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Plot 1: Rule information
    ax1 = fig3.add_subplot(gs[0, 0])
    ax1.axis('off')
    
    rule_text = format_mutation_rule_info(simulation)
    ax1.text(0.1, 0.95, rule_text, transform=ax1.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    
    # Plot 2: Impact metrics
    ax2 = fig3.add_subplot(gs[0, 1])
    ax2.axis('off')
    
    impact_text = format_impact_metrics(simulation)
    ax2.text(0.1, 0.95, impact_text, transform=ax2.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    
    # Plot 3: Mutations and stagnation over time (if available)
    if time_series and time_series.behaviour_mutations:
        ax3 = fig3.add_subplot(gs[1, :])
        _plot_mutations_and_stagnation(ax3, time_series)



