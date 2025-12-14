# Metrics and Report Window - Implementation Summary

## Changes Completed ✅

All fixes have been successfully implemented to align the metrics system with the actual mutation implementation.

### 1. **metrics_helpers.py Updates**

#### A. Renamed "Stagnation" → "Stability"
- Changed `behaviour_stagnation` → `behaviour_stability`
- Updated all references (7 locations)
- **Reason:** Original metric tracked drivers staying in same behaviour, not earnings stagnation

#### B. Added Real Earnings Stagnation Tracking
- New metric: `earnings_stagnation_events`
- Counts drivers with actual earnings stagnation (70% within ±5% of avg)
- Sourced from `mutation.mutation_history` with reason `"stagnation_exploration"`
- Implemented `_count_earnings_stagnation_events()` method

#### C. Added Mutation Reason Breakdown
- New internal tracking: `_mutation_reason_counts` dictionary
- Counts 5 mutation types:
  - `performance_low_earnings` (avg < 3.0)
  - `performance_high_earnings` (avg > 10.0)
  - `exit_greedy` (recovered to 5.0)
  - `exit_earnings` (dropped below 7.5)
  - `stagnation_exploration` (earnings stagnation)
- Implemented `_track_mutation_reasons()` method

#### D. Updated Mutation Rule Display
- **Removed obsolete attributes:**
  - `window` (was non-existent)
  - `stagnation_window` (was unified into 10-tick fixed window)

- **Added correct attributes:**
  - `greedy_exit_threshold` (5.0)
  - `earnings_max_exit_threshold` (7.5)
  - `exploration_prob` (0.3 = 30%)

- **Improved trigger conditions display:**
  - Clearer explanation of Low/High/Stagnation triggers
  - Shows Lazy vs Active driver exploration differences

- **Added Mutation Reason Breakdown section:**
  - Displays count and percentage for each mutation type
  - Example output:
    ```
    Mutation Reason Breakdown:
      • Low Earnings (< 3.0):        45  ( 15.0%)
      • High Earnings (> 10.0):      30  ( 10.0%)
      • Exit Greedy (>= 5.0):        20  (  6.7%)
      • Exit EarningsMax (< 7.5):    15  (  5.0%)
      • Stagnation Exploration:      190  ( 63.3%)
    ```

#### E. Updated Summary Statistics
- Changed `avg_stagnant_drivers` → `avg_stable_drivers`
- Added `avg_earnings_stagnation_events`
- Added `mutation_reason_breakdown` dict to final summary

### 2. **report_window.py Updates**

#### A. Plot Updates
- Updated `_plot_mutations_and_stagnation()`:
  - Now plots `earnings_stagnation_events` instead of `behaviour_stagnation`
  - Changed line color: blue → orange (for clarity)
  - Updated axis label: "Stagnant Drivers" → "Earnings Stagnation Events"

#### B. Window Titles
- `_show_mutation_window()` docstring: "...stagnation analysis" → "...earnings stagnation analysis"
- Figure suptitle: "Mutation Rule & Stagnation Analysis" → "Mutation Rule & Earnings Stagnation Analysis"

#### C. Summary Text Display
- Updated format_behaviour_statistics():
  - "Avg Stagnant Drivers" → "Avg Stable Drivers"
  - Added "Avg Earnings Stagnation"

#### D. Impact Metrics Display
- Shows breakdown of mutated drivers with percentages
- Remains unchanged (was already correct)

---

## Data Flow Improvements

### Before:
```
Simulation 
  → metrics.behaviour_stagnation (behaviour changes)
  → Plot shows "Stagnant Drivers" (misleading)
  → No connection to actual earnings stagnation
```

### After:
```
Simulation 
  → mutation_rule.mutation_history
    ├→ metrics.behaviour_stability (no behaviour change)
    ├→ metrics.earnings_stagnation_events (actual earnings stagnation)
    └→ metrics._mutation_reason_counts (breakdown by type)
  → Plots show real earnings stagnation events
  → Mutation reason breakdown visible in report
```

---

## API Changes

### New in SimulationTimeSeries:

```python
# Attributes
self.behaviour_stability          # Was: behaviour_stagnation
self.earnings_stagnation_events   # NEW
self._mutation_reason_counts      # NEW

# Methods
_count_earnings_stagnation_events()  # NEW
_track_mutation_reasons()            # NEW

# get_data() returns:
'behaviour_stability'               # Was: behaviour_stagnation
'earnings_stagnation_events'        # NEW

# get_final_summary() returns:
'avg_stable_drivers'                # Was: avg_stagnant_drivers
'avg_earnings_stagnation_events'    # NEW
'mutation_reason_breakdown'         # NEW
```

---

## Display Examples

### Summary Statistics (Before):
```
Behaviour Analysis:
  • Total Mutations:    150
  • Avg Stagnant:       2.3
```

### Summary Statistics (After):
```
Behaviour Analysis:
  • Total Mutations:    150
  • Avg Stable:         2.3
  • Avg Earnings Stag:  1.8
```

### Mutation Rule Info (Before):
```
Active Rule: HybridMutation

Performance Window:  [missing - was referencing non-existent attribute]
Low Earnings Threshold:  3.00
High Earnings Threshold:  10.00
Mutation Cooldown:  10 ticks
Stagnation Window:  [missing - was referencing non-existent attribute]
```

### Mutation Rule Info (After):
```
Active Rule: HybridMutation

Low Earnings Threshold:      3.00
High Earnings Threshold:     10.00
Mutation Cooldown:           10 ticks
Exploration Probability:     30.0%
Greedy Exit Threshold:       5.00
EarningsMax Exit Threshold:  7.50

Trigger Conditions:
  • Performance (Low):  avg < 3.0  → Switch to Greedy
  • Performance (High): avg > 10.0 → Switch to EarningsMax
  • Stagnation:         70% within ±5% of avg → Explore
    - Lazy driver:    100% explore
    - Active driver:  30% explore

Mutation Reason Breakdown:
  • Low Earnings (< 3.0):           45  ( 15.0%)
  • High Earnings (> 10.0):         30  ( 10.0%)
  • Exit Greedy (>= 5.0):           20  (  6.7%)
  • Exit EarningsMax (< 7.5):       15  (  5.0%)
  • Stagnation Exploration:        190  ( 63.3%)
```

---

## Validation

✅ All `behaviour_stagnation` references updated to `behaviour_stability`
✅ New `earnings_stagnation_events` tracking implemented
✅ Mutation reason breakdown added and displayed
✅ Obsolete attributes (`window`, `stagnation_window`) removed from display
✅ Correct attributes (`greedy_exit_threshold`, `earnings_max_exit_threshold`) now displayed
✅ Report window titles updated
✅ All references to "stagnation" updated to "earnings stagnation" for clarity
✅ Metrics summary text updated

---

## Impact on Reports

The report windows will now:
1. Show accurate breakdown of why mutations occur (5 types with percentages)
2. Track actual earnings stagnation separately from behaviour stability
3. Display correct mutation rule configuration with no missing attributes
4. Provide clearer insight into system behaviour through better terminology

