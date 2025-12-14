# Appendix E: Configuration Constants and Parameters

## E.1 Core Simulation Parameters

### E.1.1 Physics and Movement

| Constant | Value | Module | Purpose |
|----------|-------|--------|---------|
| `EPSILON` | `1e-3` | `simulation.py` | Floating-point tolerance for arrival detection |
| `MIN_SPEED` | `1e-6` | `simulation.py` | Minimum driver speed (prevents stalling) |
| `EPSILON` | `1e-9` | `point.py` | Floating-point tolerance for Point equality |

### E.1.2 Timeout and Expiration

| Constant | Value | Module | Purpose |
|----------|-------|--------|---------|
| `timeout` | 20 (default) | `DeliverySimulation.__init__()` | Maximum wait time before request expires (ticks) |
| `MAX_WAIT_ACCEPTABLE` | ~20 | Implied | Service level depends on this threshold |

---

## E.2 Driver Behaviour Parameters

### E.2.1 GreedyDistanceBehaviour

```python
# Location: phase2/behaviours.py
# Decision Rule: Accept if distance_to(request.pickup) <= max_distance

LAZY_MAX_PICKUP_DISTANCE = 5.0
# Used by LazyBehaviour, represents maximum acceptable pickup distance
```

**Configuration by Context:**

| Use Case | `max_distance` | Purpose |
|----------|---|---|
| Urban (high density) | 3–5 units | Very short distances preferred |
| Suburban | 8–15 units | Moderate distances acceptable |
| Rural (low density) | 20–50 units | Longer distances necessary |

**Example:**
```python
behaviour = GreedyDistanceBehaviour(max_distance=10.0)
# Driver accepts any request with pickup distance <= 10.0 units
```

---

### E.2.2 EarningsMaxBehaviour

**Decision Rule:** Accept if `reward / travel_time >= threshold`

```python
# Location: phase2/behaviours.py

class EarningsMaxBehaviour(DriverBehaviour):
    def __init__(self, min_reward_per_time: float):
        """Accept if reward per unit time meets threshold."""
        self.threshold = min_reward_per_time
```

**Typical Thresholds:**

| Threshold | Interpretation | Driver Type |
|-----------|---|---|
| 0.5 | $0.50 per minute | Very accepting (new/struggling driver) |
| 0.8–1.0 | $0.80–$1.00 per minute | Standard professional driver |
| 1.5–2.0 | $1.50–$2.00 per minute | Selective, experienced driver |
| 3.0+ | $3.00+ per minute | Very selective (only high-value trips) |

**Example:**
```python
behaviour = EarningsMaxBehaviour(min_reward_per_time=0.8)
# Driver accepts if: estimated_reward / estimated_travel_time >= 0.8
```

---

### E.2.3 LazyBehaviour

**Decision Rule:** Accept **ONLY IF** BOTH conditions hold:
1. `idle_duration >= idle_ticks_needed` (sufficient rest)
2. `distance_to(pickup) < 5.0` (nearby job)

```python
# Location: phase2/behaviours.py

LAZY_MAX_PICKUP_DISTANCE = 5.0

class LazyBehaviour(DriverBehaviour):
    def __init__(self, idle_ticks_needed: int):
        """Accept only after N ticks of rest AND pickup nearby."""
        self.idle_ticks_needed = idle_ticks_needed
```

**Rest Duration by Driver Type:**

| `idle_ticks_needed` | Interpretation | Driver Personality |
|---|---|---|
| 0 | Always available | Workholic |
| 3–5 | Short break | Normal professional |
| 8–10 | Medium rest | Tired driver |
| 15+ | Long break | Very selective/tired |

**Example:**
```python
behaviour = LazyBehaviour(idle_ticks_needed=5)
# Driver must rest for 5+ ticks AND request pickup must be < 5.0 units away
```

---

## E.3 Mutation Rule Parameters

### E.3.1 HybridMutation Strategy

```python
# Location: phase2/mutation.py, lines 25–42

HYBRID_LOW_EARNINGS_THRESHOLD = 3.0
# If average earnings in last window < 3.0, switch to GREEDY

HYBRID_HIGH_EARNINGS_THRESHOLD = 10.0
# If average earnings in last window > 10.0, switch to EARNINGS_MAX

HYBRID_COOLDOWN_TICKS = 10
# Minimum ticks between mutations (prevent churn)
# Driver can mutate at most every 10 ticks

HYBRID_STAGNATION_WINDOW = 8
# Examine last 8 ticks to detect stagnation

HYBRID_EXPLORATION_PROBABILITY = 0.3
# 30% chance to explore (try new behaviour) when stagnating
# 70% chance to stay with current behaviour
```

### E.3.2 Behaviour Creation During Mutation

When `HybridMutation` creates a new behaviour instance:

```python
# Location: phase2/mutation.py

# Switch TO Greedy (e.g., when earnings are LOW)
behaviour = GreedyDistanceBehaviour(
    max_distance=GREEDY_MAX_DISTANCE  # 10.0
)

# Switch TO EarningsMax (e.g., when earnings are HIGH)
behaviour = EarningsMaxBehaviour(
    min_reward_per_time=EARNINGS_MIN_REWARD_PER_TIME  # 0.8
)

# Switch TO Lazy (e.g., when exploring)
behaviour = LazyBehaviour(
    idle_ticks_needed=LAZY_IDLE_TICKS_NEEDED  # 5
)
```

