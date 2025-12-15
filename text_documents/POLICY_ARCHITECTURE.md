# Dispatch Policy Architecture: Complete Guide

## Overview

The dispatch system uses a **three-stage pipeline** to intelligently assign requests to drivers while respecting both distance (geographical proximity) and speed (driver capabilities).

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   STAGE 1    │ --> │   STAGE 2    │ --> │   STAGE 3    │
│  PROPOSALS   │     │    OFFERS    │     │ ASSIGNMENTS  │
│  (distance)  │     │(travel_time) │     │(travel_time) │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Stage 1: Dispatch Policy (Distance-Based Proposal Generation)

### Purpose
Generate initial driver-request pairings based on geographical proximity.

### When it Runs
Every simulation tick: `tick() → get_proposals(simulation)`

### Three Available Policies

#### 1. **NearestNeighborPolicy (NN)**
- **Algorithm**: Greedy iterative matching - find closest pair, assign, repeat
- **Complexity**: O(n²m²) - slower but simple
- **Approach**: Myopic - only sees current state
- **Best for**: Abundant drivers (can afford local optima)

#### 2. **GlobalGreedyPolicy (GG)**
- **Algorithm**: Rank ALL pairs by distance, greedily pick shortest
- **Complexity**: O(nm log nm) - faster, better quality
- **Approach**: Foresight - sees all options upfront
- **Best for**: Scarce drivers (needs global optimization)

#### 3. **AdaptiveHybridPolicy (Current)**
- **Algorithm**: Wrapper that switches between NN and GG
- **Decision Logic**: `if requests > drivers: use GG, else: use NN`
- **Re-evaluation**: Every tick (adaptive to changing load)
- **Best for**: Mixed scenarios with varying loads

### Key Point: Distance Only
Stage 1 uses **DISTANCE only** because:
- ✓ Computationally cheap (Euclidean distance formula)
- ✓ Good spatial proxy for decision-making
- ✓ Speed factors handled in Stages 2 & 3

### Example Output

```python
# Input to policy:
drivers = [D1(speed=2.0)@(0,0), D2(speed=1.0)@(50,50)]
requests = [R1@(10,10), R2@(55,55)]

# Stage 1 sees ONLY distances:
D1→R1: 14.1 ✓ closest overall
D1→R2: 77.8
D2→R1: 63.6
D2→R2: 7.1  ✓ closest to D2

# Stage 1 Output (PROPOSALS):
[(D1, R1), (D2, R2)]

# Note: Speed NOT considered yet
```

---

## Stage 2: Collect Offers (Speed-Aware Offer Generation)

### Purpose
Convert proposals to offers, calculate actual travel times, apply driver behavior logic.

### When it Runs
After Stage 1: `collect_offers(simulation, proposals)`

### Process

For each proposal `(driver, request)`:

1. **Calculate travel_time**
   ```
   travel_time = distance_to_pickup / driver.speed
   ```
   → **This is where SPEED enters the system**

2. **Calculate reward**
   ```
   reward = distance_to_pickup + distance_pickup_to_dropoff
   ```

3. **Create Offer**
   ```python
   Offer(driver, request, travel_time, reward)
   ```

4. **Apply Driver Behavior**
   ```python
   if driver.behaviour.decide(driver, offer, time):
       offers.append(offer)  # Driver accepts
   else:
       skip  # Driver rejects
   ```

### Example

```python
# Input from Stage 1:
proposals = [(D1, R1), (D2, R2)]

# Proposal 1: D1 → R1
distance = 14.1
D1.speed = 2.0
travel_time = 14.1 / 2.0 = 7.05 seconds  ✓ FAST
reward ≈ 24.1
Offer1 = Offer(D1, R1, 7.05, 24.1)
D1.behaviour.decide(...) → accepts
→ ADD TO OFFERS

# Proposal 2: D2 → R2
distance = 7.1
D2.speed = 1.0
travel_time = 7.1 / 1.0 = 7.1 seconds  (slow driver!)
reward ≈ 12.2
Offer2 = Offer(D2, R2, 7.1, 12.2)
D2.behaviour.decide(...) → accepts
→ ADD TO OFFERS

# Stage 2 Output (OFFERS):
[Offer(D1, R1, 7.05), Offer(D2, R2, 7.1)]

# Key: Speed now visible! D1 faster (7.05 vs 7.1)
```

