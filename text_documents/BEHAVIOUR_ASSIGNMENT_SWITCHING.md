# Driver Behaviour Assignment and Switching: Detailed Description

## Part 1: Initial Behaviour Assignment

### When Does a Driver Get Assigned a Behaviour?

A driver receives a behaviour when it is **first created** during simulation initialization. This happens in two possible scenarios:

#### Scenario 1: Drivers Created Programmatically
When the simulation is set up in code, drivers are instantiated directly:

```python
# Example: Creating a driver with GreedyDistanceBehaviour
behaviour = GreedyDistanceBehaviour(max_distance=10.0)
driver = Driver(
    id=1,
    position=Point(50, 50),
    speed=1.5,
    behaviour=behaviour  # Behaviour assigned here
)
```

At this moment:
- The driver is born with a specific behaviour policy
- This behaviour is stored as `driver.behaviour` (a reference to the behaviour object)
- The behaviour will remain unchanged **until a mutation occurs**
- The driver's idle time is initialized (time when it started being available)

#### Scenario 2: Drivers Generated from CSV
When loading drivers from a data file, the adapter creates behaviour objects based on configuration:

```python
# Each loaded driver receives a default initial behaviour
driver = Driver(
    id=loaded_id,
    position=Point(x, y),
    speed=speed,
    behaviour=LazyBehaviour(idle_ticks_needed=5)  # Default initial behaviour
)
```

### Behaviour as a Strategy Pattern

The behaviour object implements the **Strategy Pattern**:
- The `Driver` class does **not** contain decision logic
- Instead, it delegates all offer decisions to `driver.behaviour.decide(offer, time)`
- This design allows behaviour to be **swapped at runtime** without changing the driver

```python
# How a driver uses its behaviour to make decisions
offer = Offer(driver=driver, request=request, reward=5.0, travel_time=10.0)
should_accept = driver.behaviour.decide(driver, offer, time=100)

# The actual decision logic lives in the behaviour object, not the driver
# GreedyDistanceBehaviour would check: distance_to_pickup <= 10.0
# EarningsMaxBehaviour would check: 5.0 / 10.0 >= 0.8
# LazyBehaviour would check: idle_duration >= 5 AND distance < 5.0
```

---

## Part 2: Behaviour During Simulation (No Switching Yet)

### What Happens Each Tick with the Current Behaviour?

Every simulation tick (time increment), the driver's behaviour is used:

#### Phase 4: Collect Offers
When offers are proposed to drivers:
1. For each idle driver with an offer
2. The dispatch policy creates an `Offer` object
3. The driver's current behaviour evaluates the offer: `behaviour.decide(driver, offer, time)`
4. If returns `True`: driver accepts and gets assigned the request
5. If returns `False`: driver rejects and remains idle

#### Example: Driver with GreedyDistanceBehaviour

```
Time = 50
Driver #3 (GreedyDistanceBehaviour, max_distance=10.0) is idle at position (30, 40)
New request appears at pickup location (35, 44) - distance = ~6.4 units

Offer proposed to Driver #3:
  driver.behaviour.decide(driver, offer, time=50)
  → Check: distance_to_pickup (6.4) <= max_distance (10.0)
  → TRUE: Accept! Move to pickup

Later in tick:
  driver.position is updated by driver.step(dt=1.0)
  Driver moves 1.5 units closer to pickup
  Eventually reaches pickup, completes it, moves to dropoff
  Eventually reaches dropoff, completes delivery, earns money
```

---

## Part 3: Behaviour Switching Via Mutation

### When Does Behaviour Switching Occur?

Behaviour switching happens in **Phase 8: Mutate Drivers**, which occurs **after every tick**.

The `HybridMutation` rule evaluates each driver independently to decide if switching makes sense.

#### Step 1: Cooldown Check
```python
# First question: Can this driver mutate right now?

last_mutation_time = driver._last_mutation_time  # When did they last switch?
time_since_mutation = current_time - last_mutation_time

if time_since_mutation < HYBRID_COOLDOWN_TICKS (10 ticks):
    # Nope, still in cooldown period
    # Prevents behaviour thrashing (constant switching)
    return  # Skip mutation, keep current behaviour
else:
    # OK, cooldown expired, check performance
```

**Purpose of cooldown:** A driver needs time to "adjust" to their new behaviour before switching again. This prevents unrealistic constant switching.

#### Step 2: Earnings Analysis
```python
# Second question: How is this driver performing?

average_earnings = calculate_average_earnings(driver)
# Looks at the last 8 ticks of trip history
# Formula: sum of earnings in last 8 trips / number of trips

if average_earnings < HYBRID_LOW_EARNINGS_THRESHOLD (3.0):
    # Driver is struggling, not making enough money
    # They need to be less picky
    switch_to_greedy(driver)
    
elif average_earnings > HYBRID_HIGH_EARNINGS_THRESHOLD (10.0):
    # Driver is doing great, making good money
    # They can afford to be selective
    switch_to_earnings_max(driver)
    
else:
    # Driver is in middle range (3.0 <= earnings <= 10.0)
    # Check for stagnation
```

