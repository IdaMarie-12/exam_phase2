# 3.4 Metrics and Reporting: Data Collection, Handling, and Visualization

## 3.4.1 Overview

The metrics and reporting system captures simulation state at each tick and aggregates it into time-series data structures for post-simulation analysis. This enables comprehensive visualization of system behavior including mutation dynamics, driver adaptation patterns, and dispatch efficiency.

## 3.4.2 Data Collection Architecture

### 3.4.2.1 Collection Flow

The data collection follows a clear pipeline:

```
Simulation Tick (9 phases)
    ↓
Phase 8: Mutations recorded in mutation_history
    ↓
Phase 9: Time incremented
    ↓
After Tick: SimulationTimeSeries.record_tick() called
    ↓
Extract & Aggregate Current State
    ↓
Store in Time-Series Arrays
```

### 3.4.2.2 Data Sources

Data is collected from three primary sources during each tick:

**1. Simulation State (DeliverySimulation)**
- `time`: Current simulation tick
- `served_count`: Cumulative requests completed
- `expired_count`: Cumulative requests expired due to timeout
- `avg_wait`: Average wait time for completed requests
- `drivers`: List of driver objects with current status and behavior
- `requests`: List of all requests in system
- `offer_history`: Historical record of all generated offers
- `mutation_rule.mutation_history`: Detailed mutation records

**2. Driver State (per driver)**
- `id`: Driver identifier
- `status`: Current status (IDLE, TO_PICKUP, TO_DROPOFF, ASSIGNED)
- `behaviour`: Current behavior object (GreedyDistanceBehaviour, EarningsMaxBehaviour, LazyBehaviour)
- `history`: Trip completion records with fare and wait time
- `earnings`: Cumulative driver earnings

**3. Request State (per request)**
- `id`: Request identifier
- `status`: Request status (WAITING, ASSIGNED, PICKED, DELIVERED, EXPIRED)
- `creation_time`: When request entered system
- `pickup`: Pickup location (Point object)
- `dropoff`: Dropoff location (Point object)
- `wait_time`: Time customer waited for pickup

## 3.4.3 SimulationTimeSeries: Core Data Structure

### 3.4.3.1 Purpose

The `SimulationTimeSeries` class accumulates metrics across all simulation ticks into parallel arrays, enabling time-series analysis and plotting.

### 3.4.3.2 Data Categories Tracked

#### System Performance Metrics
```python
times[]                    # Simulation ticks
served[]                   # Cumulative requests served
expired[]                  # Cumulative requests expired
avg_wait[]                 # Average wait time per tick
service_level[]            # % served / (served + expired)
utilization[]              # % of drivers actively busy
```

#### Mutation Tracking
```python
mutations_per_tick[]       # Count of mutations each tick
mutation_rate[]            # 10-tick rolling average mutation rate
stable_ratio[]             # % of drivers without recent mutation
driver_mutation_freq{}     # Per-driver mutation counts
mutation_reasons[]         # Breakdown of mutation causes (6 types)
```

#### Behavior Dynamics
```python
behaviour_distribution[]   # Distribution of behavior types per tick
                          # Example: {'LazyBehaviour': 2, 'GreedyDistanceBehaviour': 1, ...}
```

#### Request Queue Dynamics
```python
pending_requests[]         # Number of waiting requests per tick
max_request_age[]          # Age of oldest waiting request
avg_request_age[]          # Average age of waiting requests
rejection_rate[]           # % of offers drivers reject
```

#### Dispatch Efficiency
```python
offers_generated[]         # Number of offers created per tick
offer_acceptance_rate[]    # % of offers that became assignments
matching_efficiency[]      # % of offers that became assignments
conflict_count[]           # Offers competing for same request
```

#### Policy Effectiveness
```python
policy_distribution[]      # Drivers assigned to each policy
avg_offer_quality[]        # Average reward/time ratio
actual_policy_used[]       # Which policy executed each tick
```

### 3.4.3.3 Mutation Data Collection Details

#### Mutation History Structure

Each mutation is recorded with:
```python
{
    'time': int,               # Simulation tick when mutation occurred
    'driver_id': int,          # ID of mutated driver
    'from_behaviour': str,     # Previous behaviour class name
    'to_behaviour': str,       # New behaviour class name
    'reason': str,             # Mutation trigger reason
    'avg_fare': float          # Driver's average fare at mutation time
}
```

