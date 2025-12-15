# Mutation Metrics Fix - Issue Resolution

## Problem
User reported: "When I run and look at the metrics there is no mutation data regarding mutation."

Mutation data was not appearing in the UI metrics display despite the mutation system working correctly internally.

## Root Cause Analysis

### Symptom Discovery
- Mutation history WAS being populated correctly (mutations recorded during simulation)
- But `mutations_per_tick` array was always zeros
- The mutation detection in metrics was failing silently

### Timing Issue Found
The issue was a **time synchronization bug** between when mutations are recorded and when metrics are collected:

1. **During Tick (Phase 8):** `HybridMutation.maybe_mutate()` records mutations with:
   ```python
   entry['time'] = simulation.time  # e.g., time=37
   ```

2. **End of Tick (Phase 9):** Simulation increments time:
   ```python
   self.time += 1  # Now time=38
   ```

3. **After Tick:** `SimulationTimeSeries.record_tick()` is called AFTER time increment
   - Looking for mutations at the CURRENT time (38)
   - But mutations were recorded at PREVIOUS time (37)
   - Result: No mutations found! ❌

### Verification
Debug traces confirmed:
- Mutation recorded: `{'time': 37, 'driver_id': 0, ...}`
- Metrics checking: `_count_mutations_this_tick(history, simulation.time=38)`
- Searching for: entries where `entry['time'] == 38`
- Found: None ❌

## Solution Implemented

### Fix in `phase2/helpers_2/metrics_helpers.py`

Changed the mutation counting to look at the correct time:

```python
# OLD (WRONG):
mutations_this_tick = self._count_mutations_this_tick(
    simulation.mutation_rule.mutation_history,
    simulation.time  # ❌ Already incremented!
)

# NEW (CORRECT):
mutations_this_tick = self._count_mutations_this_tick(
    simulation.mutation_rule.mutation_history,
    simulation.time - 1  # ✓ Time when the tick actually occurred
)
```

Also updated the recent mutations filter to use the correct time:

```python
# OLD (WRONG):
current_tick_mutations = [entry for entry in ... if entry.get('time') == simulation.time]

# NEW (CORRECT):
current_tick_mutations = [entry for entry in ... if entry.get('time') == simulation.time - 1]
```

### Test Update

Updated `test/test_metrics.py::test_mutation_detection` to match the new timing:
- Records mutations at `time - 1` to simulate real tick behavior
- Verifies metrics correctly detect mutations from the previous tick

## Verification

### Results
✓ All 427 tests passing
✓ Mutations now appear in `mutations_per_tick` array
✓ Mutation reasons tracked correctly
✓ Behavior distribution transitions visible
✓ UI metrics will now display mutation data

### Integration Test Results
- 100-tick simulation: 1 mutation detected
- Tick 37: LazyBehaviour → EarningsMaxBehaviour (performance_high_earnings)
- Mutations in `mutation_history`: 1 ✓
- Mutations in metrics: 1 ✓
- Counts match: ✓

## Impact
- Users will now see mutation data in metrics/reports
- Mutation plots will display correctly in report windows
- Mutation reasons breakdown will populate
- Full mutation analytics now functional