**Mutation Parameter Values:**

| Parameter | Value | Module | Rationale |
|-----------|-------|--------|-----------|
| `GREEDY_MAX_DISTANCE` | 10.0 | `mutation.py` | Moderate distance; accepts most requests |
| `EARNINGS_MIN_REWARD_PER_TIME` | 0.8 | `mutation.py` | Mid-range threshold; realistic earnings target |
| `LAZY_IDLE_TICKS_NEEDED` | 5 | `mutation.py` | Reasonable rest period (~5 time units) |
| `LAZY_MAX_DISTANCE` | 5.0 | `behaviours.py` | Short distance; only nearby jobs accepted |

---

## E.4 Request Generation Parameters

### E.4.1 RequestGenerator

```python
# Location: phase2/generator.py, class RequestGenerator

class RequestGenerator:
    def __init__(self, rate: float, width: int, height: int, 
                 start_id: int = 1, enabled: bool = True):
        """
        rate: Expected number of requests per tick (Poisson λ)
        width: Map width for random position generation
        height: Map height for random position generation
        start_id: Starting request ID (auto-increments)
        enabled: Can be disabled (e.g., for CSV-loaded requests)
        """
```

**Typical Configuration:**

| Scenario | `rate` | `width` | `height` | Requests/tick |
|----------|--------|--------|---------|---|
| Light traffic | 0.5 | 100 | 100 | ~0.5 per tick |
| Moderate traffic | 2.0 | 100 | 100 | ~2 per tick |
| Heavy traffic | 5.0 | 100 | 100 | ~5 per tick |
| Very heavy | 10.0 | 100 | 100 | ~10 per tick |

**Poisson Distribution:**
```python
# Used by RequestGenerator.maybe_generate()
num_requests = _generate_poisson(rate)

# Example: rate = 2.0
# P(0 requests) ≈ 0.135
# P(1 request)  ≈ 0.270
# P(2 requests) ≈ 0.270
# P(3 requests) ≈ 0.180
# Mean: 2.0 requests per tick
```

---

## E.5 Simulation Orchestration Constants

### E.5.1 Phase Timing

The simulation tick consists of 9 phases executed in order:

```python
# Location: phase2/simulation.py, DeliverySimulation.tick()

def tick(self):
    """9-phase orchestration per simulation step."""
    
    # Phase 1: Generate new requests
    gen_requests(self)
    # ~O(rate) requests created
    
    # Phase 2: Expire old requests
    expire_requests(self)
    # ~O(R) checks where R = active requests
    
    # Phase 3: Propose assignments
    proposals = get_proposals(self)
    # Time complexity depends on policy
    # NearestNeighbor: O(D²M²), GlobalGreedy: O(DM log(DM))
    # where D = idle drivers, M = waiting requests
    
    # Phase 4: Collect offers
    offers = collect_offers(self, proposals)
    # O(proposals) calls to DriverBehaviour.decide()
    
    # Phase 5: Resolve conflicts
    final = resolve_conflicts(self, offers)
    # O(offers) conflict checking
    
    # Phase 6: Assign requests
    assign_requests(self, final)
    # O(final assignments)
    
    # Phase 7: Move drivers
    move_drivers(self)
    # O(D) driver movements + event handling
    
    # Phase 8: Mutate drivers
    mutate_drivers(self)
    # O(D) mutation checks with 1/10 rate (cooldown)
    
    # Phase 9: Increment time
    self.time += 1
```

### E.5.2 Time Step (dt)

| Constant | Value | Purpose |
|----------|-------|---------|
| `dt` | 1.0 (per tick) | Movement distance = speed × dt |

Driver movement each tick:
```python
# distance_moved = driver.speed * dt
# Example: speed = 1.5, dt = 1.0 → moves 1.5 units per tick
```

---

## E.6 Metrics and Reporting Constants

### E.6.1 Visualization Parameters

```python
# Location: phase2/report_window.py

PLOT_COLOURS = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700', 
                '#FF99FF', '#99FFFF']
# 6-colour palette for behaviour distribution plots

# Figure sizes
figure_1_size = (16, 13)  # Metrics report
figure_2_size = (16, 14)  # Behaviour analysis
figure_3_size = (16, 12)  # Mutation analysis
```

### E.6.2 SimulationTimeSeries Metrics

```python
# Location: phase2/helpers_2/metrics_helpers.py
# Tracked per tick by SimulationTimeSeries

class SimulationTimeSeries:
    def record_tick(self, simulation):
        """Record 9 metrics at each timestep:"""
        
        metrics = {
            'times': int,                      # Simulation tick number
            'served': int,                     # Cumulative requests served
            'expired': int,                    # Cumulative requests expired
            'avg_wait': float,                 # Average wait time (current)
            'pending': int,                    # Active requests in system
            'utilization': float,              # % drivers currently busy
            'behaviour_distribution': dict,    # Count by behaviour type
            'behaviour_mutations': int,        # Cumulative mutations
            'behaviour_stagnation': int,       # Drivers unchanged behaviour
        }
```