#### Mutation Reason Categories (6 Types)

The system tracks six distinct mutation triggers:

1. **performance_low_earnings** - Driver struggling (avg < 3.0) switches to Greedy
2. **performance_high_earnings** - Driver thriving (avg > 10.0) switches to EarningsMax
3. **exit_greedy** - Greedy driver recovered (avg ≥ 5.0) resets to Lazy
4. **exit_earnings** - EarningsMax driver declined (avg < 7.5) resets to Lazy
5. **exit_lazy** - Lazy driver exits (unused - Lazy has no exit condition)
6. **stagnation_exploration** - Stagnated driver explores other strategies

#### Critical Timing Fix

**Issue:** Mutations recorded during phase 8 at `time=T`, but time incremented in phase 9 to `T+1`. When `record_tick()` called after tick, it was looking for mutations at wrong time.

**Solution:** Metrics system searches for mutations at `simulation.time - 1` to match the tick that just completed.

```python
# Correct approach in _track_behaviour_changes():
mutations_this_tick = self._count_mutations_this_tick(
    simulation.mutation_rule.mutation_history,
    simulation.time - 1  # Look at previous tick (which just finished)
)
```

## 3.4.4 Mutation Analysis Pipeline

### 3.4.4.1 Per-Tick Mutation Detection

For each simulation tick, the system:

1. **Extract current behavior snapshot** for all drivers
2. **Query mutation_history** for entries with `time == simulation.time - 1`
3. **Count mutations** this tick
4. **Build transition map** (e.g., "LazyBehaviour→GreedyDistanceBehaviour": 2)
5. **Track driver frequency** - how many times each driver has mutated
6. **Update reason breakdown** - tally which mutation reason triggered
7. **Calculate stability ratio** - % of drivers without recent mutations (last 5 ticks)

### 3.4.4.2 Mutation Rate Calculation

A 10-tick rolling window tracks mutation sustainability:

```python
mutation_rate = sum(mutations_per_tick[-10:]) / 10.0
```

This represents the average mutations per tick over the last 10 ticks, accounting for cooldown periods.

### 3.4.4.3 Behavior Stability Tracking

For each tick, the system calculates:

```python
stable_drivers = total_drivers - drivers_with_recent_mutations
stable_ratio = (stable_drivers / total_drivers) * 100%
```

A driver is marked as "recently mutated" if they mutated in the last 5 ticks. This indicates how many drivers have settled into stable strategies.

## 3.4.5 Behavior Distribution Tracking

### 3.4.5.1 Snapshot Recording

At each tick, behavior distribution is captured:

```python
behaviour_distribution.append({
    'LazyBehaviour': 2,
    'GreedyDistanceBehaviour': 1,
    'EarningsMaxBehaviour': 0
})
```

This enables visualization of:
- **Adaptation over time** - how behavior populations change
- **Strategy adoption** - which strategies become dominant
- **Convergence patterns** - if system reaches stable state

### 3.4.5.2 Behavior-Performance Correlation

The system tracks earnings by behavior type:

```python
earnings_by_behaviour['GreedyDistanceBehaviour'].append(avg_earnings)
earnings_by_behaviour['EarningsMaxBehaviour'].append(avg_earnings)
earnings_by_behaviour['LazyBehaviour'].append(avg_earnings)
```

This allows analysis of which strategies actually perform best in practice.

## 3.4.6 System Efficiency Metrics

### 3.4.6.1 Service Level

```python
service_level = (served_count / (served_count + expired_count)) * 100
```

Indicates what percentage of requests are successfully completed vs. timing out.

### 3.4.6.2 Driver Utilization

```python
busy_drivers = count(d.status != 'IDLE' for d in drivers)
utilization = (busy_drivers / total_drivers) * 100
```

Shows what percentage of drivers are actively working at any point.

### 3.4.6.3 Request Queue Health

- **pending_requests**: How many customers are waiting at each moment
- **max_request_age**: Longest any customer has waited (timeout indicator)
- **avg_request_age**: Average customer wait (QoS indicator)

## 3.4.7 Dispatch Efficiency Analysis

