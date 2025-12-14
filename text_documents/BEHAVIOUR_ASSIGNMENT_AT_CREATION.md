# Driver Behaviour Assignment at Creation

## Overview: Two Sources of New Drivers

Drivers enter the simulation through two mechanisms:
1. **Programmatic Generation** - Created dynamically during simulation setup
2. **CSV Loading** - Loaded from data files at initialization

Each source has different behaviour assignment strategies.

---

## Part 1: Programmatic Driver Generation

### When Drivers Are Created Programmatically

Programmatic driver creation happens during **simulation initialization**, typically when running standalone tests or experiments:

```python
from phase2.driver import Driver
from phase2.point import Point
from phase2.behaviours import GreedyDistanceBehaviour, LazyBehaviour

# Example: Creating drivers for a fresh simulation
drivers = []
for i in range(10):
    behaviour = GreedyDistanceBehaviour(max_distance=10.0)
    driver = Driver(
        id=i,
        position=Point(50, 50),
        speed=1.5,
        behaviour=behaviour  # Explicitly assigned
    )
    drivers.append(driver)

sim = DeliverySimulation(
    drivers=drivers,
    dispatch_policy=GlobalGreedyPolicy(),
    request_generator=RequestGenerator(rate=2.0, width=100, height=100),
    mutation_rule=HybridMutation(),
    timeout=20
)
```

### Behaviour Assignment Strategy: Explicit Choice

When drivers are created programmatically, **each driver's behaviour is chosen explicitly by the programmer**.

#### Uniform Assignment (All Same Behaviour)

```python
# All 10 drivers get the same behaviour
behaviour = LazyBehaviour(idle_ticks_needed=5)
for i in range(10):
    driver = Driver(
        id=i,
        position=Point(50, 50),
        speed=1.5,
        behaviour=behaviour
    )
    drivers.append(driver)

# Result: 100% LazyBehaviour at start
# Useful for: Testing how a single behaviour type performs under a policy
```

**Likelihood Distribution:**
- LazyBehaviour: 100%
- GreedyDistanceBehaviour: 0%
- EarningsMaxBehaviour: 0%

#### Proportional Assignment (Mixed Fleet)

```python
# Simulate realistic fleet composition
behaviours = [
    LazyBehaviour(idle_ticks_needed=5),
    GreedyDistanceBehaviour(max_distance=10.0),
    EarningsMaxBehaviour(min_reward_per_time=0.8),
]

for i in range(10):
    behaviour = behaviours[i % 3]  # Round-robin
    driver = Driver(
        id=i,
        position=Point(50, 50),
        speed=1.5,
        behaviour=behaviour
    )
    drivers.append(driver)

# Result: Roughly 33% each
# Drivers 0, 3, 6, 9: LazyBehaviour
# Drivers 1, 4, 7: GreedyDistanceBehaviour
# Drivers 2, 5, 8: EarningsMaxBehaviour
```

**Likelihood Distribution:**
- LazyBehaviour: 33.3%
- GreedyDistanceBehaviour: 33.3%
- EarningsMaxBehaviour: 33.3%

#### Random Assignment (Stochastic Fleet)

```python
import random

for i in range(10):
    behaviour_type = random.choice(['lazy', 'greedy', 'earnings_max'])
    
    if behaviour_type == 'lazy':
        behaviour = LazyBehaviour(idle_ticks_needed=5)
    elif behaviour_type == 'greedy':
        behaviour = GreedyDistanceBehaviour(max_distance=10.0)
    else:
        behaviour = EarningsMaxBehaviour(min_reward_per_time=0.8)
    
    driver = Driver(
        id=i,
        position=Point(50, 50),
        speed=1.5,
        behaviour=behaviour
    )
    drivers.append(driver)

# Result: Random distribution, typically ~33% each
# But with randomness: could be 40% LazyBehaviour, 30% Greedy, 30% EarningsMax
```

**Likelihood Distribution (Expected):**
- LazyBehaviour: 33.3%
- GreedyDistanceBehaviour: 33.3%
- EarningsMaxBehaviour: 33.3%

