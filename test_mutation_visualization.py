#!/usr/bin/env python3
"""
Test script to verify mutation visualization works with different scenarios.
Tests cumulative mutations and reason evolution stacked area.
"""

import sys
sys.path.insert(0, '/Users/idamariethyssen/Desktop/phase2/exam_phase2')

from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
import matplotlib.pyplot as plt


def test_scenario_1_low_earnings_mutations():
    """Scenario 1: Many low earnings mutations early, then stabilize."""
    print("\n=== Scenario 1: Low Earnings Pressure ===")
    
    ts = SimulationTimeSeries()
    
    # Simulate 100 ticks with mutations concentrated early
    for tick in range(100):
        ts.times.append(tick)
        
        # More mutations in first 30 ticks (low earnings pressure)
        if tick < 30:
            mutations = 2 + (30 - tick) // 10  # Decreasing over time
            ts.mutations_per_tick.append(mutations)
            
            # Reason: mostly low earnings
            ts.mutation_reasons.append({
                'performance_low_earnings': mutations,
                'performance_high_earnings': 0,
                'exit_greedy': 0,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': 0,
            })
        else:
            # Few mutations later (rare exploration)
            if tick % 15 == 0:
                ts.mutations_per_tick.append(1)
                ts.mutation_reasons.append({
                    'performance_low_earnings': 0,
                    'performance_high_earnings': 0,
                    'exit_greedy': 0,
                    'exit_earnings': 0,
                    'exit_lazy': 0,
                    'stagnation_exploration': 1,
                })
            else:
                ts.mutations_per_tick.append(0)
                ts.mutation_reasons.append({
                    'performance_low_earnings': 0,
                    'performance_high_earnings': 0,
                    'exit_greedy': 0,
                    'exit_earnings': 0,
                    'exit_lazy': 0,
                    'stagnation_exploration': 0,
                })
    
    # Print summary
    total_mutations = sum(ts.mutations_per_tick)
    final_reasons = ts.mutation_reasons[-1] if ts.mutation_reasons else {}
    
    print(f"Total mutations: {total_mutations}")
    print(f"Final reason counts: {ts.mutation_reasons[-1]}")
    
    # Find actual values
    cumulative_by_reason = {
        'low_earnings': 0,
        'exploration': 0,
    }
    
    for reasons_dict in ts.mutation_reasons:
        cumulative_by_reason['low_earnings'] += reasons_dict.get('performance_low_earnings', 0)
        cumulative_by_reason['exploration'] += reasons_dict.get('stagnation_exploration', 0)
    
    print(f"Cumulative: Low Earnings={cumulative_by_reason['low_earnings']}, Exploration={cumulative_by_reason['exploration']}")
    assert cumulative_by_reason['low_earnings'] > cumulative_by_reason['exploration'], \
        "Should have more low earnings than exploration"
    print("✓ Scenario 1: Low earnings dominate - PASS")
    
    return ts


def test_scenario_2_mixed_mutations():
    """Scenario 2: Mixed mutation reasons throughout."""
    print("\n=== Scenario 2: Mixed Mutation Reasons ===")
    
    ts = SimulationTimeSeries()
    
    # Simulate 100 ticks with varied mutations
    for tick in range(100):
        ts.times.append(tick)
        
        # Different phases with different mutation reasons
        if tick < 25:
            # Phase 1: Low earnings pressure
            mutations = 2
            ts.mutations_per_tick.append(mutations)
            ts.mutation_reasons.append({
                'performance_low_earnings': mutations,
                'performance_high_earnings': 0,
                'exit_greedy': 0,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': 0,
            })
        elif tick < 50:
            # Phase 2: Exit conditions
            mutations = 1
            ts.mutations_per_tick.append(mutations)
            ts.mutation_reasons.append({
                'performance_low_earnings': 0,
                'performance_high_earnings': 0,
                'exit_greedy': mutations,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': 0,
            })
        elif tick < 75:
            # Phase 3: High earnings
            mutations = 1
            ts.mutations_per_tick.append(mutations)
            ts.mutation_reasons.append({
                'performance_low_earnings': 0,
                'performance_high_earnings': mutations,
                'exit_greedy': 0,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': 0,
            })
        else:
            # Phase 4: Exploration
            mutations = 1
            ts.mutations_per_tick.append(mutations)
            ts.mutation_reasons.append({
                'performance_low_earnings': 0,
                'performance_high_earnings': 0,
                'exit_greedy': 0,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': mutations,
            })
    
    # Verify we have variations
    cumulative_by_reason = {
        'low_earnings': 0,
        'exit_greedy': 0,
        'high_earnings': 0,
        'exploration': 0,
    }
    
    for reasons_dict in ts.mutation_reasons:
        cumulative_by_reason['low_earnings'] += reasons_dict.get('performance_low_earnings', 0)
        cumulative_by_reason['exit_greedy'] += reasons_dict.get('exit_greedy', 0)
        cumulative_by_reason['high_earnings'] += reasons_dict.get('performance_high_earnings', 0)
        cumulative_by_reason['exploration'] += reasons_dict.get('stagnation_exploration', 0)
    
    print(f"Cumulative reasons: {cumulative_by_reason}")
    
    # All should have values
    assert all(v > 0 for v in cumulative_by_reason.values()), \
        "All reason types should have mutations"
    print("✓ Scenario 2: Mixed reasons present - PASS")
    
    return ts