### 3.4.7.1 Offer Generation and Acceptance

```python
offers_generated = len(offers_this_tick)
offers_accepted = len(assignments)
offer_acceptance_rate = (offers_accepted / offers_generated) * 100
```

Shows how selective drivers are and whether strategy is working.

### 3.4.7.2 Matching Efficiency

```python
matching_efficiency = (successful_matches / total_offers) * 100
```

Indicates how well the dispatch policy is at creating successful matches.

### 3.4.7.3 Conflict Detection

Tracks when multiple offers compete for the same request - a sign of inefficiency in the dispatch policy.

## 3.4.8 Post-Simulation Report Generation

### 3.4.8.1 Four Report Windows

The system generates four specialized matplotlib windows:

#### Window 1: System Efficiency
- Service level over time
- Driver utilization trends
- Average wait time
- Served vs. expired requests
- Served to expired ratio (KPI)

#### Window 2: Behavior Dynamics
- Behavior distribution over time (stacked area chart)
- Behavior-specific earnings comparison
- Stable ratio evolution
- Mutation rate (10-tick rolling average)

#### Window 3: Mutation Analysis
- Cumulative mutations over time
- Mutation reasons breakdown (stacked area)
- Driver mutation frequency distribution
- Which drivers are most adaptive

#### Window 4: Policy & Offer Effectiveness
- Offers generated per tick
- Offer acceptance rate
- Policy distribution across drivers
- Matching efficiency trends

### 3.4.8.2 Plot Types Used

**Time-Series Line Plots**
```python
ax.plot(times, data, linewidth=2.5, marker='o', markersize=3)
```
Used for: service_level, utilization, avg_wait, mutation_rate

**Stacked Area Charts**
```python
ax.stackplot(times, *data_series, labels=labels, alpha=0.75)
```
Used for: behavior_distribution, mutation_reasons (shows composition)

**Bar Charts**
```python
ax.bar(driver_ids, mutation_counts)
```
Used for: driver_mutation_frequency (shows distribution)

**Filled Area Charts**
```python
ax.fill_between(times, data, alpha=0.2)
```
Used for cumulative trends

## 3.4.9 Data Aggregation Intervals

### Per-Tick Collection (Every Simulation Tick)
- Current time
- Served/expired counts
- Wait times
- Behavior distribution
- Active mutations
- Queue statistics

### Post-Simulation Processing
- Cumulative statistics
- Behavior change transitions
- Performance summaries
- Mutation pattern analysis

## 3.4.10 Key Metrics for Thesis Analysis

### Mutation System Effectiveness
1. **Total mutations** - How adaptive are drivers?
2. **Mutation rate stability** - Is 10-tick cooldown effective?
3. **Reasons distribution** - Which conditions trigger adaptation?
4. **Stable ratio growth** - Do drivers settle into strategies?

### Behavior Adaptation Success
1. **Behavior distribution evolution** - Which strategies dominate?
2. **Performance by behavior** - Do mutations improve earnings?
3. **Convergence patterns** - Does system reach equilibrium?
4. **Transition frequency** - How often do strategies change?

### System-Level Performance
1. **Service level** - Success rate of requests
2. **Utilization trends** - Are drivers optimally deployed?
3. **Queue health** - Request aging and wait times
4. **Offer efficiency** - Quality of dispatch decisions

## 3.4.11 Data Validation

The system ensures data integrity through:

1. **Attribute validation** in `record_tick()` - confirms required fields exist
2. **Array length consistency** - all metrics arrays same length
3. **Reasonable value ranges** - percentages 0-100, counts non-negative
4. **Mutation history accuracy** - verified against simulation behavior changes

## 3.4.12 Visualization Customization

### Color Coding
```python
PLOT_COLOURS = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700', '#FF99FF', '#99FFFF']
```
Consistent colors across plots for behavior types

### Formatting
- Grid enabled for readability
- Alpha transparency for overlapping data
- Legend placement optimized per plot
- Axis labels with units

---

**Summary**: The metrics system provides a complete audit trail of simulation behavior, with particular emphasis on mutation dynamics. Data flows from real-time simulation events through time-series aggregation into visualization-ready formats, enabling detailed analysis of driver adaptation patterns and system efficiency.