#### Step 3: Stagnation Detection (if in middle range)
```python
# Third question: Is the driver stuck in a rut?

earnings_window = last 8 trips earnings
has_stagnated = (all earnings in window are similar, no improvement)

if has_stagnated:
    # Driver is earning consistently but not improving
    # Time to try something different
    
    if random() < HYBRID_EXPLORATION_PROBABILITY (0.3):
        # 30% chance to switch to a random behaviour
        # This helps drivers escape local optima
        explore_behaviour(driver)
        # Could become Greedy, EarningsMax, or LazyBehaviour randomly
    else:
        # 70% chance: stick with current behaviour
        return
else:
    # Driver is adapting well, no change needed
    return
```

---

## Part 4: The Moment of Switching

### What Actually Changes When Switching Behaviours?

When a behaviour switch is triggered, the following happens:

#### Before Switch
```python
Driver #5 is:
  - behaviour = LazyBehaviour(idle_ticks_needed=5)
  - earnings = 2.8 (low, below 3.0 threshold)
  - idle_since = 95
  - status = IDLE
```

#### During Mutation (Phase 8)
```python
# HybridMutation.maybe_mutate() is called on Driver #5

# Step 1: Check cooldown - PASS (10+ ticks since last mutation)
# Step 2: Calculate average_earnings - 2.8
# Step 3: 2.8 < 3.0 → LOW EARNINGS DETECTED!
# Step 4: Create new behaviour

new_behaviour = GreedyDistanceBehaviour(max_distance=10.0)
# This is a FRESH instance with default parameters
```

#### After Switch
```python
Driver #5 is now:
  - behaviour = GreedyDistanceBehaviour(max_distance=10.0)  [CHANGED]
  - earnings = 2.8  [unchanged, history preserved]
  - idle_since = 95  [unchanged]
  - status = IDLE  [unchanged]
  - _last_mutation_time = 100  [updated to current time]
  - history = [trips...]  [unchanged]
```

### What Doesn't Change?
- Driver ID
- Driver position and speed
- Current assignment (if any)
- Earnings and history (all trips recorded)
- Idle timer (time since last became idle)

### What Changed?
- **Only** `driver.behaviour` (the strategy object)
- Plus internal tracking: `driver._last_mutation_time` (for cooldown)

---

## Part 5: Impact of Behaviour Switching

### How Does the Switch Affect Decision-Making?

#### Before: LazyBehaviour
```
Tick 105, Offer proposed:
  - Driver idle for 10 ticks (meets lazy requirement)
  - Pickup is 8 units away

LazyBehaviour.decide():
  if idle_duration (10) >= idle_ticks_needed (5)  → TRUE
  AND distance_to_pickup (8) < LAZY_MAX_DISTANCE (5.0)  → FALSE
  Result: REJECT (distance requirement failed)
```

#### After: GreedyDistanceBehaviour (same offer)
```
Tick 105, Same offer, same driver:
  - Distance to pickup is 8 units

GreedyDistanceBehaviour.decide():
  if distance_to_pickup (8) <= max_distance (10.0)  → TRUE
  Result: ACCEPT (much more willing now)
```

**Result:** The driver now accepts jobs it previously rejected!

---

## Part 6: Chain Reaction After Switching

### What Happens After a Behaviour Switch?

When a driver's behaviour changes, it affects their entire future:

#### Immediate Effect (same tick)
```
Tick 100: Driver #5 mutates from Lazy to Greedy
Tick 101: Phase 3 (Propose) - DispatchPolicy now matches this driver
          with new criteria (more generous distance allowance)
Tick 101: Phase 4 (Collect) - GreedyDistanceBehaviour accepts more offers
Tick 101: Phase 6-7 (Move) - Driver starts new trip immediately
```

#### Medium-term Effect (next 10 ticks)
```
During cooldown (ticks 101-110):
  - Driver cannot mutate again
  - Earns money with new Greedy behaviour
  - If earnings improve: stays greedy longer
  - If earnings worsen: will switch again at tick 111
```

#### Long-term Effect (visible in metrics)
```
Metrics after switch:
  - behaviour_distribution changes (one more Greedy, one less Lazy)
  - utilization may increase (driver accepts more offers)
  - avg_wait may decrease (driver busier, fewer idle moments)
  - earnings pattern changes in driver.history
```

---

## Part 7: Realistic Example: Driver's Journey

### Complete Lifecycle with Multiple Switches

