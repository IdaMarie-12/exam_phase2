# IDA's Contribution Points: Paper References Guide

This document maps your (IDA) contributions to relevant sections in the appendices and provides writing guidance for each.

---

## **3.2.4 Mutation of Driver Behavior (IDA)**

### What to Cover

1. **HybridMutation Strategy Overview**
   - Explain why drivers need to adapt behaviour over time
   - Describe the three adaptation mechanisms: performance-based switching, stagnation detection, exploration

2. **Thresholds and Decision Logic**
   - Low earnings threshold (3.0) → switch to GREEDY
   - High earnings threshold (10.0) → switch to EARNINGS_MAX
   - Cooldown period (10 ticks) prevents mutation churn
   - Stagnation window (8 ticks) triggers exploration (30% probability)

3. **Implementation Details**
   - Show how `MutationRule.maybe_mutate()` is called each tick
   - Explain the earning history tracking in `driver.history`
   - Performance-based decision: average of last N trips

4. **Behavioral Adaptation Example**
   - Walk through a concrete scenario:
     - Driver starts as LAZY (selective, high standards)
     - Earnings drop → switches to GREEDY (accepts most jobs)
     - On recovery, switches to EARNINGS_MAX (efficient jobs only)

### Relevant Appendix References

**Appendix E.3: Mutation Rule Parameters**
- All 5 configuration constants with their values and rationale
- Table E.3.1 shows exact thresholds (HYBRID_LOW_EARNINGS_THRESHOLD = 3.0, etc.)
- Table E.3.2 shows which behaviour is created during mutation

**Appendix A.2: Policy and Mutation Classes**
- UML showing HybridMutation inheriting from MutationRule
- Helper diagram showing how mutation fits into simulation

**Appendix D.2.8: test_mutation.py**
- 60 tests validating mutation logic
- Example test cases: `test_hybrid_mutation_low_earnings_trigger()`, `test_hybrid_mutation_stagnation_detection()`

### Suggested Text Structure

> **3.2.4 Mutation of Driver Behavior (IDA)**
>
> To model realistic driver adaptation, drivers can change their behaviour policy during simulation based on performance. This implements the biological concept of selection pressure: struggling drivers become less selective, while high earners become picky.
>
> Our implementation uses a **HybridMutation** rule combining three strategies:
>
> 1. **Performance-Based Switching:** If average earnings in the last 8 ticks fall below 3.0, the driver switches to GreedyDistanceBehaviour (accept more work). If earnings exceed 10.0, switch to EarningsMaxBehaviour (optimize efficiency).
>
> 2. **Cooldown Mechanism:** To prevent constant behaviour switching (churn), each driver can mutate at most once per 10 ticks, ensuring stability while allowing adaptation.
>
> 3. **Stagnation-Based Exploration:** If earnings plateau, there's a 30% probability the driver explores a different behaviour, helping escape local optima.
>
> See Appendix E.3 for all configuration parameters and Appendix D.2.8 for test coverage.

---

## **3.3 Integration with the UI (IDA)**

### What to Cover

1. **Adapter Pattern Design**
   - Explain how the OO simulation is exposed through a procedural interface
   - Why this design bridges two worlds: OO backend vs. functional UI expectations

2. **Adapter Functions**
   - `init_simulation()`: Initialize DeliverySimulation with drivers, policies, etc.
   - `step_simulation()`: Advance one tick, return state snapshot
   - `get_plot_data()`: Extract positions for rendering

3. **Data Contract**
   - `get_snapshot()` returns JSON-serializable dict with:
     - Driver positions and current targets
     - Pickup/dropoff locations (by request status)
     - Global statistics (served, expired, avg_wait)

4. **State Management**
   - How simulation state persists across multiple UI calls
   - Stateless snapshots vs. stateful simulation instance

### Relevant Appendix References

**Appendix A.1 & A.6: Core Classes and Data Flow**
- Diagram showing how DeliverySimulation interfaces with external systems
- `get_snapshot()` output structure documented in flow diagram

