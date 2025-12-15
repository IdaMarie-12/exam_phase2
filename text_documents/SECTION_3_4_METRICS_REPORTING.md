# 3.4 Metrics and Reporting System

## 3.4.1 Overview

The metrics and reporting system provides comprehensive observation and visualization of simulation behavior across four dimensions: system efficiency, behavior dynamics, mutation analysis, and policy performance. Rather than a separate post-processing step, metrics collection is tightly integrated into the simulation's execution flow, recording observations at each tick alongside the core simulation logic.

### Key Design Principles

1. **Integrated Recording**: Metrics are captured within the simulation tick cycle, ensuring real-time observation of all state changes
2. **Reason Normalization**: Mutation reasons are translated from implementation-specific class names to user-friendly categories for clearer analysis
3. **Cumulative Tracking**: Historical snapshots are maintained for all metrics, enabling temporal analysis and trend visualization
4. **Separation of Concerns**: Simulation logic (phases 1-8) remains isolated from observation logic (metrics recording), improving maintainability and extensibility

### Design Rationale: Why Track Through SimulationTimeSeries, Mutations, and Behaviors Separately?

The metrics system maintains three distinct tracking mechanisms despite their logical interdependence. This design choice is intentional and serves several architectural purposes:

#### 1. **Isolation of Responsibilities**

Each component has a single, well-defined purpose:
- **Mutations**: The `HybridMutation` class records *what happened* (driver changed behavior, reason why)
- **Behaviors**: Driver behavior changes are recorded as state transitions, not as metrics
- **SimulationTimeSeries**: Observes and aggregates *how the system responded* to those changes

This separation prevents the mutation system from having knowledge of or dependencies on the metrics system. If metrics collection needs to change (e.g., adding new visualization windows), mutation logic remains untouched.

#### 2. **Temporal Ordering and Consistency**

The sequential nature of the three tracking systems ensures data consistency:

```
Tick N execution:
1. Simulation logic runs (phases 1-7)
2. Mutations occur (phase 8) → mutation_history is written
3. Metrics collection (record_tick) → reads from mutation_history
```

If mutations and metrics were tracked in the same component, there would be risk of:
- Recording mutations before they fully execute
- Mixing mutation side effects with observation side effects
- Race conditions in multi-threaded contexts

By keeping them separate, we enforce a clear "write-then-read" contract that guarantees correctness.

#### 3. **Independent Scalability and Extensibility**

Separate tracking allows each component to scale independently:

- **Adding new mutations**: Simply extend the `HybridMutation.maybe_mutate()` logic and append to `mutation_history`. No changes to metrics collection needed.
- **Adding new metrics**: Extend `record_tick()` and add time-series lists. Mutation logic is unaffected.
- **Adding new visualizations**: Query the already-collected metrics data. No impact on simulation or mutation systems.

For example, if future research requires tracking individual driver mutation sequences, this could be added to `mutation_history` without affecting the aggregated `mutation_reason_counts` that `SimulationTimeSeries` maintains.

#### 4. **Domain Separation: Physics vs. Observation**

There's a conceptual distinction between the two domains:

- **Simulation Domain** (Mutations + Behaviors): "This is what the driver agents are doing and why"
  - Concerns: Rule correctness, behavior transitions, decision logic
  - Ownership: `HybridMutation`, `Behavior` classes
  
- **Observation Domain** (SimulationTimeSeries): "This is how the system as a whole is performing"
  - Concerns: Aggregation, normalization, visualization preparation
  - Ownership: `SimulationTimeSeries` class

Conflating these domains would create a system that is simultaneously a simulation engine and an analytics engine—mixing concerns in ways that make testing, debugging, and future maintenance harder.

#### 5. **Testing and Validation Clarity**

Separate tracking simplifies testing:

```python
# Test mutation logic in isolation
def test_mutation_triggers():
    # Verify mutations occur for the right reasons
    assert mutation_history[-1]['reason'] == 'performance_low_earnings'

# Test metrics collection in isolation  
def test_metrics_normalization():
    # Verify reasons are normalized correctly
    assert 'low_earnings' in normalized_reasons
    assert 'performance_low_earnings' not in normalized_reasons

# Test integration
def test_simulation_metrics_integration():
    # Verify full pipeline works end-to-end
    summary = ts.get_final_summary()
    assert summary['total_mutations'] > 0
```