**Likelihood Distribution (Actual Run):**
- LazyBehaviour: 40% (4/10 drivers)
- GreedyDistanceBehaviour: 30% (3/10 drivers)
- EarningsMaxBehaviour: 30% (3/10 drivers)

#### Weighted Random Assignment

```python
import random

# Realistic fleet: many greedy drivers (newly trained), few selective ones
weights = {
    'lazy': 0.2,           # 20% - veteran selective drivers
    'greedy': 0.6,         # 60% - newer drivers, less choosy
    'earnings_max': 0.2,   # 20% - experienced optimizers
}

for i in range(10):
    behaviour_type = random.choices(
        list(weights.keys()),
        weights=list(weights.values()),
        k=1
    )[0]
    
    if behaviour_type == 'lazy':
        behaviour = LazyBehaviour(idle_ticks_needed=5)
    elif behaviour_type == 'greedy':
        behaviour = GreedyDistanceBehaviour(max_distance=10.0)
    else:
        behaviour = EarningsMaxBehaviour(min_reward_per_time=0.8)
    
    driver = Driver(
        id=i,
        position=Point(50, 50),
        speed=1.5,
        behaviour=behaviour
    )
    drivers.append(driver)

# Result: Biased distribution reflecting realistic fleet composition
```

**Likelihood Distribution (Expected):**
- LazyBehaviour: 20%
- GreedyDistanceBehaviour: 60%
- EarningsMaxBehaviour: 20%

**Likelihood Distribution (Actual Run with 10 drivers):**
- LazyBehaviour: 2 drivers (20%)
- GreedyDistanceBehaviour: 6 drivers (60%)
- EarningsMaxBehaviour: 2 drivers (20%)

---

## Part 2: CSV-Based Driver Loading

### When Drivers Are Loaded from CSV

CSV loading happens during **adapter initialization** when the GUI is being used. The adapter loads driver data from a file:

```python
# File: data/drivers.csv
id,x,y,speed
1,10,20,1.5
2,15,25,1.2
3,50,50,1.8
...
```

### Current Implementation: Default Assignment

When drivers are loaded from CSV, the current implementation assigns a **default initial behaviour**:

```python
# In adapter.py or equivalent initialization code

from phase2.driver import Driver
from phase2.point import Point
from phase2.behaviours import LazyBehaviour

def load_drivers_from_csv(filepath):
    drivers = []
    with open(filepath, 'r') as f:
        for line in f:
            id, x, y, speed = parse_csv_line(line)
            
            # Default behaviour: LazyBehaviour
            behaviour = LazyBehaviour(idle_ticks_needed=5)
            
            driver = Driver(
                id=id,
                position=Point(x, y),
                speed=speed,
                behaviour=behaviour  # ALL get LazyBehaviour
            )
            drivers.append(driver)
    
    return drivers

# Result: 100% LazyBehaviour at start
```

**Current Likelihood Distribution:**
- LazyBehaviour: 100%
- GreedyDistanceBehaviour: 0%
- EarningsMaxBehaviour: 0%

### Why Default to LazyBehaviour?