**Not directly referenced:** No specific test file for UI adapter (it's tested via integration)
- But see Appendix D.2.9: test_simulation.py includes snapshot tests

### Suggested Text Structure

> **3.3 Integration with the UI (IDA)**
>
> The OO simulation engine is exposed to the GUI through a thin **adapter layer** implementing the same procedural interface as Part I. This design allows the sophisticated internal object-oriented architecture to coexist with the simple functional API the UI expects.
>
> The adapter manages three key responsibilities:
>
> 1. **Initialization:** Create driver objects, instantiate policies and generators, and initialize the DeliverySimulation instance from simple parameters.
>
> 2. **State Snapshots:** After each `tick()`, extract a JSON-serializable snapshot containing driver positions, request locations, and statistics. This snapshot is immutable from the UI's perspective—all state lives in the simulation.
>
> 3. **Lifecycle Management:** Maintain the simulation instance across multiple calls, accumulating statistics and history.
>
> The snapshot format (Appendix A.6) includes:
> - Driver IDs, positions, statuses, current request assignments
> - Pickup and dropoff locations for requests by status
> - Global counters: served, expired, average wait time

---

## **3.4 Metrics and Reporting (IDA)**

### What to Cover

1. **Time-Series Tracking**
   - `SimulationTimeSeries` class records 9 metrics per tick
   - Metrics: served, expired, avg_wait, pending, utilization, behaviour_distribution, mutations, stagnation

2. **Three-Window Reporting System**
   - **Metrics Window:** Served vs. Expired (cumulative), wait time trend, pending requests, driver utilization
   - **Behaviour Window:** Current behaviour distribution (bar chart), behaviour evolution (stacked area)
   - **Mutation Window:** Mutation rule configuration, impact metrics, mutations over time

3. **Post-Simulation Analysis**
   - After GUI closes, automatically generate matplotlib figures
   - Data export capability for external analysis (R, Excel, Python notebooks)

4. **Metrics Calculation**
   - Service level = served / (served + expired) * 100%
   - Driver utilization = (# busy drivers) / (# total drivers) * 100%
   - Average wait = sum of all wait times / # delivered requests

### Relevant Appendix References

**Appendix E.6: Metrics and Reporting Constants**
- PLOT_COLOURS palette for consistency
- Figure sizes for three windows (16×13, 16×14, 16×12)

**Appendix E.6.2: SimulationTimeSeries Metrics**
- List of 9 tracked metrics with types
- Example calculation formulas

**Appendix D.2.11: test_metrics.py**
- 28 tests validating time-series tracking
- Example: `test_record_tick_captures_all_metrics()`, `test_behaviour_distribution_tracking()`

**Appendix D.2.12: test_report_window.py**
- 29 tests for report generation
- Validates all three windows, plot data handling, edge cases

### Suggested Text Structure

> **3.4 Metrics and Reporting (IDA)**
>
> To support post-simulation analysis and policy comparison, the system records detailed metrics throughout execution and generates three interactive visualization windows when the GUI closes.
>
> **Time-Series Tracking**
>
> A `SimulationTimeSeries` object captures 9 metrics at each timestep (see Appendix E.6.2):
> - Cumulative requests served and expired
> - Current average wait time
> - Pending (undelivered) request count
> - Driver utilization percentage
> - Distribution of behaviours across fleet
> - Cumulative mutation count
> - Number of drivers in stagnant state
>
> **Post-Simulation Reporting**
>
> Upon GUI closure, three matplotlib windows display:
>
> 1. **Metrics Report (Figure 1):** Five subplots showing request fulfillment evolution, wait time trends, system load, and driver engagement.
>
> 2. **Behaviour Analysis (Figure 2):** Current behaviour distribution and how behaviours changed over time (stacked area chart), revealing fleet adaptation patterns.
>
> 3. **Mutation Analysis (Figure 3):** Mutation rule configuration, impact metrics (how many drivers mutated, when), and stagnation patterns.
>
> This post-simulation analysis enables policy comparison and system tuning. See Appendix E.6 for visualization parameters and Appendix D.2.11–D.2.12 for comprehensive test coverage.

---

## **Test Coverage for IDA Sections**

### Mutation Testing (Section 3.2.4)
- **File:** Appendix D.2.8 (test_mutation.py)
- **Key Tests:**
  - `test_hybrid_mutation_low_earnings_trigger()`: Verifies LOW threshold (3.0)
  - `test_hybrid_mutation_high_earnings_trigger()`: Verifies HIGH threshold (10.0)
  - `test_hybrid_mutation_stagnation_detection()`: Tests 8-tick window
  - `test_hybrid_mutation_exploration_switch()`: Tests 30% probability
  - `test_hybrid_mutation_cooldown_enforcement()`: Tests 10-tick cooldown
  - **Coverage:** 60 tests validating all mutation scenarios

### Simulation Integration (Section 3.3)
- **File:** Appendix D.2.9 (test_simulation.py)
- **Key Tests:**
  - `test_snapshot_format_and_keys()`: Validates snapshot structure
  - `test_snapshot_json_serializable()`: Ensures adapter output is JSON-compatible
  - `test_snapshot_with_assigned_requests()`: Tests request state in snapshot
  - **Coverage:** 150 tests including snapshot validation

### Metrics and Reporting (Section 3.4)
- **File:** Appendix D.2.11 (test_metrics.py)
- **Key Tests:**
  - `test_timeseries_initialization()`: Initialize metrics tracking
  - `test_record_tick_captures_all_metrics()`: All 9 metrics captured
  - `test_behaviour_distribution_tracking()`: Behaviour counting
  - `test_mutation_counting()`: Cumulative mutations tracked
  - **Coverage:** 28 tests

- **File:** Appendix D.2.12 (test_report_window.py)
- **Key Tests:**
  - `test_generate_report_creates_figures()`: All 3 windows generated
  - `test_metrics_window_plots_served_vs_expired()`: Figure 1 plots
  - `test_behaviour_window_shows_distribution()`: Figure 2 plots
  - `test_mutation_window_shows_rule_info()`: Figure 3 plots
  - **Coverage:** 29 tests

---

## **Quick Reference Table**

| Your Section | Key Concept | Appendix | Key Values |
|---|---|---|---|
| 3.2.4 Mutation | HybridMutation thresholds | E.3, D.2.8 | low=3.0, high=10.0, cooldown=10, window=8, explore=30% |
| 3.3 UI Integration | Adapter + Snapshot | A.1, A.6, D.2.9 | `get_snapshot()` returns JSON dict with drivers, requests, stats |
| 3.4 Metrics | 9 metrics tracked | E.6.2, D.2.11, D.2.12 | served, expired, avg_wait, pending, utilization, behaviour_dist, mutations, stagnation, times |

---

## **Writing Tips for Your Sections**

### For 3.2.4 (Mutation)
- Start with **why**: Real drivers adapt; model this with behaviour switching
- Then **what**: Describe the three mechanisms (performance, cooldown, exploration)
- Then **how**: Explain the thresholds and algorithm
- End with **example**: Walk through a concrete scenario of a driver's behaviour evolution
- **Length:** 0.5–1 page with code snippet showing decision logic

### For 3.3 (UI Integration)
- Explain the **adapter pattern**: Bridge between OO engine and procedural interface
- Describe the **contract**: What functions does adapter provide? What do they return?
- Show the **snapshot format**: JSON structure with example
- Mention **state management**: Why simulation state persists across calls
- **Length:** 0.3–0.5 page (brief section)

### For 3.4 (Metrics)
- Explain **why**: Need post-simulation analysis to compare policies
- Describe **what**: Three windows, nine metrics, time-series tracking
- Show **how**: How metrics are calculated (e.g., service_level = served / total)
- Visualize: Include screenshot or sketch of one report window
- Mention **capabilities**: Export data, compare policies, identify trends
- **Length:** 0.5–1 page with visualization

---

## **Summary**

- **3.2.4 Mutation:** See Appendix E.3 (parameters), D.2.8 (tests)
- **3.3 UI Integration:** See Appendix A.1/A.6 (architecture), D.2.9 (snapshot tests)
- **3.4 Metrics:** See Appendix E.6 (parameters), D.2.11 (time-series tests), D.2.12 (report tests)

All referenced sections in the appendices contain concrete details, code examples, and test coverage summaries to support your writing.