If tracking were unified, these separate test concerns would be harder to isolate and verify.

#### 6. **Data Representation Differences**

Each tracking system represents data in the most appropriate format for its purpose:

- **Mutation History** (raw list): `[{reason: "exit_greedydistancebehaviour", driver_id: 5}, ...]`
  - Format: Detailed, unprocessed, preserves full context
  - Why: Enables mutation-specific analysis (e.g., "which drivers mutated to behavior X?")

- **Mutation Reasons** (normalized cumulative): `{tick: {exit_greedy: 12, low_earnings: 5, ...}}`
  - Format: Aggregated per-tick, normalized for display
  - Why: Enables temporal visualization without normalization during plotting

Keeping these separate prevents forcing mutation history into a pre-normalized format that would lose detail (driver_id), or forcing metrics into raw format that would require expensive normalization during visualization.

#### 7. **Mutation History as a Resource**

The `mutation_history` list serves as a **public resource** that multiple systems can read:

- `SimulationTimeSeries._track_mutation_reasons()` reads it for aggregation
- Future analysis tools could read it for mutation pattern analysis
- Debugging tools could read it to reconstruct driver decision trees

By not coupling it directly to metrics collection, `mutation_history` becomes a reusable artifact of the simulation that any observer can consume.

#### Counterargument: Why Not Unify?

One might argue: "Why not have mutations directly append to the metrics collections?" This would be simpler in the short term but creates problems:

- **Premature aggregation**: Raw mutation data is lost immediately, preventing later analysis
- **Tight coupling**: Metrics schema changes break mutation logic
- **Normalization timing**: When should class names become display keys? In the mutation system (wrong domain) or metrics system (right domain)?
- **Testing complexity**: Must test mutation correctness and metrics correctness simultaneously rather than independently

The current design accepts a small amount of complexity (three tracking systems instead of one) to gain:
- Clear responsibility boundaries
- Independent testability
- Flexible extensibility
- Correct temporal ordering
- Domain-appropriate representations

## 3.4.2 Recording Architecture

### Execution Flow Integration

The metrics system integrates seamlessly into each simulation tick:

```
Simulation Tick:
├─ Phases 1-7: Core simulation logic
│  ├─ Request matching
│  ├─ Driver assignment
│  └─ Proposal generation
├─ Phase 8: Mutation rule application
│  └─ mutation_history updated with (reason, driver_id, timestamp)
└─ After All Phases: Metrics recording (record_tick)
   ├─ Calculate current metrics (service level, utilization, etc.)
   ├─ Snapshot time-series data
   ├─ Track mutation reasons (normalized)
   └─ Track behavior distribution
```

### Three-Tier Data Tracking System

The system tracks data across three distinct levels, each with specific responsibilities and formats:

#### Tier 1: Mutation Tracking (Raw Data Collection)

**Location**: `HybridMutation` class in `phase2/mutation.py`

**Data Structure**: 
```python
mutation_history: List[Dict] = [
    {
        'reason': 'exit_greedydistancebehaviour',  # Full class name
        'driver_id': 42,
        'tick': 150,
        'old_behaviour': 'GreedyDistanceBehaviour',
        'new_behaviour': 'EarningsMaxBehaviour',
        'timestamp': 1450
    },
    {
        'reason': 'performance_low_earnings',
        'driver_id': 7,
        'tick': 155,
        'old_behaviour': 'LazyBehaviour',
        'new_behaviour': 'GreedyDistanceBehaviour',
        'timestamp': 1550
    },
    ...
]
```

**What it tracks**: Every individual mutation event with full context
- Raw reason strings (implementation-specific class names)
- Driver identity
- Temporal information (tick, timestamp)
- Behavior transition details (old → new)

**How it's populated**: 
- `HybridMutation.maybe_mutate()` calls `_record_mutation(driver, reason, old_behaviour, new_behaviour)` when a mutation occurs
- Appended immediately during phase 8 of simulation tick

**Purpose**: 
- Serves as the authoritative source of what mutations occurred
- Enables detailed mutation analysis (which drivers mutated, when, why, to what)
- Acts as a resource that any subsystem can query

**Characteristics**:
- Detailed (preserves full context)
- Unprocessed (raw class names, not normalized)
- Event-oriented (one entry per mutation)
- Immutable (only appended, never modified)