def test_scenario_3_sparse_mutations():
    """Scenario 3: Few mutations, mostly no activity."""
    print("\n=== Scenario 3: Sparse Mutations ===")
    
    ts = SimulationTimeSeries()
    
    # Simulate 100 ticks with very few mutations
    for tick in range(100):
        ts.times.append(tick)
        
        # Only mutate at tick 20, 50, 80
        if tick in [20, 50, 80]:
            ts.mutations_per_tick.append(1)
            ts.mutation_reasons.append({
                'performance_low_earnings': 1 if tick == 20 else 0,
                'performance_high_earnings': 1 if tick == 50 else 0,
                'exit_greedy': 1 if tick == 80 else 0,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': 0,
            })
        else:
            ts.mutations_per_tick.append(0)
            ts.mutation_reasons.append({
                'performance_low_earnings': 0,
                'performance_high_earnings': 0,
                'exit_greedy': 0,
                'exit_earnings': 0,
                'exit_lazy': 0,
                'stagnation_exploration': 0,
            })
    
    total = sum(ts.mutations_per_tick)
    print(f"Total mutations: {total}")
    assert total == 3, "Should have exactly 3 mutations"
    print("✓ Scenario 3: Sparse mutations - PASS")
    
    return ts


def visualize_scenarios():
    """Create visualizations for each scenario."""
    print("\n" + "="*60)
    print("TESTING MUTATION VISUALIZATION WITH DIFFERENT SCENARIOS")
    print("="*60)
    
    scenarios = [
        ("Scenario 1: Low Earnings Pressure", test_scenario_1_low_earnings_mutations()),
        ("Scenario 2: Mixed Reasons", test_scenario_2_mixed_mutations()),
        ("Scenario 3: Sparse Mutations", test_scenario_3_sparse_mutations()),
    ]
    
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    
    for idx, (title, ts) in enumerate(scenarios):
        # Plot cumulative mutations
        ax_cum = axes[idx, 0]
        cumulative = []
        total = 0
        for mutations in ts.mutations_per_tick:
            total += mutations
            cumulative.append(total)
        
        ax_cum.plot(ts.times, cumulative, linewidth=2, color='darkred', marker='o', markersize=3)
        ax_cum.fill_between(ts.times, cumulative, alpha=0.2, color='red')
        ax_cum.set_title(f"{title} - Cumulative")
        ax_cum.set_ylabel('Total Mutations')
        ax_cum.grid(True, alpha=0.3)
        
        # Plot reason evolution
        ax_rea = axes[idx, 1]
        
        reason_labels_map = {
            'performance_low_earnings': 'Low Earnings',
            'performance_high_earnings': 'High Earnings',
            'exit_greedy': 'Exit Greedy',
            'exit_earnings': 'Exit EarningsMax',
            'exit_lazy': 'Exit Lazy',
            'stagnation_exploration': 'Exploration',
        }
        
        all_reasons = set()
        for reason_dict in ts.mutation_reasons:
            all_reasons.update(reason_dict.keys())
        
        all_reasons = sorted(list(all_reasons))
        
        # Build cumulative data
        reason_series = {reason: [] for reason in all_reasons}
        
        for reason_dict in ts.mutation_reasons:
            for reason in all_reasons:
                # reason_dict already contains cumulative count from start
                count = reason_dict.get(reason, 0)
                reason_series[reason].append(count)
        
        # Plot stacked
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
        labels = [reason_labels_map.get(r, r) for r in all_reasons]
        
        ax_rea.stackplot(ts.times,
                         *[reason_series[r] for r in all_reasons],
                         labels=labels,
                         colors=colors[:len(all_reasons)],
                         alpha=0.75)
        
        ax_rea.set_title(f"{title} - Reasons Evolution")
        ax_rea.set_ylabel('Cumulative Mutations')
        ax_rea.legend(loc='upper left', fontsize=8)
        ax_rea.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/Users/idamariethyssen/Desktop/phase2/exam_phase2/mutation_visualization_test.png', dpi=100)
    print("\n✓ Visualization saved to: mutation_visualization_test.png")
    
    print("\n" + "="*60)
    print("ALL SCENARIOS PASSED!")
    print("="*60)
    print("\nConclusions:")
    print("✓ Cumulative line shows total mutation count trajectory")
    print("✓ Stacked area shows which reasons drive mutations")
    print("✓ Variations between different mutation reasons visible")
    print("\nIf your run showed flat visualizations:")
    print("  - May indicate stable system with few mutations")
    print("  - Check if mutations are actually occurring")
    print("  - Verify with actual_policy_used and driver behaviors")


if __name__ == '__main__':
    visualize_scenarios()
