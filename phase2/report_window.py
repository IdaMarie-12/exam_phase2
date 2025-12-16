"""Post-simulation metrics visualization with 4 specialized report windows."""

from typing import Optional

try:
    # Try relative import first (when imported as module)
    from .helpers_2.metrics_helpers import (
        SimulationTimeSeries, get_behaviour_distribution, PLOT_COLOURS,
        format_summary_statistics, format_behaviour_statistics,
        format_impact_metrics, format_mutation_rule_info
    )
except ImportError:
    # Fallback to absolute import (for direct execution)
    from phase2.helpers_2.metrics_helpers import (
        SimulationTimeSeries, get_behaviour_distribution, PLOT_COLOURS,
        format_summary_statistics, format_behaviour_statistics,
        format_impact_metrics, format_mutation_rule_info
    )

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import Counter


def generate_report(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Generate 4 report windows with 15 plots."""
    
    _show_metrics_window(simulation, time_series)           # Window 1: System Efficiency
    _show_behaviour_window(simulation, time_series)         # Window 2: Behaviour Dynamics
    _show_mutation_root_cause_window(simulation, time_series)  # Window 3: Mutation Root Cause
    _show_policy_offer_window(simulation, time_series)      # Window 4: Policy & Offer Effectiveness
    
    print("\nReport windows opened. Close the windows to continue.")
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
# WINDOW 1: SYSTEM EFFICIENCY
# ====================================================================

def _show_metrics_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display Window 1: System efficiency metrics."""
    fig1 = plt.figure(num=1, figsize=(16, 15))
    fig1.suptitle('System Efficiency Overview', fontsize=16, fontweight='bold')
    
    gs = gridspec.GridSpec(4, 2, figure=fig1, hspace=0.50, wspace=0.40, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Plot 1: Served vs Expired (cumulative)
    ax1 = fig1.add_subplot(gs[0, :])
    _plot_requests_evolution(ax1, time_series)
    
    # Plot 2: Service Level % over time
    ax2 = fig1.add_subplot(gs[1, 0])
    _plot_service_level_evolution(ax2, time_series)
    
    # Plot 3: Pending Requests Queue
    ax3 = fig1.add_subplot(gs[1, 1])
    _plot_pending_requests(ax3, time_series)
    
    # Plot 4: Driver Utilization
    ax4 = fig1.add_subplot(gs[2, 0])
    _plot_utilization_evolution(ax4, time_series)
    
    # Plot 5: Request Age Pressure
    ax5 = fig1.add_subplot(gs[2, 1])
    _plot_request_age_evolution(ax5, simulation, time_series)
    
    # Plot 6: Summary Statistics
    ax6 = fig1.add_subplot(gs[3, :])
    _plot_summary_statistics(ax6, simulation, time_series)


def _plot_requests_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot cumulative served and expired requests."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_title('Served vs Expired Requests')
        return
    
    _plot_time_series(ax, time_series.times, time_series.served, 'Served', 'green',
                     'Request Fulfillment Evolution', 'Cumulative Count', fill=True)
    
    # Add expired as second series
    ax.plot(time_series.times, time_series.expired, linewidth=2, color='red', marker='s', 
            markersize=2, label='Expired')
    ax.fill_between(time_series.times, time_series.expired, alpha=0.2, color='red')
    ax.legend(loc='upper left')


def _plot_service_level_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot service level (% served) trend."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Service Level')
        return
    
    _plot_time_series(ax, time_series.times, time_series.service_level, 'Service Level', 'darkgreen',
                     'Service Level Evolution (% Served)', 'Service Level (%)', fill=True)
    ax.set_ylim([0, 105])


def _plot_utilization_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot driver utilization (% busy) over time."""
    if time_series is None or not time_series.times:
        ax.text(0.5, 0.5, 'No time-series data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Driver Utilization')
        return
    
    _plot_time_series(ax, time_series.times, time_series.utilization, 'Utilization', 'indigo',
                     'Driver Utilization Trend', 'Utilization (%)', fill=True)
    ax.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Max')
    ax.set_ylim([0, 110])
    ax.legend(loc='upper left')


def _plot_pending_requests(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot pending requests queue depth."""
    if time_series is None or not time_series.pending_requests:
        ax.text(0.5, 0.5, 'No pending request data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Pending Requests Queue')
        return
    
    _plot_time_series(ax, time_series.times, time_series.pending_requests, 'Pending', 'orange',
                     'Pending Requests Over Time', 'Queue Depth', fill=True)


def _plot_request_age_evolution(ax, simulation, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot max and average request age vs timeout threshold."""
    if time_series is None or not time_series.max_request_age:
        ax.text(0.5, 0.5, 'No request age data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Request Age Pressure')
        return
    
    ax.plot(time_series.times, time_series.max_request_age, linewidth=2, color='red', 
            marker='.', label='Max Age (oldest request)', alpha=0.7)
    ax.plot(time_series.times, time_series.avg_request_age, linewidth=2, color='orange', 
            marker='s', markersize=2, label='Avg Age', alpha=0.7)
    
    # Add timeout threshold line
    timeout = simulation.timeout
    ax.axhline(y=timeout, color='darkred', linestyle='--', linewidth=2.5, 
               label=f'Timeout Threshold ({timeout} ticks)', alpha=0.8)
    
    ax.fill_between(time_series.times, time_series.max_request_age, alpha=0.15, color='red')
    ax.set_xlabel('Simulation Time (ticks)')
    ax.set_ylabel('Request Age (ticks)')
    ax.set_title('Request Age Pressure (Queue Latency vs Timeout)')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)


def _plot_summary_statistics(ax, simulation, time_series: Optional[SimulationTimeSeries]) -> None:
    """Display final simulation summary statistics as text."""
    ax.axis('off')
    stats_text = format_summary_statistics(simulation, time_series)
    ax.text(0.1, 0.95, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


# ====================================================================
# WINDOW 2: BEHAVIOUR DYNAMICS
# ====================================================================

def _show_behaviour_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display Window 2: Behaviour dynamics and stability."""
    
    # Create figure with 3 rows if we have time-series data, 2 rows otherwise
    num_rows = 3 if (time_series and time_series.behaviour_distribution) else 2
    fig_height = 14 if num_rows == 3 else 11
    fig2 = plt.figure(num=2, figsize=(16, fig_height))
    fig2.suptitle('Behaviour Dynamics', fontsize=14, fontweight='bold')
    
    gs = gridspec.GridSpec(num_rows, 2, figure=fig2, hspace=0.50, wspace=0.40, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Get all possible behaviours from time-series or final state
    all_behaviours = set()
    if time_series and time_series.behaviour_distribution:
        for dist_dict in time_series.behaviour_distribution:
            all_behaviours.update(dist_dict.keys())
    
    behaviour_counts = get_behaviour_distribution(simulation)
    if not behaviour_counts and not all_behaviours:
        fig2.text(0.5, 0.5, 'No driver behaviour data available', 
                ha='center', va='center', fontsize=12)
        return
    
    plot_idx = 0
    
    # Plot 0 (if available): Behaviour distribution evolution over time
    if time_series and time_series.behaviour_distribution:
        ax0 = fig2.add_subplot(gs[0, :])
        _plot_behaviour_distribution_evolution(ax0, time_series)
        plot_idx = 1
    
    # Plot 1: Pie chart of behaviour distribution (final) - only non-zero values
    ax1 = fig2.add_subplot(gs[plot_idx, 0])
    if behaviour_counts:
        ax1.pie(behaviour_counts.values(), labels=behaviour_counts.keys(), 
                autopct='%1.1f%%', colors=PLOT_COLOURS, startangle=90)
    ax1.set_title('Final Behaviour Distribution')
    
    # Plot 2: Bar chart of ALL possible behaviours (including zeros)
    # Count how many times each behaviour appeared across entire simulation
    ax2 = fig2.add_subplot(gs[plot_idx, 1])
    all_behaviours_sorted = sorted(list(all_behaviours.union(set(behaviour_counts.keys()))))
    
    # For historical overview: count total driver-behaviour instances across all ticks
    behaviour_total_counts = {b: 0 for b in all_behaviours_sorted}
    if time_series and time_series.behaviour_distribution:
        for dist_dict in time_series.behaviour_distribution:
            for behaviour, count in dist_dict.items():
                if behaviour in behaviour_total_counts:
                    behaviour_total_counts[behaviour] += count
    
    # For current state: add final behaviour counts (drivers at end of simulation)
    for behaviour, count in behaviour_counts.items():
        if behaviour not in behaviour_total_counts:
            behaviour_total_counts[behaviour] = 0
        behaviour_total_counts[behaviour] += count
    
    counts = [behaviour_total_counts.get(b, 0) for b in all_behaviours_sorted]
    bars = ax2.bar(range(len(all_behaviours_sorted)), counts, color=PLOT_COLOURS[:len(all_behaviours_sorted)])
    ax2.set_xticks(range(len(all_behaviours_sorted)))
    ax2.set_xticklabels(all_behaviours_sorted, rotation=45, ha='right', fontsize=9)
    ax2.set_ylabel('Total Behaviour-Tick Count')
    ax2.set_title('Behaviour Presence Over Time (Aggregated)')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:  # Only show labels for non-zero values
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
    
    # Plot 3: Behaviour statistics and stability
    ax3 = fig2.add_subplot(gs[plot_idx + 1, :])
    ax3.axis('off')
    
    stats_text = format_behaviour_statistics(simulation, time_series)
    ax3.text(0.1, 0.95, stats_text, transform=ax3.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))


def _plot_behaviour_distribution_evolution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot behaviour distribution evolution as stacked area."""
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


# ====================================================================
# WINDOW 3: MUTATION ROOT CAUSE ANALYSIS
# ====================================================================

def _show_mutation_root_cause_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display Window 3: Mutation analysis with 3-category focus and 6-reason details."""
    
    fig3 = plt.figure(num=3, figsize=(16, 12))
    fig3.suptitle('Mutation Root Cause Analysis', fontsize=14, fontweight='bold')
    
    gs = gridspec.GridSpec(2, 2, figure=fig3, hspace=0.35, wspace=0.35, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Plot 1 (Top-Left): 3-Category Pie Chart
    ax1 = fig3.add_subplot(gs[0, 0])
    _plot_mutation_categories_pie(ax1, time_series)
    
    # Plot 2 (Top-Right): 3-Category Bar Chart
    ax2 = fig3.add_subplot(gs[0, 1])
    _plot_mutation_categories_bar(ax2, time_series)
    
    # Plot 3 (Bottom-Left): 6-Reason Breakdown
    ax3 = fig3.add_subplot(gs[1, 0])
    _plot_mutation_reason_breakdown_detailed(ax3, time_series)
    
    # Plot 4 (Bottom-Right): Driver Mutation Frequency
    ax4 = fig3.add_subplot(gs[1, 1])
    _plot_driver_mutation_frequency(ax4, time_series)


def _plot_mutation_categories_pie(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot 3-category mutation distribution as pie chart."""
    if time_series is None:
        ax.text(0.5, 0.5, 'No mutation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Categories (3-Way Split)')
        return
    
    summary = time_series.get_final_summary()
    if not summary or 'entry_performance_based' not in summary:
        ax.text(0.5, 0.5, 'No mutation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Categories (3-Way Split)')
        return
    
    categories = {
        'Performance-Based Entry': summary.get('entry_performance_based', 0),
        'Stagnation-Based Entry': summary.get('entry_stagnation_exploration', 0),
        'Exit Safety Valve': summary.get('exit_safety_valve', 0)
    }
    
    total = sum(categories.values())
    if total == 0:
        ax.text(0.5, 0.5, 'No mutations', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Categories (3-Way Split)')
        return
    
    colors = ['#2ecc71', '#e74c3c', '#f39c12']  # Green, Red, Orange
    wedges, texts, autotexts = ax.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%',
                                        colors=colors, startangle=90, textprops={'fontsize': 10})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Mutation Categories (3-Way Split)')


def _plot_mutation_categories_bar(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot 3-category mutation counts as bar chart."""
    if time_series is None:
        ax.text(0.5, 0.5, 'No mutation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Counts by Category')
        return
    
    summary = time_series.get_final_summary()
    if not summary or 'entry_performance_based' not in summary:
        ax.text(0.5, 0.5, 'No mutation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Counts by Category')
        return
    
    categories = {
        'Performance-Based': summary.get('entry_performance_based', 0),
        'Stagnation-Based': summary.get('entry_stagnation_exploration', 0),
        'Exit Safety': summary.get('exit_safety_valve', 0)
    }
    
    colors = ['#2ecc71', '#e74c3c', '#f39c12']  # Green, Red, Orange
    bars = ax.bar(categories.keys(), categories.values(), color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Count')
    ax.set_title('Mutation Counts by Category')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')


def _plot_mutation_reason_breakdown_detailed(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot detailed breakdown of all 6 mutation reasons."""
    if time_series is None:
        ax.text(0.5, 0.5, 'No mutation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Reasons (6-Way Breakdown)')
        return
    
    summary = time_series.get_final_summary()
    if not summary or 'mutation_reason_breakdown' not in summary:
        ax.text(0.5, 0.5, 'No mutation reason data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Reasons (6-Way Breakdown)')
        return
    
    breakdown = summary.get('mutation_reason_breakdown', {})
    
    reason_labels = {
        'performance_low_earnings': 'Low Earnings',
        'performance_high_earnings': 'High Earnings',
        'stagnation_exploration': 'Stagnation',
        'exit_greedy': 'Exit Greedy',
        'exit_earnings': 'Exit Earnings',
        'exit_lazy': 'Exit Lazy'
    }
    
    # Distinct colors for 6 reasons (different from 3-category scheme)
    reason_colors = ['#3498db', '#9b59b6', '#1abc9c', '#f1c40f', '#e67e22', '#95a5a6']  # Blue, Purple, Teal, Yellow, Orange, Gray
    
    labels = [reason_labels.get(r, r) for r in breakdown.keys()]
    values = list(breakdown.values())
    
    if sum(values) == 0:
        ax.text(0.5, 0.5, 'No mutations', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Mutation Reasons (6-Way Breakdown)')
        return
    
    bars = ax.bar(range(len(labels)), values, color=reason_colors, alpha=0.8, edgecolor='black', linewidth=1)
    
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Count')
    ax.set_title('Mutation Reasons (6-Way Breakdown)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8, fontweight='bold')




def _plot_driver_mutation_frequency(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot distribution of mutations per driver."""
    if time_series is None or not time_series.driver_mutation_freq:
        ax.text(0.5, 0.5, 'No driver mutation data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Driver Mutation Frequency Distribution')
        return
    
    from collections import Counter
    mutation_freq_dist = Counter(time_series.driver_mutation_freq.values())
    frequencies = sorted(mutation_freq_dist.keys())
    counts = [mutation_freq_dist[f] for f in frequencies]
    
    bars = ax.bar(frequencies, counts, color='steelblue', width=0.8)
    ax.set_xlabel('Number of Mutations per Driver')
    ax.set_ylabel('Number of Drivers')
    ax.set_title('Driver Mutation Frequency Distribution')
    ax.set_xticks(frequencies)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')


# ====================================================================
# WINDOW 4: POLICY & OFFER EFFECTIVENESS
# ====================================================================

def _show_policy_offer_window(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    """Display window 4: Policy and offer analysis."""
    if time_series is None or (not time_series.offers_generated and not time_series.policy_distribution):
        fig = plt.figure(num=4, figsize=(16, 10))
        fig.suptitle('Policy & Offer Effectiveness', fontsize=16, fontweight='bold')
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'No offer/policy data available', ha='center', va='center',
                transform=ax.transAxes, fontsize=12)
        return
    
    fig4 = plt.figure(num=4, figsize=(16, 15))
    fig4.suptitle('Policy & Offer Effectiveness', fontsize=14, fontweight='bold')
    
    # Create grid: 4 rows, 2 columns
    gs = gridspec.GridSpec(4, 2, figure=fig4, hspace=0.40, wspace=0.40, top=0.96, bottom=0.06, left=0.08, right=0.96)
    
    # Plot 0: Offers generated over time
    ax0 = fig4.add_subplot(gs[0, 0])
    _plot_offers_generated(ax0, time_series)
    
    # Plot 1: Matching efficiency (% of offers that became assignments)
    ax1 = fig4.add_subplot(gs[0, 1])
    _plot_matching_efficiency(ax1, time_series)
    
    # Plot 2: Average offer quality
    ax2 = fig4.add_subplot(gs[1, 0])
    _plot_offer_quality(ax2, time_series)
    
    # Plot 3: Rejection rate
    ax3 = fig4.add_subplot(gs[1, 1])
    _plot_rejection_rate(ax3, time_series)
    
    # Plot 4: Policy distribution over time
    ax4 = fig4.add_subplot(gs[2, :])
    _plot_policy_distribution(ax4, time_series)
    
    # Plot 5: Summary statistics
    ax5 = fig4.add_subplot(gs[3, :])
    _plot_policy_offer_summary(ax5, simulation, time_series)


def _plot_offers_generated(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot number of offers generated over time."""
    if time_series is None or not time_series.offers_generated:
        ax.text(0.5, 0.5, 'No offer data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Offers Generated')
        return
    
    _plot_time_series(ax, time_series.times, time_series.offers_generated, 
                     'Offers', 'steelblue', 'Offers Generated Per Tick', 
                     'Number of Offers', fill=True)


def _plot_offer_quality(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot average offer quality (reward/time ratio) over time."""
    if time_series is None or not time_series.avg_offer_quality:
        ax.text(0.5, 0.5, 'No quality data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Average Offer Quality')
        return
    
    _plot_time_series(ax, time_series.times, time_series.avg_offer_quality,
                     'Quality', 'purple', 'Average Offer Quality (Reward/Time)',
                     'Reward per Time Unit', fill=True)


def _plot_matching_efficiency(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot matching efficiency (% of offers that became assignments)."""
    if time_series is None or not time_series.matching_efficiency:
        ax.text(0.5, 0.5, 'No efficiency data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Offer Matching Efficiency')
        return
    
    _plot_time_series(ax, time_series.times, time_series.matching_efficiency,
                     'Efficiency', 'darkgreen', 'Offer-to-Assignment Conversion Rate',
                     'Efficiency (%)', fill=True)
    ax.set_ylim([0, 105])


def _plot_rejection_rate(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot driver rejection rate (% of offers drivers reject)."""
    if time_series is None or not time_series.rejection_rate:
        ax.text(0.5, 0.5, 'No rejection data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Offer Rejection Rate')
        return
    
    _plot_time_series(ax, time_series.times, time_series.rejection_rate,
                     'Rejection', 'crimson', 'Driver Rejection Rate (Behaviour Impact)',
                     'Rejection Rate (%)', fill=True)
    ax.set_ylim([0, 105])


def _plot_policy_distribution(ax, time_series: Optional[SimulationTimeSeries]) -> None:
    """Plot actual policy usage over time as stacked bar chart (NN vs GG for AdaptiveHybrid, or single policy)."""
    if time_series is None or not time_series.actual_policy_used:
        ax.text(0.5, 0.5, 'No policy data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Policy Adoption Over Time')
        return
    
    all_policies = sorted(set(time_series.actual_policy_used))
    
    if not all_policies:
        ax.text(0.5, 0.5, 'No policy data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title('Policy Adoption Over Time')
        return
    
    # Bin the time series into time windows for bar chart
    bin_size = 50 if len(time_series.times) > 100 else max(10, len(time_series.times) // 10)
    
    # Create bins
    time_bins = []
    policy_counts_per_bin = {policy: [] for policy in all_policies}
    
    # Find max time and create bin edges
    max_time = max(time_series.times) if time_series.times else 100
    bin_edges = list(range(0, int(max_time) + bin_size, bin_size))
    
    # Count policies in each bin
    for i in range(len(bin_edges) - 1):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        time_bins.append(f"{bin_start}-{bin_end}")
        
        # Count policies in this time window
        for policy in all_policies:
            count = sum(1 for t, p in zip(time_series.times, time_series.actual_policy_used) 
                       if bin_start <= t < bin_end and p == policy)
            policy_counts_per_bin[policy].append(count)
    
    # Create stacked bar chart
    x_pos = range(len(time_bins))
    bottom = [0] * len(time_bins)
    
    for policy_idx, policy in enumerate(all_policies):
        color = PLOT_COLOURS[policy_idx % len(PLOT_COLOURS)]
        ax.bar(x_pos, policy_counts_per_bin[policy], bottom=bottom, 
               label=policy, color=color, alpha=0.8)
        # Update bottom for next policy
        bottom = [bottom[i] + policy_counts_per_bin[policy][i] for i in range(len(time_bins))]
    
    ax.set_xlabel('Simulation Time Window (ticks)')
    ax.set_ylabel('Policy Usage Count')
    ax.set_title('Policy Adoption Over Time (Stacked by Time Window)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(time_bins, rotation=45, ha='right', fontsize=9)
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')


def _plot_policy_offer_summary(ax, simulation, time_series: Optional[SimulationTimeSeries]) -> None:
    """Display summary statistics about policies and offers."""
    ax.axis('off')
    
    if not time_series:
        summary_text = "No offer/policy data available"
    else:
        summary = time_series.get_final_summary()
        
        # Build policy information
        policies_used = ', '.join(sorted(time_series.policy_names)) if time_series.policy_names else 'None'
        
        # If PolicyManager, show which sub-policy was actually used
        actual_policy_display = ""
        if 'PolicyManager' in time_series.policy_names and summary.get('actual_policy_usage'):
            actual_usage = summary.get('actual_policy_usage', {})
            nn_count = actual_usage.get('NearestNeighborPolicy', 0)
            gg_count = actual_usage.get('GlobalGreedyPolicy', 0)
            total_uses = nn_count + gg_count
            
            if total_uses > 0:
                nn_pct = (nn_count / total_uses * 100)
                gg_pct = (gg_count / total_uses * 100)
                actual_policy_display = f"""
Actual Sub-Policies Used:
  • NearestNeighbor:       {nn_count} ticks ({nn_pct:.1f}%)
  • GlobalGreedy:          {gg_count} ticks ({gg_pct:.1f}%)
"""
        
        summary_text = f"""
POLICY & OFFER SUMMARY
{'=' * 60}

Total Offers Generated:    {summary.get('total_offers_generated', 0)}
Average Acceptance Rate:   {summary.get('avg_acceptance_rate', 0):.1f}%
Average Offer Quality:     {summary.get('avg_offer_quality', 0):.4f} (Reward/Time)
Matching Efficiency:       {summary.get('avg_matching_efficiency', 0):.1f}%{actual_policy_display}
"""
    
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