#### Tier 2: SimulationTimeSeries - Behavior Distribution Tracking (Aggregated Snapshots)

**Location**: `SimulationTimeSeries` class in `phase2/helpers_2/metrics_helpers.py`

**Data Structure**: 
```python
behaviour_distribution: List[Dict] = [
    {0: {'GreedyDistanceBehaviour': 40, 'LazyBehaviour': 30, 'EarningsMaxBehaviour': 20, ...}},
    {1: {'GreedyDistanceBehaviour': 39, 'LazyBehaviour': 31, 'EarningsMaxBehaviour': 20, ...}},
    {2: {'GreedyDistanceBehaviour': 38, 'LazyBehaviour': 30, 'EarningsMaxBehaviour': 22, ...}},
    ...
]
```

**What it tracks**: 
- Count of drivers in each behavior type at each tick
- Behavior changes detected through mutation_history

**How it's populated** (within `record_tick(simulation)`) - Single-Pass Approach:

```python
# Read current behavior from each driver object
current_behaviours = {
    driver.id: driver.behaviour.__class__.__name__ 
    for driver in simulation.drivers
}

# Count mutations THIS tick from mutation_history (single source of truth)
mutations_this_tick = sum(1 for entry in mutation_history 
                          if entry.get('tick') == current_tick)

# Get mutation details from mutation_history for this tick
for entry in mutation_history:
    if entry.get('tick') == current_tick:
        driver_id = entry.get('driver_id')
        driver_mutation_freq[driver_id] += 1
        recent_mutations[driver_id] = current_tick

# Snapshot current distribution
behaviour_counts = Counter(current_behaviours.values())
behaviour_distribution.append(dict(behaviour_counts))
```

**Purpose**:
- Provides behavioral state at each tick
- Enables behavior evolution visualization
- Allows tracking of behavior adoption rates
- Uses mutation_history as single source of truth

**Characteristics**:
- Aggregated (one count per behavior type per tick)
- Single-source approach (mutation_history is only source of behavior change truth)
- Temporal (one snapshot per tick)
- Memory efficient (no redundant per-driver state storage)

#### Tier 3: SimulationTimeSeries - Mutation Metrics Tracking (Normalized and Aggregated)

**Location**: `SimulationTimeSeries` class in `phase2/helpers_2/metrics_helpers.py`

**Data Structure**: 
```python
# Time-series (one entry per tick)
times: List[int] = [0, 1, 2, 3, ..., N]
served: List[int] = [0, 5, 12, 19, ..., 5000]
expired: List[int] = [0, 0, 1, 3, ..., 250]

# Mutation reason distribution (normalized from Tier 1)
mutation_reasons: List[Dict] = [
    {'performance_low_earnings': 0, 'performance_high_earnings': 0, 'exit_greedy': 1, 
     'exit_earnings': 0, 'exit_lazy': 0, 'stagnation_exploration': 0},
    {'performance_low_earnings': 0, 'performance_high_earnings': 0, 'exit_greedy': 1, 
     'exit_earnings': 0, 'exit_lazy': 0, 'stagnation_exploration': 1},
    ...
]

# Aggregation data (cumulative)
driver_mutation_freq: Dict[int, int] = {1: 5, 2: 3, 3: 12, ...}
_mutation_reason_counts: Dict[str, int] = {'exit_greedy': 87, 'low_earnings': 45, ...}
```

**What it tracks**:
- Aggregated metrics (served, expired, utilization, efficiency)
- Cumulative mutation reason counts (normalized from class names)
- Per-driver mutation frequency

**How it's populated** (within `record_tick(simulation)`):

1. **Calculate metrics**: 
   ```python
   service_level = (total_served / (total_served + total_expired)) * 100
   utilization = (drivers_in_use / total_drivers) * 100
   avg_age = sum(request_ages) / len(request_ages)
   ```

2. **Snapshot time-series**:
   ```python
   self.times.append(current_tick)
   self.served.append(cumulative_served)
   self.expired.append(cumulative_expired)
   self.service_level.append(service_level_pct)
   self.utilization.append(utilization_pct)
   ```