1. **Conservative Choice:** LazyBehaviour is selective (won't accept every offer)
   - Safer for testing: drivers won't spam accept
   - Allows requests to wait for better matches

2. **Aligns with CSV Context:** CSV files typically contain pre-configured scenarios
   - User controls driver count, speed, positions
   - Default behaviour provides predictable baseline
   - Mutation will adapt behaviours later anyway

3. **Matches GUI Expectations:** The GUI is designed for human interaction
   - Users load drivers and see predictable initial behavior
   - As simulation runs, mutations will diversify behaviours

---

## Part 3: Alternative CSV Assignment Strategies

### Strategy 1: Behaviour Column in CSV

Add a behaviour column to specify each driver's initial behaviour:

```csv
id,x,y,speed,behaviour
1,10,20,1.5,lazy
2,15,25,1.2,greedy
3,50,50,1.8,earnings_max
4,60,40,1.4,lazy
5,30,70,1.6,greedy
```

```python
def load_drivers_from_csv_with_behaviour(filepath):
    drivers = []
    with open(filepath, 'r') as f:
        for line in f:
            id, x, y, speed, behaviour_name = parse_csv_line(line)
            
            if behaviour_name == 'lazy':
                behaviour = LazyBehaviour(idle_ticks_needed=5)
            elif behaviour_name == 'greedy':
                behaviour = GreedyDistanceBehaviour(max_distance=10.0)
            elif behaviour_name == 'earnings_max':
                behaviour = EarningsMaxBehaviour(min_reward_per_time=0.8)
            else:
                behaviour = LazyBehaviour(idle_ticks_needed=5)  # Default
            
            driver = Driver(
                id=id,
                position=Point(x, y),
                speed=speed,
                behaviour=behaviour
            )
            drivers.append(driver)
    
    return drivers

# Result (from CSV example above):
# LazyBehaviour: 2/5 = 40%
# GreedyDistanceBehaviour: 2/5 = 40%
# EarningsMaxBehaviour: 1/5 = 20%
```

**Likelihood Distribution (from CSV file above):**
- LazyBehaviour: 40% (2/5)
- GreedyDistanceBehaviour: 40% (2/5)
- EarningsMaxBehaviour: 20% (1/5)

### Strategy 2: Distribution Parameter in Config

Define probability distribution, apply to all CSV drivers:

```python
INITIAL_BEHAVIOUR_DISTRIBUTION = {
    'lazy': 0.3,
    'greedy': 0.5,
    'earnings_max': 0.2,
}

def load_drivers_from_csv_with_distribution(filepath, distribution):
    drivers = []
    with open(filepath, 'r') as f:
        for line in f:
            id, x, y, speed = parse_csv_line(line)
            
            # Sample behaviour from distribution
            behaviour_name = random.choices(
                list(distribution.keys()),
                weights=list(distribution.values()),
                k=1
            )[0]
            
            if behaviour_name == 'lazy':
                behaviour = LazyBehaviour(idle_ticks_needed=5)
            elif behaviour_name == 'greedy':
                behaviour = GreedyDistanceBehaviour(max_distance=10.0)
            else:
                behaviour = EarningsMaxBehaviour(min_reward_per_time=0.8)
            
            driver = Driver(
                id=id,
                position=Point(x, y),
                speed=speed,
                behaviour=behaviour
            )
            drivers.append(driver)
    
    return drivers

# With 5 drivers and distribution above:
# Expected: ~1-2 lazy, ~2-3 greedy, ~1 earnings_max
```

**Likelihood Distribution (Expected):**
- LazyBehaviour: 30%
- GreedyDistanceBehaviour: 50%
- EarningsMaxBehaviour: 20%

### Strategy 3: Parameter Columns in CSV

Include behaviour-specific parameters:

```csv
id,x,y,speed,behaviour,param1,param2
1,10,20,1.5,lazy,5,5.0
2,15,25,1.2,greedy,10.0,0
3,50,50,1.8,earnings_max,0,0.8
4,60,40,1.4,lazy,3,5.0
5,30,70,1.6,greedy,15.0,0
```

```python
def load_drivers_csv_with_parameters(filepath):
    drivers = []
    with open(filepath, 'r') as f:
        for line in f:
            id, x, y, speed, behaviour_name, param1, param2 = parse_csv_line(line)
            
            if behaviour_name == 'lazy':
                behaviour = LazyBehaviour(idle_ticks_needed=int(param1))
            elif behaviour_name == 'greedy':
                behaviour = GreedyDistanceBehaviour(max_distance=float(param1))
            elif behaviour_name == 'earnings_max':
                behaviour = EarningsMaxBehaviour(min_reward_per_time=float(param2))
            
            driver = Driver(
                id=id,
                position=Point(x, y),
                speed=speed,
                behaviour=behaviour
            )
            drivers.append(driver)
    
    return drivers

# Result:
# Driver 1: LazyBehaviour(idle_ticks_needed=5)
# Driver 2: GreedyDistanceBehaviour(max_distance=10.0)
# Driver 3: EarningsMaxBehaviour(min_reward_per_time=0.8)
# Driver 4: LazyBehaviour(idle_ticks_needed=3) - DIFFERENT PARAMETER
# Driver 5: GreedyDistanceBehaviour(max_distance=15.0) - DIFFERENT PARAMETER
```

**Likelihood Distribution (from CSV above):**
- LazyBehaviour: 40% (2/5)
- GreedyDistanceBehaviour: 40% (2/5)
- EarningsMaxBehaviour: 20% (1/5)

**Parameter Variation:**
- LazyBehaviour: Parameters [5, 3] (idle ticks needed varies)
- GreedyDistanceBehaviour: Parameters [10.0, 15.0] (max distance varies)
- EarningsMaxBehaviour: Parameters [0.8] (same)

---

## Part 4: Recommended Assignment Strategy

### For Programmatic Use (Tests, Experiments)

```python
# Use explicit, controlled assignment
DRIVER_CONFIGS = [
    ('lazy', {'idle_ticks_needed': 5}),
    ('greedy', {'max_distance': 10.0}),
    ('earnings_max', {'min_reward_per_time': 0.8}),
]

drivers = []
for i, (behaviour_type, params) in enumerate(DRIVER_CONFIGS):
    if behaviour_type == 'lazy':
        behaviour = LazyBehaviour(**params)
    elif behaviour_type == 'greedy':
        behaviour = GreedyDistanceBehaviour(**params)
    else:
        behaviour = EarningsMaxBehaviour(**params)
    
    driver = Driver(
        id=i,
        position=Point(50, 50),
        speed=1.5,
        behaviour=behaviour
    )
    drivers.append(driver)

# Result: Predictable, reproducible, one of each behaviour type
```

**Likelihood Distribution:**
- LazyBehaviour: 33.3%
- GreedyDistanceBehaviour: 33.3%
- EarningsMaxBehaviour: 33.3%

### For CSV Use (GUI, Experiments)

```python
# Option A: Current approach (simplest)
# All CSV drivers get LazyBehaviour(idle_ticks_needed=5)
# Mutations will diversify the fleet as simulation runs

# Option B: Add behaviour column (recommended)
# Allows fine-grained control without code changes
# CSV: id, x, y, speed, behaviour

# Option C: Use weighted distribution
# All CSV drivers sampled from: 60% greedy, 30% lazy, 10% earnings_max
# Reflects realistic "new driver" fleet composition
```

---

## Part 5: Impact of Initial Distribution

### Scenario A: All LazyBehaviour

```
Tick 0:
  behaviour_distribution = {'LazyBehaviour': 10}

Tick 50:
  behaviour_distribution = {'LazyBehaviour': 6, 'GreedyDistanceBehaviour': 3, 'EarningsMaxBehaviour': 1}
  
Tick 200:
  behaviour_distribution = {'LazyBehaviour': 2, 'GreedyDistanceBehaviour': 5, 'EarningsMaxBehaviour': 3}
```

**Observations:**
- Fleet starts homogeneous (all same behaviour)
- Mutations gradually diversify the population
- Better-adapted behaviours (based on earnings) accumulate
- Shows how policy + mutations creates diversity

---

### Scenario B: 33% Each Behaviour

```
Tick 0:
  behaviour_distribution = {'LazyBehaviour': 3, 'GreedyDistanceBehaviour': 3, 'EarningsMaxBehaviour': 4}

Tick 50:
  behaviour_distribution = {'LazyBehaviour': 2, 'GreedyDistanceBehaviour': 5, 'EarningsMaxBehaviour': 3}

Tick 200:
  behaviour_distribution = {'LazyBehaviour': 1, 'GreedyDistanceBehaviour': 6, 'EarningsMaxBehaviour': 3}
```

**Observations:**
- Fleet starts diverse (mixed initial strategies)
- Mutations reinforce successful behaviours
- Greedy might dominate (most adaptable under given policy)
- Shows whether diversity helps or hinders

---

### Scenario C: 60% Greedy, 30% Lazy, 10% EarningsMax

```
Tick 0:
  behaviour_distribution = {'GreedyDistanceBehaviour': 6, 'LazyBehaviour': 3, 'EarningsMaxBehaviour': 1}

Tick 50:
  behaviour_distribution = {'GreedyDistanceBehaviour': 5, 'LazyBehaviour': 3, 'EarningsMaxBehaviour': 2}

Tick 200:
  behaviour_distribution = {'GreedyDistanceBehaviour': 4, 'LazyBehaviour': 2, 'EarningsMaxBehaviour': 4}
```

**Observations:**
- Fleet starts realistic (new drivers mostly greedy)
- Mutations help specialization (EarningsMax grows to 4)
- Greedy decreases as mutations find better fits
- Shows realistic "new worker" → "experienced worker" progression

---

## Part 6: Summary Table

### Current Implementation

| Source | Method | LazyBehaviour | GreedyDistanceBehaviour | EarningsMaxBehaviour |
|--------|--------|---|---|---|
| **Programmatic** | Explicit per-driver | Varies (user choice) | Varies (user choice) | Varies (user choice) |
| **CSV** | Default | 100% | 0% | 0% |

### Recommended Strategies

| Source | Method | LazyBehaviour | GreedyDistanceBehaviour | EarningsMaxBehaviour | Use Case |
|--------|--------|---|---|---|---|
| **Programmatic** | Uniform | 100% | 0% | 0% | Test single behaviour |
| **Programmatic** | Proportional (round-robin) | 33.3% | 33.3% | 33.3% | Test behaviour interaction |
| **Programmatic** | Random uniform | ~33% | ~33% | ~33% | Stochastic baseline |
| **Programmatic** | Weighted random | Configurable | Configurable | Configurable | Realistic fleet mix |
| **CSV** | Current (default) | 100% | 0% | 0% | Simple baseline |
| **CSV** | Column-based | Per-row | Per-row | Per-row | Fine-grained control |
| **CSV** | Config distribution | Configurable | Configurable | Configurable | Reproducible mix |
| **CSV** | Parameter columns | Per-row configurable | Per-row configurable | Per-row configurable | Full customization |

---

## Part 7: Configuration for Your Paper

### Recommended Initial Distributions for Experiments

#### Experiment 1: Behaviour Isolation
Test each behaviour independently to understand strengths/weaknesses:
```python
# Run 3 separate simulations, each with uniform fleet
configs = [
    {'name': 'all_lazy', 'distribution': {'lazy': 1.0}},
    {'name': 'all_greedy', 'distribution': {'greedy': 1.0}},
    {'name': 'all_earnings_max', 'distribution': {'earnings_max': 1.0}},
]
```

**Likelihood Distributions:**
- Experiment 1: 100% LazyBehaviour
- Experiment 2: 100% GreedyDistanceBehaviour
- Experiment 3: 100% EarningsMaxBehaviour

#### Experiment 2: Balanced Fleet
Test how diversity affects outcomes:
```python
configs = [
    {'name': 'uniform_mix', 'distribution': {
        'lazy': 0.333,
        'greedy': 0.333,
        'earnings_max': 0.334,
    }},
]
```

**Likelihood Distribution:**
- LazyBehaviour: 33.3%
- GreedyDistanceBehaviour: 33.3%
- EarningsMaxBehaviour: 33.4%

#### Experiment 3: Realistic Fleet
Simulate real driver population (mostly new, some experienced):
```python
configs = [
    {'name': 'realistic', 'distribution': {
        'lazy': 0.2,        # 20% - Veteran selective
        'greedy': 0.6,      # 60% - New/pragmatic
        'earnings_max': 0.2, # 20% - Experienced optimizer
    }},
]
```

**Likelihood Distribution:**
- LazyBehaviour: 20%
- GreedyDistanceBehaviour: 60%
- EarningsMaxBehaviour: 20%

---

## Conclusion

### Key Points

1. **Programmatic Creation:** Full control, choose explicitly for each driver
2. **CSV Loading:** Currently defaults to LazyBehaviour for all
3. **Strategies:** Uniform, proportional, random, or weighted
4. **Impact:** Initial distribution affects fleet diversity and evolution
5. **Mutations:** Will reshape distribution as simulation runs
6. **Recommendation:** Use weighted distribution (60% greedy, 30% lazy, 10% earnings_max) for realistic scenarios

### For Your Paper

Clearly specify:
- Which assignment strategy you used for experiments
- Initial behaviour distribution percentages
- How mutations changed distribution over time
- Whether mutation improved service levels compared to static initial distribution