---

## Stage 3: Resolve Conflicts (Travel_Time-Based Selection)

### Purpose
When multiple drivers are interested in the same request, pick the fastest one.

### When it Runs
After Stage 2: `resolve_conflicts(simulation, offers)`

### Conflict Scenario

```python
# What if both drivers wanted same request?
offers = [
    Offer(D1, R1, 7.05),     # D1 to R1: fast
    Offer(D2, R1, 56.6),     # D2 to R1: slow! (D2 is 56.6 units away)
    Offer(D2, R2, 7.1)       # D2 to R2: okay
]
```

### Resolution Algorithm

```python
# Step 1: Group by request_id
grouped = {
    R1: [Offer(D1, R1, 7.05), Offer(D2, R1, 56.6)],
    R2: [Offer(D2, R2, 7.1)]
}

# Step 2: Sort each group by travel_time (ascending)
grouped[R1].sort(key=lambda o: o.estimated_travel_time)
# Result: [Offer(D1, R1, 7.05) ✓, Offer(D2, R1, 56.6)]

# Step 3: Take first (fastest) from each group
final = [
    grouped[R1][0],  # D1, R1, 7.05 seconds ✓ FASTEST
    grouped[R2][0]   # D2, R2, 7.1 seconds
]
```

### Code Implementation

```python
def resolve_conflicts(simulation, offers):
    """Group offers by request, keep fastest driver per request."""
    from collections import defaultdict
    
    grouped = defaultdict(list)
    for o in offers:
        grouped[o.request.id].append(o)
    
    final = []
    for same_request_offers in grouped.values():
        # Sort by travel_time (ascending)
        same_request_offers.sort(key=lambda o: o.estimated_travel_time)
        # Keep fastest driver
        final.append(same_request_offers[0])
    
    return final
```

### Key Insight
**Stage 3 corrects for speed differences!** A slow driver with a close request can lose to a fast driver with a farther request.

---

## Distance vs Travel_Time: Decision Matrix

### Stage 1: POLICIES
```
┌────────────────────────────────────┐
│ Uses: DISTANCE ONLY                │
├────────────────────────────────────┤
│ Why: Fast, good spatial proxy      │
│ Sort key: d.position.distance_to() │
│ Ignores: Driver speed              │
│ Example: "14 units vs 50 units"    │
│          → Closer one wins          │
└────────────────────────────────────┘
```

### Stage 2: COLLECT OFFERS
```
┌────────────────────────────────────┐
│ Calculates: TRAVEL_TIME            │
├────────────────────────────────────┤
│ Formula: distance / speed          │
│ Why: Actual ETA needed             │
│ Stores: In Offer.estimated_time    │
│ Filters: By behavior.decide()      │
│ Example: "14 units, speed 2.0"     │
│          → 7.0 seconds             │
└────────────────────────────────────┘
```

### Stage 3: RESOLVE CONFLICTS
```
┌────────────────────────────────────┐
│ Uses: TRAVEL_TIME                  │
├────────────────────────────────────┤
│ Why: When conflicts occur, pick    │
│      driver with shortest ETA      │
│ Sort key: o.estimated_travel_time  │
│ Considers: Driver speed (embedded) │
│ Example: "7.0s vs 14.2s"           │
│          → 7.0s wins               │
└────────────────────────────────────┘
```

---

## Complete Simulation Tick Example

### Initial State (Tick 5)

```
Drivers:
  D1: position (0, 0), speed 2.0, status IDLE
  D2: position (50, 50), speed 1.0, status IDLE

Requests:
  R1: pickup (10, 10), dropoff (20, 20), status WAITING
  R2: pickup (55, 55), dropoff (60, 60), status WAITING
```

### Stage 1: Get Proposals