3. **Track mutations** via `_track_mutation_reasons(simulation)`:
   ```python
   # Read from mutation_history (Tier 1)
   for entry in simulation.mutation_rule.mutation_history:
       reason = entry['reason']  # e.g., 'exit_greedydistancebehaviour'
       
       # Normalize to display key
       if 'performance_low_earnings' in reason:
           self._mutation_reason_counts['performance_low_earnings'] += 1
       elif 'exit_greedy' in reason:
           self._mutation_reason_counts['exit_greedy'] += 1
       # ... handle other reasons
   
   # Snapshot cumulative counts
   self.mutation_reasons.append(self._mutation_reason_counts.copy())
   ```

**Purpose**:
- Provides processed, analysis-ready data for visualization
- Normalizes raw mutation reasons for human interpretation
- Maintains temporal history enabling trend analysis
- Aggregates individual events into meaningful statistics

**Characteristics**:
- Aggregated (combines multiple Tier 1 events)
- Normalized (class names → display keys)
- Temporal (one snapshot per tick, enabling visualization)
- Cumulative (reason counts grow monotonically)

### Data Flow and Relationships

```
Tier 1 (HybridMutation - Raw Events)
└─ mutation_history
   ├─ "exit_greedydistancebehaviour"
   ├─ "performance_low_earnings"
   └─ [raw events with driver_id, timestamps, full context]

Tier 2 (SimulationTimeSeries - Behavioral Snapshots)
├─ behaviour_distribution (reads current driver states)
│  ├─ Tick 0: {GreedyDistanceBehaviour: 40, LazyBehaviour: 30, ...}
│  └─ Tick N: {GreedyDistanceBehaviour: 38, LazyBehaviour: 32, ...}
└─ Used for: Evolution graphs, diversity metrics, adoption rates

Tier 3 (SimulationTimeSeries - Normalized Metrics)
├─ mutation_reasons (reads and normalizes from Tier 1)
│  ├─ Tick 0: {exit_greedy: 1, low_earnings: 0, stagnation: 1, ...}
│  └─ Tick N: {exit_greedy: 87, low_earnings: 45, stagnation: 223, ...}
├─ service_level, utilization, efficiency, etc.
└─ Used for: All visualization windows, trend analysis

Dependency Flow:
Tier 1 (HybridMutation) 
  ↓ (read & normalize)
Tier 3 (SimulationTimeSeries metrics)

Tier 2 (Driver.behaviour current state)
  ↓ (read & aggregate)
Tier 2 (SimulationTimeSeries behaviour_distribution)
```

**Key Insight**: Behaviors are now tracked using a single-pass approach:
- **behaviour_distribution**: Aggregated snapshot of how many drivers are in each behavior (one count per type per tick)
- **mutation_history**: Single source of truth for behavior changes (used to detect which drivers mutated this tick)

This eliminates redundant per-driver state storage while maintaining identical data quality and accuracy.

### Single-Pass Optimization: Implemented

The behavior tracking system has been optimized to use a **single-pass approach**, eliminating the need for redundant state storage:

**Previous Approach (Two-State)**:
```python
# Store current behaviors
current_behaviours = {driver.id: driver.behaviour.__class__.__name__ for driver in drivers}

# Compare with previous state (redundant storage)
if driver_id in self._previous_behaviours:
    if current_behaviours[driver_id] != self._previous_behaviours[driver_id]:
        mutations_this_tick += 1

# Store for next tick
self._previous_behaviours = current_behaviours.copy()  # O(n) memory per tick
```

**Current Approach (Single-Pass)**:
```python
# Get current behaviors
current_behaviours = {driver.id: driver.behaviour.__class__.__name__ for driver in drivers}

# Use mutation_history as single source of truth
mutations_this_tick = sum(1 for entry in mutation_history 
                          if entry.get('tick') == current_tick)

# Extract mutation details directly from mutation_history
for entry in mutation_history:
    if entry.get('tick') == current_tick:
        driver_id = entry.get('driver_id')
        old_behaviour = entry.get('old_behaviour')
        new_behaviour = entry.get('new_behaviour')
        driver_mutation_freq[driver_id] += 1
```

**Benefits Achieved**:
- **Memory**: Eliminated \_previous_behaviours dict (saves O(n) storage per tick)
- **Consistency**: mutation_history becomes the single source of truth
- **Clarity**: Change detection is explicit through mutation_history records
- **Data Quality**: Identical accuracy (no degradation)