---

## E.7 Default Simulation Configuration

### E.7.1 Typical Scenario Setup

```python
# Common initialization

from phase2.driver import Driver
from phase2.point import Point
from phase2.behaviours import GreedyDistanceBehaviour
from phase2.policies import GlobalGreedyPolicy
from phase2.generator import RequestGenerator
from phase2.mutation import HybridMutation
from phase2.simulation import DeliverySimulation

# Initialize drivers
drivers = [
    Driver(
        id=i,
        position=Point(50, 50),  # Start at center
        speed=1.5,               # Medium speed
        behaviour=GreedyDistanceBehaviour(max_distance=10.0)
    )
    for i in range(10)  # 10 drivers
]

# Request generation: 2 requests per tick on average
generator = RequestGenerator(
    rate=2.0,
    width=100,
    height=100,
    start_id=1,
    enabled=True
)

# Dispatch policy: more efficient than nearest-neighbor
policy = GlobalGreedyPolicy()

# Mutation: drivers adapt behaviour over time
mutation = HybridMutation()

# Create simulation
sim = DeliverySimulation(
    drivers=drivers,
    dispatch_policy=policy,
    request_generator=generator,
    mutation_rule=mutation,
    timeout=20  # Requests expire after 20 ticks
)

# Run simulation
for tick in range(1000):
    sim.tick()

# Examine results
snapshot = sim.get_snapshot()
print(f"Served: {snapshot['statistics']['served']}")
print(f"Expired: {snapshot['statistics']['expired']}")
print(f"Avg wait: {snapshot['statistics']['avg_wait']}")
```

---

## E.8 Environment Constants

### E.8.1 Map Boundaries

| Dimension | Typical Value | Range | Purpose |
|-----------|---|---|---|
| Width | 100 units | 50–500 | Map horizontal extent |
| Height | 100 units | 50–500 | Map vertical extent |

**Distance Scaling:**
- Point (0, 0) to Point (100, 100) → distance ≈ 141.4 units (diagonal)
- Behaviour thresholds should scale with map size

---

## E.9 Performance Characteristics

### E.9.1 Time Complexity per Tick

| Phase | Complexity | Notes |
|-------|-----------|-------|
| Generate | O(1) avg | Poisson: mean = rate |
| Expire | O(R) | R = active requests |
| Propose | O(D²M²) NN / O(DM log DM) GG | D = idle drivers, M = waiting |
| Collect | O(proposals) | Each offer → 1 behaviour decision |
| Resolve | O(offers) | Conflict detection and resolution |
| Assign | O(assignments) | Link drivers to requests |
| Move | O(D) | Step each driver |
| Mutate | O(D) | 1 in 10 chance (cooldown) |
| **Total** | **O(max(D²M², D·R))** | Dispatch dominates |

### E.9.2 Space Complexity

| Data Structure | Size | Notes |
|---|---|---|
| drivers | O(D) | List of D driver objects |
| requests | O(total_requests) | Accumulates over simulation |
| history per driver | O(trips) | ~2-20 trips per driver typical |
| time_series | O(ticks) | Grows linearly with simulation length |

---

## E.10 Tuning Guide

### To Make Simulation More Challenging:

1. **Increase request rate:** `rate = 5.0` (was 2.0)
2. **Increase map size:** `width = 200, height = 200`
3. **Lower timeout:** `timeout = 10` (was 20)
4. **Reduce driver speed:** `speed = 0.8` (was 1.5)
5. **Increase pickiness:** `max_distance = 5.0` (was 10.0)

### To Make Simulation Easier:

1. **Decrease request rate:** `rate = 0.5` (was 2.0)
2. **Decrease map size:** `width = 50, height = 50`
3. **Increase timeout:** `timeout = 40` (was 20)
4. **Increase driver speed:** `speed = 2.5` (was 1.5)
5. **Reduce pickiness:** `max_distance = 20.0` (was 10.0)

---

## E.11 Summary Table

| Category | Key Constant | Value | Impact |
|----------|---|---|---|
| **Physics** | EPSILON | 1e-3 | Arrival detection sensitivity |
| **Behaviour** | Greedy max_distance | 10.0 | Driver acceptance threshold |
| **Behaviour** | EarningsMax threshold | 0.8 | Earnings-per-time target |
| **Behaviour** | Lazy rest period | 5 ticks | Required idle time |
| **Mutation** | Earnings threshold (low) | 3.0 | Switch to greedy trigger |
| **Mutation** | Earnings threshold (high) | 10.0 | Switch to earnings-max trigger |
| **Mutation** | Cooldown | 10 ticks | Min between mutations |
| **Mutation** | Stagnation window | 8 ticks | Detection window |
| **Mutation** | Exploration prob | 0.3 | 30% chance to explore |
| **Generation** | Poisson rate | 2.0 | Expected requests/tick |
| **Simulation** | Timeout | 20 ticks | Request expiration |
| **Simulation** | Driver speed | 1.5 units/tick | Movement rate |