```python
AdaptiveHybridPolicy.assign([D1, D2], [R1, R2], 5):
    # Check ratio: 2 requests, 2 drivers
    # Is 2 > 2? NO → Use NearestNeighbor
    
    # NN finds closest using DISTANCE:
    distances = {
        'D1→R1': 14.1  ✓ closest overall
        'D1→R2': 77.8
        'D2→R1': 56.6
        'D2→R2': 7.1   ✓ closest to D2
    }
    
    # Greedy iteration:
    # 1st: Pick (D1, R1) - distance 14.1, remove D1 and R1
    # 2nd: Pick (D2, R2) - distance 7.1, remove D2 and R2
    
    OUTPUT: [(D1, R1), (D2, R2)]
```

### Stage 2: Collect Offers

```python
For (D1, R1):
    distance = 14.1
    travel_time = 14.1 / 2.0 = 7.05 seconds ✓ FAST
    Offer1 = Offer(D1, R1, 7.05, reward=...)
    D1.behaviour.decide(Offer1) → accepts
    
For (D2, R2):
    distance = 7.1
    travel_time = 7.1 / 1.0 = 7.1 seconds
    Offer2 = Offer(D2, R2, 7.1, reward=...)
    D2.behaviour.decide(Offer2) → accepts
    
OUTPUT: [Offer1, Offer2]
```

### Stage 3: Resolve Conflicts

```python
Group by request:
    R1: [Offer1(D1, 7.05)]
    R2: [Offer2(D2, 7.1)]

Sort each by travel_time:
    R1: [Offer1] (only one)
    R2: [Offer2] (only one)

No conflicts! Take first from each:
    Final: [Offer1, Offer2]
    
    Assignments:
    R1 → D1 (7.05 seconds)
    R2 → D2 (7.1 seconds)
```

### Stage 4-9: Assignment & Movement
```python
D1.assign_request(R1, 5)  # D1 status → TO_PICKUP
D2.assign_request(R2, 5)  # D2 status → TO_PICKUP

# Then: Move drivers, handle arrivals, mutations, etc.
```

---

## Design Benefits

### 1. **Separation of Concerns**
- Stage 1: Geographic optimization
- Stage 2: Behavior & filtering
- Stage 3: Speed-aware conflict resolution

### 2. **Computational Efficiency**
- Stage 1: No speed calculation (expensive)
- Stage 2: Travel_time calculated once per offer
- Stage 3: Only when conflicts exist

### 3. **Flexibility**
- Can swap policies without affecting Stages 2 & 3
- Speed always considered in resolution
- Behavior logic independent

### 4. **Correctness**
- Fast drivers get advantage in conflicts
- Slow drivers + close requests still valid
- System self-corrects through resolution

---

## Key Takeaways

### Three-Stage Pipeline
1. **Proposals** (distance-based greedy)
2. **Offers** (calculate travel_time, apply behavior)
3. **Assignments** (resolve conflicts by speed)

### Policy Selection (Binary)
- `requests > drivers` → **GlobalGreedy** (optimize scarce resource)
- `requests ≤ drivers` → **NearestNeighbor** (responsive + fast)

### Distance vs Travel_Time
- **Distance**: Fast spatial approximation, used in Stage 1
- **Travel_Time**: Actual ETA, used in Stages 2 & 3

### Conflict Resolution
- When multiple drivers want same request
- Sort by travel_time (fastest wins)
- Automatically optimizes for speed

### Speed Matters
A fast driver with a farther request can outbid a slow driver with a closer request when conflicts occur. This is by design and ensures the system optimizes for actual service time, not just distance.

---

## Implementation Files

- **`phase2/policies.py`**: Policy implementations (NN, GG, Adaptive)
- **`phase2/offer.py`**: Offer dataclass with travel_time
- **`phase2/helpers_2/engine_helpers.py`**: 
  - `get_proposals()` → calls policy.assign()
  - `collect_offers()` → calculates travel_time
  - `resolve_conflicts()` → sorts by travel_time
- **`test/test_policies.py`**: Policy tests (31 total)