**Implementation Details**:
- New method `_count_mutations_this_tick()` queries mutation_history for current tick
- `_track_behaviour_changes()` reads mutation_history entries matching current_tick
- Behavior transition details are preserved from `old_behaviour` and `new_behaviour` fields
- Recent mutations tracking still maintains O(n) in worst case but only for recently mutated drivers (typically sparse)

**Impact**:
For simulations with 100-500 drivers:
- **Memory saved**: ~100-500 integers per tick (negligible in absolute terms but principle improves)
- **Clarity improved**: Single source of truth (mutation_history) rather than dual state
- **Maintainability**: Easier to debug mutation tracking (single point of reference)
- **Correctness guarantee**: Guaranteed consistency between mutations and detected changes

### Core Data Structure: SimulationTimeSeries

The `SimulationTimeSeries` class manages all metrics collection and aggregation:

**Time-Series Lists** (one entry per tick):
- `times`: Simulation time for each tick
- `served`: Cumulative requests served
- `expired`: Cumulative requests expired
- `service_level`: Percentage of served requests
- `utilization`: Average driver utilization
- `pending_requests`: Active unmatched requests
- `avg_request_age`: Mean request waiting time
- `max_request_age`: Maximum request waiting time
- `mutations_per_tick`: Count of mutations in current tick
- `offers_generated`: Count of offers generated
- `matching_efficiency`: Percentage of matched requests
- `rejection_rate`: Percentage of rejected offers

**Distribution Snapshots** (categorical data per tick):
- `behaviour_distribution`: Current distribution of driver behaviors {behavior_type: count}
- `mutation_reasons`: Cumulative counts per mutation reason {reason: total_count}
- `actual_policy_used`: Which sub-policy (NearestNeighbor or GlobalGreedy) was active

**Aggregation Data** (cumulative):
- `driver_mutation_freq`: Frequency map of which drivers have mutated {driver_id: count}
- `policy_names`: Set of all distinct policies observed
- `_mutation_reason_counts`: Internal tracking of reason normalization

## 3.4.3 Mutation Metrics Integration

### Mutation Reason Tracking and Normalization

Mutations are recorded with full class names during the mutation phase. The metrics system normalizes these reasons into user-friendly categories:

| Raw Reason (Class Name) | Normalized Key | Category |
|---|---|---|
| `exit_greedydistancebehaviour` | `exit_greedy` | Exit Condition |
| `exit_earningsmaxbehaviour` | `exit_earnings` | Exit Condition |
| `exit_lazybehaviour` | `exit_lazy` | Exit Condition |
| `performance_low_earnings` | `low_earnings` | Performance-Based |
| `performance_high_earnings` | `high_earnings` | Performance-Based |
| `stagnation_exploration` | `stagnation` | Stagnation Detection |

The normalization occurs within `record_tick()` via `_track_mutation_reasons()`, which:

1. Reads raw mutation history from the mutation rule
2. Counts occurrences of each raw reason string
3. Normalizes class names to display keys
4. Maintains cumulative totals across all ticks
5. Appends normalized snapshot to `mutation_reasons` list

This design keeps mutation logic independent of display concerns while ensuring accurate tracking.

### Cumulative Tracking Structure

Mutation reason counts are cumulative from simulation start:

```
Tick 0: {low_earnings: 0, high_earnings: 0, exit_greedy: 1, ...}
Tick 1: {low_earnings: 0, high_earnings: 0, exit_greedy: 1, ...}
Tick 5: {low_earnings: 2, high_earnings: 1, exit_greedy: 5, ...}
Tick N: {low_earnings: 45, high_earnings: 32, exit_greedy: 87, ...}
```

This cumulative structure enables stacked area visualization showing how mutation patterns evolve across the simulation.

## 3.4.4 Report Window Implementation

### Window 1: System Efficiency (6 plots)

Focuses on overall request handling performance and system load:

1. **Request Evolution**: Served vs. Expired requests over time (line chart)
2. **Service Level %**: Percentage of requests served before timeout (line chart)
3. **Pending Requests**: Number of active unmatched requests (line chart)
4. **Driver Utilization**: Percentage of drivers in use with 100% threshold line (area chart)
5. **Request Age Pressure**: Evolution of max request age with timeout threshold (line chart)
6. **Summary Statistics**: Text box showing min/max/avg values for all metrics

**Key Insights**: Service degradation, bottleneck identification, request aging patterns