```
TICK 0 - Initialization:
  Driver #7 created with LazyBehaviour(idle_ticks_needed=5)
  Status: IDLE at position (50, 50)

TICKS 1-50:
  Various offers come and go
  LazyBehaviour is selective: only accepts nearby jobs after rest
  Earnings accumulate slowly: ~2.5 per trip (below 3.0 threshold)

TICK 51 - First Mutation Check:
  Cooldown: 0 ticks (first check, can mutate)
  Average earnings: 2.5 (< 3.0)
  → Switch to GreedyDistanceBehaviour(max_distance=10.0)
  Record: _last_mutation_time = 51

TICKS 52-61:
  Now accepts MORE offers (bigger distance threshold)
  Busier: completes 8 trips instead of 4
  But earnings/trip: only 2.8 (still low)
  Overall earnings up due to volume: 22.4 total

TICK 62 - Second Mutation Check:
  Cooldown: 11 ticks (51 → 62, OK to mutate)
  Average earnings: 2.8 (still < 3.0)
  → Stagnation check: no improvement over time
  → Exploration: roll dice, 25% chance (< 0.3) → YES
  → Switch to EarningsMaxBehaviour(threshold=0.8)
  Record: _last_mutation_time = 62

TICKS 63-72:
  Now accepts only HIGH-reward jobs
  Trip count drops: only 2 trips
  But earnings/trip: 5.5 (high value)
  Testing this new strategy

TICK 73 - Third Mutation Check:
  Cooldown: 11 ticks (62 → 73, OK to mutate)
  Average earnings: 5.5 (between 3.0 and 10.0)
  → No stagnation: performance is improving
  → Keep EarningsMaxBehaviour
  No mutation

TICKS 74-120:
  Driver continues as EarningsMaxBehaviour
  Earns consistently 4-6 per trip
  Total earnings growing healthily
  Eventually might hit 10.0 threshold and switch again
```

---

## Part 8: Why This Design?

### The Philosophy Behind Behaviour Switching

1. **Realistic Adaptation**
   - Real drivers adjust their strategies based on earnings
   - A driver struggling to earn money becomes less selective
   - A driver doing well can afford to be picky

2. **Prevents Local Optima**
   - Stagnation detection + exploration breaks unhelpful patterns
   - Driver stuck earning 4/trip tries something new
   - Could discover a better strategy worth 6/trip

3. **Fair Comparison**
   - Dispatch policy remains constant (e.g., GlobalGreedy)
   - But driver BEHAVIOURS vary and evolve
   - Allows testing: "Does our policy help diverse driver types succeed?"

4. **Stable Transitions**
   - Cooldown prevents thrashing (switching every tick)
   - Drivers need time to "get used to" a new behaviour
   - Realistic: can't completely change strategy instantly

---

## Part 9: Tracking Behaviour Changes

### What Gets Recorded?

The `SimulationTimeSeries` object captures behaviour evolution:

```python
# Every tick, after mutation phase:

# Update 1: Current distribution
behaviour_distribution = Counter()
for driver in drivers:
    behaviour_distribution[driver.behaviour.__class__.__name__] += 1

timeseries.behaviour_distribution.append(behaviour_distribution)
# Result: {'LazyBehaviour': 6, 'GreedyDistanceBehaviour': 3, 'EarningsMaxBehaviour': 1}

# Update 2: Cumulative mutations
timeseries.behaviour_mutations.append(total_mutations_so_far)
# Result: [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, ...]
# Tick 3: first mutation occurred
# Tick 6: second mutation occurred
# Tick 10: third mutation occurred

# Update 3: Stagnant drivers (unchanged behaviour)
timeseries.behaviour_stagnation.append(count_of_stagnant_drivers)
# Result: [10, 10, 10, 9, 9, 8, 8, 8, 7, ...]
# Most drivers start stagnant (same behaviour)
# As mutations occur, count decreases
```

These metrics are then **visualized in the Behaviour Analysis window** showing:
- How many drivers use each behaviour type over time (stacked area chart)
- When mutations happen (cumulative line)
- How many drivers are "stuck" unchanged (stagnation line)

---

## Summary

**Initial Assignment:**
- Drivers receive a behaviour when created
- Behaviour implements Strategy Pattern (swappable decision logic)

**Usage:**
- Each tick, driver's behaviour.decide() evaluates offers
- Determines which requests to accept

**Switching:**
- Occurs in Phase 8 (Mutate) every tick
- Only if cooldown expired (10+ ticks since last switch)
- Based on 3 factors:
  1. Low earnings (< 3.0) → switch to Greedy
  2. High earnings (> 10.0) → switch to EarningsMax
  3. Stagnation (30% explore) → try random behaviour

**After Switch:**
- Only `driver.behaviour` object changes
- Everything else persists (position, history, earnings)
- Next tick, driver makes decisions with new behaviour
- Metrics track distribution changes and mutation count

**Visible Result:**
- Fleet composition changes over time
- Some drivers become Greedy (struggling), others EarningsMax (succeeding)
- Behaviour Analysis window shows this evolution
- Reveals which dispatch policies help or hinder different driver types