### Window 2: Behavior Dynamics (4 plots)

Analyzes how driver behavior evolves through the simulation:

1. **Behavior Distribution Evolution**: Stacked area showing composition over time
2. **Final Distribution**: Pie chart of behavior distribution at simulation end
3. **All Behavior Types**: Bar chart showing cumulative driver counts per behavior
4. **Behavior Statistics**: Text box with transition counts and distribution details

**Key Insights**: Behavior adoption rates, convergence patterns, policy effectiveness

### Window 3: Mutation Analysis (3 plots)

Tracks root causes of driver behavior changes:

1. **Cumulative Mutations**: Total mutations over time (line chart)
2. **Mutation Reasons**: Stacked area showing cumulative count per reason type
3. **Driver Mutation Frequency**: Histogram showing distribution of mutation counts across drivers

**Key Insights**: Which reasons trigger most mutations, which drivers mutate most frequently, mutation rates over time

### Window 4: Policy and Offers (5 plots)

Examines matching quality and policy behavior:

1. **Offers Generated**: Count of proposals per tick (line chart)
2. **Matching Efficiency**: Percentage of requests that receive offers (line chart)
3. **Offer Quality**: Average reward-to-time ratio of generated offers (line chart)
4. **Rejection Rate**: Percentage of offers rejected by drivers (line chart)
5. **Policy Adoption**: Cumulative stacked area showing which sub-policy is active each tick

**Key Insights**: Matching algorithm performance, offer quality trends, policy selection patterns

### Summary Statistics Integration

Each window includes a text-based summary showing:
- Minimum, maximum, and average values for all plotted metrics
- Statistical measures (variance for utilization, total counts)
- Policy and behavior distribution snapshots

## 3.4.5 Data Flow and Dependencies

The complete metrics pipeline maintains clear data dependencies:

1. **Simulation writes** mutation history during phase 8
2. **record_tick()** is called after all phases complete
   - Reads current simulation state
   - Reads mutation history (for normalization)
   - Appends snapshots to all time-series lists
   - Normalizes mutation reasons
   - Tracks behavior distribution
3. **get_final_summary()** aggregates all accumulated data
   - Compiles 30+ summary statistics
   - Calculates derived metrics (variance, frequencies)
   - Prepares data for reporting
4. **generate_report()** creates visualizations
   - Accesses finalized SimulationTimeSeries
   - Creates 4 windows with 18+ plots
   - Renders all graphics

This linear pipeline ensures data consistency: mutations are recorded before metrics are collected, and all processing happens before visualization.

## 3.4.6 No-Data Handling

The system gracefully handles edge cases:

- **Empty metrics**: Plotting functions check for None or empty lists and display "No data recorded" message
- **Single tick**: Time-series plots adjust to show point or minimal line
- **No mutations**: Mutation windows display zero counts without errors
- **Inactive policies**: Missing policies are omitted from visualization with appropriate messaging

## 3.4.7 Performance Considerations

- **Memory**: Metrics are appended once per tick; no per-request overhead
- **Computation**: Summary generation is O(n) where n is number of ticks; happens once at end
- **Visualization**: Matplotlib rendering is the primary time cost; occurs after simulation completes
- **Storage**: For 10,000-tick simulations with ~100 drivers, total metrics storage is ~5 MB

## 3.4.8 Testing and Validation

All metrics functionality is covered by unit tests:
- `test_metrics.py`: Metrics collection, normalization, and aggregation
- `test_report_window.py`: Plotting functions and window generation
- `test_simulation.py`: Integration tests verifying metrics are recorded during simulation

Tests validate:
- Correct cumulative tracking of all metrics
- Proper mutation reason normalization
- Accurate calculation of derived statistics
- Graceful handling of missing data
- Visual rendering without errors

## 3.4.9 Extension Points

The architecture supports future enhancements:

1. **Additional Metrics**: Add new time-series lists to `SimulationTimeSeries.__init__()` and populate in `record_tick()`
2. **New Visualizations**: Implement new plotting functions following the `_plot_*` pattern
3. **Custom Aggregations**: Extend `get_final_summary()` with domain-specific calculations
4. **Export Formats**: Add methods to export metrics to CSV, JSON, or database formats
5. **Real-Time Monitoring**: Stream metrics during simulation for live dashboards

