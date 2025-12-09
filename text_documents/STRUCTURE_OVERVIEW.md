# Complete Project Structure Overview

## Project Layout

```
exam_phase2/
│
├── 📄 dispatch_ui.py                 ⭐ ENTRY POINT (Teacher-provided, slightly modified)
├── 📄 RECOMMENDED_STRUCTURE.md       📋 This guide
│
├── 📁 gui/                           👨‍💼 Teacher's GUI Engine (DO NOT MODIFY)
│   ├── _engine.py                    - Handles visualization & event loop
│   └── __pycache__/
│
├── 📁 phase1/                        🔧 PHASE 1 - Procedural Backend (Improved)
│   ├── __init__.py
│   ├── io_mod.py                     📥 Load/generate drivers & requests
│   ├── sim_mod.py                    ⚙️ Simulation step & state init
│   ├── help_functions.py             🛠️ Helper utilities
│   └── __pycache__/
│
├── 📁 phase2/                        🎯 PHASE 2 - Object-Oriented Backend (New)
│   │
│   ├── __init__.py                   (empty or imports)
│   │
│   ├── 📁 core/                      🏗️ CORE DOMAIN CLASSES
│   │   ├── __init__.py
│   │   ├── point.py                  📍 Point(x, y) - geometric operations
│   │   ├── request.py                📦 Request - food delivery order
│   │   └── driver.py                 🚗 Driver - active agent with behaviour
│   │
│   ├── 📁 policies/                  🎲 DISPATCH POLICIES
│   │   ├── __init__.py
│   │   ├── base.py                   📋 DispatchPolicy (abstract)
│   │   ├── nearest_neighbor.py       👥 Greedy nearest-neighbor assignment
│   │   └── global_greedy.py          🌐 Global greedy matching
│   │
│   ├── 📁 behaviours/                🧠 DRIVER BEHAVIOUR
│   │   ├── __init__.py
│   │   ├── base.py                   📋 DriverBehaviour (abstract)
│   │   ├── greedy_distance.py        📏 Accept if close enough
│   │   ├── earnings_max.py           💰 Accept if reward/time ratio high
│   │   └── lazy.py                   😴 Accept only if idle & close
│   │
│   ├── 📁 mutations/                 🧬 BEHAVIOUR MUTATIONS
│   │   ├── __init__.py
│   │   ├── base.py                   📋 MutationRule (abstract)
│   │   ├── performance_based.py      📊 Mutate based on earnings/trips
│   │   └── exploration.py            🎲 Random behaviour switching
│   │
│   ├── 📁 engine/                    ⚡ SIMULATION ENGINE
│   │   ├── __init__.py
│   │   ├── offer.py                  💌 Offer data class
│   │   ├── generator.py              🎪 RequestGenerator - stochastic arrivals
│   │   └── simulation.py             🎬 DeliverySimulation - main orchestrator
│   │
│   ├── adapter.py                    🔌 GUI ADAPTER - Bridges OOP ↔ Procedural
│   │
│   ├── reporting.py                  📊 POST-SIM METRICS & PLOTS
│   │
│   └── __pycache__/
│
├── 📁 test/                          ✅ UNIT TESTS (Required for Phase 2)
│   ├── __init__.py
│   ├── test_point.py                 🧪 Test Point class & operations
│   ├── test_request.py               🧪 Test Request lifecycle
│   ├── test_driver.py                🧪 Test Driver movement & assignment
│   ├── test_policies.py              🧪 Test dispatch policies
│   ├── test_behaviours.py            🧪 Test driver behaviours
│   ├── test_simulation.py            🧪 Test full DeliverySimulation
│   └── __pycache__/
│
└── [Legacy: io_mod.py, sim_mod.py at root - for backward compatibility]
```

---

# Detailed Module Reference

## 🎯 **Entry Point: `dispatch_ui.py`**

**Purpose:** Launcher that tries Phase 2 first, falls back to Phase 1.

**What it does:**
1. Imports and calls `create_phase2_backend()` from `phase2/adapter.py`
2. Falls back to Phase 1 if Phase 2 unavailable
3. Passes backend dict to `gui._engine.run_app()`
4. Calls reporting functions after GUI closes

**Key section to modify (at end):**
```python
if __name__ == "__main__":
    try:
        from phase2.adapter import create_phase2_backend
        _backend = create_phase2_backend()
    except Exception:
        try:
            from phase1 import io_mod, sim_mod
            _backend = {...}  # Phase 1 backend
        except Exception:
            _backend = None
    
    main(_backend)
    
    # After GUI closes, show metrics
    if _backend is not None and hasattr(_backend, 'get_report_data'):
        from phase2.reporting import show_report
        show_report(_backend.get_report_data())
```

---

## 🏗️ **Phase 2: Core Domain Classes** (`phase2/core/`)

### `point.py`
**Class:** `Point`

**Responsibility:** Geometric position with operations.

**Attributes:**
- `x: float`
- `y: float`

**Methods:**
```python
distance_to(other: Point) -> float          # Euclidean distance
__add__(other: Point) -> Point              # p1 + p2
__sub__(other: Point) -> Point              # p1 - p2
__iadd__(other: Point) -> Point             # p1 += p2
__isub__(other: Point) -> Point             # p1 -= p2
__mul__(scalar: float|int) -> Point         # p * 2
__rmul__(scalar: float|int) -> Point        # 2 * p
```

**Usage in simulation:**
```python
driver.position += direction * speed  # Move driver
```

---

### `request.py`
**Class:** `Request`

**Responsibility:** Represents a food delivery order.

**Attributes:**
- `id: int` - Unique identifier
- `pickup: Point` - Where to pick up food
- `dropoff: Point` - Where to deliver
- `creation_time: int` - When request appeared (simulation tick)
- `status: str` - One of: `WAITING`, `ASSIGNED`, `PICKED`, `DELIVERED`, `EXPIRED`
- `assigned_driver_id: int | None` - Currently assigned driver
- `wait_time: int` - Time spent in system

**Methods:**
```python
is_active() -> bool                     # Status in {WAITING, ASSIGNED, PICKED}?
mark_assigned(driver_id: int) -> None   # Change status to ASSIGNED
mark_picked(current_time: int) -> None  # Change status to PICKED
mark_delivered(current_time: int) -> None  # Change status to DELIVERED, record wait
mark_expired(current_time: int) -> None # Change status to EXPIRED
update_wait(current_time: int) -> None  # Update wait_time counter
```

**Lifecycle:**
```
WAITING → ASSIGNED → PICKED → DELIVERED
                    ↓
                 EXPIRED (if timeout exceeded)
```

---

### `driver.py`
**Class:** `Driver`

**Responsibility:** Active agent that moves, accepts offers, completes deliveries.

**Attributes:**
- `id: int` - Unique identifier
- `position: Point` - Current location
- `speed: float` - Units per tick
- `status: str` - One of: `IDLE`, `TO_PICKUP`, `TO_DROPOFF`
- `current_request: Request | None` - Currently assigned order
- `behaviour: DriverBehaviour` - Decision policy
- `history: list[dict]` - Completed trips with earnings/times

**Methods:**
```python
assign_request(request: Request, current_time: int) -> None
    # Accept a request, set status to TO_PICKUP

target_point() -> Point | None
    # Return next destination: pickup or dropoff

step(dt: float) -> None
    # Move towards target by dt * speed

complete_pickup(time: int) -> None
    # Update state when pickup reached

complete_dropoff(time: int) -> None
    # Update state & history when dropoff reached

decide_on_offer(offer: Offer, time: int) -> bool
    # Delegate to behaviour.decide()
```

**State transitions:**
```
IDLE  → TO_PICKUP → TO_DROPOFF → IDLE
        (when pickup reached)
                   (when dropoff reached)
```

---

## 🎲 **Phase 2: Policies** (`phase2/policies/`)

### `base.py`
**Class:** `DispatchPolicy` (abstract)

**Responsibility:** Define interface for assignment strategy.

```python
class DispatchPolicy(ABC):
    @abstractmethod
    def assign(self, drivers: list[Driver], requests: list[Request], 
               time: int) -> list[tuple[Driver, Request]]:
        """
        Given available drivers and waiting requests, return list of 
        (driver, request) pairs to propose. Multiple drivers may be 
        assigned to same request (conflict resolved in simulation).
        """
        pass
```

---

### `nearest_neighbor.py`
**Class:** `NearestNeighborPolicy`

**Algorithm:**
1. Find closest idle driver to closest waiting request
2. Assign that pair
3. Repeat until no more idle drivers or waiting requests

**Complexity:** O(n² * m²) - not optimal, but simple.

---

### `global_greedy.py`
**Class:** `GlobalGreedyPolicy`

**Algorithm:**
1. Build all (idle_driver, waiting_request) pairs
2. Calculate distance for each pair
3. Sort by distance (ascending)
4. Greedily assign: pick closest pair, remove both from available, repeat

**Complexity:** O(n*m log(n*m)) - better than nearest neighbor.

---

## 🧠 **Phase 2: Behaviours** (`phase2/behaviours/`)

### `base.py`
**Class:** `DriverBehaviour` (abstract)

**Responsibility:** Encapsulate how a driver accepts/rejects offers.

```python
class DriverBehaviour(ABC):
    @abstractmethod
    def decide(self, driver: Driver, offer: Offer, time: int) -> bool:
        """
        Return True to accept offer, False to reject.
        """
        pass
```

---

### `greedy_distance.py`
**Class:** `GreedyDistanceBehaviour`

**Decision logic:**
```python
def decide(self, driver, offer, time):
    distance = driver.position.distance_to(offer.request.pickup)
    return distance < self.distance_threshold
```

**Interpretation:** Accept if pickup is within threshold distance.

---

### `earnings_max.py`
**Class:** `EarningsMaxBehaviour`

**Decision logic:**
```python
def decide(self, driver, offer, time):
    reward = offer.estimated_reward
    travel_time = offer.estimated_travel_time
    ratio = reward / travel_time if travel_time > 0 else float('inf')
    return ratio > self.earning_threshold
```

**Interpretation:** Accept if reward-per-time ratio exceeds threshold.

---

### `lazy.py`
**Class:** `LazyBehaviour`

**Decision logic:**
```python
def decide(self, driver, offer, time):
    distance = driver.position.distance_to(offer.request.pickup)
    idle_duration = time - driver.last_assignment_time
    return (distance < self.distance_threshold and 
            idle_duration > self.idle_threshold)
```

**Interpretation:** Accept only if close AND driver has been idle long enough.

---

## 🧬 **Phase 2: Mutations** (`phase2/mutations/`)

### `base.py`
**Class:** `MutationRule` (abstract)

**Responsibility:** Decide if/how a driver's behaviour should change.

```python
class MutationRule(ABC):
    @abstractmethod
    def maybe_mutate(self, driver: Driver, time: int) -> None:
        """
        Inspect driver's history. If conditions met, change behaviour 
        (or behaviour parameters) in-place.
        """
        pass
```

---

### `performance_based.py`
**Class:** `PerformanceMutation`

**Logic:**
1. Look at driver's last N completed trips
2. Calculate average earnings
3. If below threshold → switch to greedier behaviour
4. If above threshold → can be more selective

**Example:**
```
Earnings too low for 5 trips → switch from LazyBehaviour to GreedyDistance
Earnings good for 10 trips → can switch to EarningsMax (more selective)
```

---

### `exploration.py`
**Class:** `ExplorationMutation`

**Logic:**
1. With small probability p (e.g., 0.1%), randomly pick new behaviour
2. Allows drivers to "explore" different strategies

**Effect:** Adds stochasticity, prevents getting stuck in poor local optima.

---

## ⚡ **Phase 2: Engine** (`phase2/engine/`)

### `offer.py`
**Class:** `Offer`

**Responsibility:** Data holder for dispatch proposal.

**Attributes:**
- `driver: Driver`
- `request: Request`
- `estimated_travel_time: float` - Distance / speed
- `estimated_reward: float` - Reward model (e.g., distance-based)

**Usage:**
```python
offer = Offer(driver, request, travel_time, reward)
accepts = driver.behaviour.decide(driver, offer, current_time)
```

---

### `generator.py`
**Class:** `RequestGenerator`

**Responsibility:** Stochastically generate new requests each tick.

**Attributes:**
- `rate: float` - Expected requests per tick (e.g., 0.5)
- `next_id: int` - Counter for request IDs
- `width: int, height: int` - Grid bounds
- `rng: random.Random` - Random number generator

**Methods:**
```python
def maybe_generate(self, time: int) -> list[Request]:
    """
    Called each tick. Draws from Poisson distribution with rate λ.
    Returns list of newly created Request objects.
    """
    pass
```

**Stochastic generation:**
- Expected number of requests per tick = `rate`
- Actual number varies: sometimes 0, sometimes 1+, averaged over time

---

### `simulation.py`
**Class:** `DeliverySimulation`

**Responsibility:** Main orchestrator. Coordinates all components. Executes one tick per call.

**Attributes:**
- `time: int` - Current simulation tick
- `drivers: list[Driver]`
- `requests: list[Request]` - All requests (active + completed)
- `dispatch_policy: DispatchPolicy`
- `request_generator: RequestGenerator`
- `mutation_rule: MutationRule`
- `timeout: int` - Max waiting time before expiration
- `served_count, expired_count: int` - Counters
- `served_waits: list[float]` - Waiting times of delivered requests

**Main method:**
```python
def tick(self) -> None:
    """
    Execute one simulation tick:
    
    1. Generate new requests
    2. Mark expired requests (waited > timeout)
    3. Compute dispatch proposals
    4. Convert to offers, ask drivers to decide
    5. Resolve conflicts (multiple drivers accept same request)
    6. Finalize assignments & update request/driver status
    7. Move drivers towards targets
    8. Check for pickup/dropoff completions
    9. Apply mutations to drivers
    10. Increment time
    """
    pass

def get_snapshot(self) -> dict:
    """
    Return GUI-friendly state:
    {
        'drivers': [...],      # Positions, status, etc.
        'requests': [...],     # Positions, status, etc.
        'metrics': {...}       # served, expired, avg_wait
    }
    """
    pass
```

---

## 🔌 **Adapter: `phase2/adapter.py`**

**Responsibility:** Bridge between OOP backend (Phase 2) and procedural GUI interface.

**Key function:**
```python
def create_phase2_backend() -> dict:
    """
    Create all OOP objects, then return dict with procedural interface.
    
    Returns:
    {
        'load_drivers': adapter_load_drivers,
        'load_requests': adapter_load_requests,
        'generate_drivers': adapter_generate_drivers,
        'generate_requests': adapter_generate_requests,
        'init_state': adapter_init_state,
        'simulate_step': adapter_simulate_step,
    }
    """
```

**Adapter functions:**
- `adapter_load_drivers(path: str) -> list[dict]` - Load CSV, return driver dicts
- `adapter_load_requests(path: str) -> list[dict]` - Load CSV, return request dicts
- `adapter_generate_drivers(n, w, h) -> list[dict]` - Random drivers, return dicts
- `adapter_generate_requests(t, out_list, rate, w, h) -> None` - Generate requests, append to list
- `adapter_init_state(drivers, requests, timeout, rate, w, h) -> dict` - Create DeliverySimulation, return state dict
- `adapter_simulate_step(state: dict) -> tuple[dict, dict]` - Call `sim.tick()`, return (updated_state, metrics)

**Internal state (module-level):**
```python
_simulation: DeliverySimulation | None = None

def adapter_init_state(...):
    global _simulation
    _simulation = DeliverySimulation(...)
    return sim_to_state_dict(_simulation)

def adapter_simulate_step(state):
    global _simulation
    _simulation.tick()
    return (sim_to_state_dict(_simulation), get_metrics(_simulation))
```

---

## 📊 **Reporting: `phase2/reporting.py`**

**Responsibility:** Collect metrics during simulation, generate plots post-simulation.

**Key structures:**
```python
class MetricsCollector:
    """Store metrics at each tick for later analysis."""
    def __init__(self):
        self.time_steps = []       # [0, 1, 2, 3, ...]
        self.served_counts = []    # [0, 1, 2, 3, 3, 4, ...]
        self.expired_counts = []   # [0, 0, 0, 1, 1, 1, 2, ...]
        self.avg_waits = []        # [0.0, 2.5, 3.1, 3.0, ...]

def show_report(report_data: dict) -> None:
    """Generate matplotlib plots showing metrics evolution."""
    # Plot 1: Served & Expired over time
    # Plot 2: Average waiting time over time
    # Plot 3: Comparison of policies (if multiple runs)
```

**Called after GUI closes:**
```python
# In dispatch_ui.py
if _backend is not None:
    from phase2.reporting import show_report
    report = _backend.get_report_data()
    show_report(report)
```

---

## ✅ **Tests: `test/`**

**Purpose:** Required for Phase 2. Validate all components work.

### `test_point.py`
- Test distance calculations
- Test vector operations (+, -, *, etc.)

### `test_request.py`
- Test lifecycle transitions (WAITING → ASSIGNED → PICKED → DELIVERED)
- Test expiration
- Test wait_time tracking

### `test_driver.py`
- Test movement towards target
- Test status transitions
- Test assignment

### `test_policies.py`
- Test NearestNeighborPolicy output
- Test GlobalGreedyPolicy output
- Verify no duplicate assignments

### `test_behaviours.py`
- Test GreedyDistance accepts/rejects correctly
- Test EarningsMax threshold logic
- Test LazyBehaviour idle check

### `test_simulation.py`
- Test full tick() execution
- Test metrics collection
- Test state consistency

---

## 🔧 **Phase 1: Improved** (`phase1/`)

For backward compatibility and addressing feedback:

### `io_mod.py`
**Improvements needed:**
- ✅ Validate file exists before reading
- ✅ Type check: convert to int/float, raise error if invalid
- ✅ Provide descriptive error messages
- ✅ Add docstrings

### `sim_mod.py`
**Improvements needed:**
- ✅ Use `req_rate` in simulate_step
- ✅ Fix tolerance check for `at_target` (use epsilon, not `==`)
- ✅ Collect metrics at each step
- ✅ Add docstrings
- ✅ Return proper metrics dict

### `help_functions.py`
**Improvements needed:**
- ✅ Don't modify input parameters
- ✅ Add docstrings

---

# Data Flow Diagram

```
dispatch_ui.py (Entry)
    ↓
phase2/adapter.py (Procedural Interface)
    ↓
phase2/engine/simulation.py (Main Engine)
    ├─→ phase2/core/driver.py (Agents)
    ├─→ phase2/core/request.py (Orders)
    ├─→ phase2/core/point.py (Geometry)
    ├─→ phase2/policies/*.py (Assignment)
    ├─→ phase2/behaviours/*.py (Decisions)
    └─→ phase2/mutations/*.py (Learning)
    ↓
gui/_engine.py (GUI Rendering)
    ↓
User Sees: Drivers, Requests, Metrics on Screen
    ↓
[GUI Closes]
    ↓
phase2/reporting.py (Plots & Analysis)
```

---

# Key Implementation Sequence

1. **phase2/core/** - Implement Point, Request, Driver
2. **phase2/policies/** - Implement DispatchPolicy & concrete classes
3. **phase2/behaviours/** - Implement DriverBehaviour & concrete classes
4. **phase2/mutations/** - Implement MutationRule & concrete classes
5. **phase2/engine/offer.py** - Simple data class
6. **phase2/engine/generator.py** - RequestGenerator
7. **phase2/engine/simulation.py** - DeliverySimulation (uses all above)
8. **phase2/adapter.py** - Bridge to procedural interface
9. **phase2/reporting.py** - Metrics collection & plotting
10. **test/** - Unit tests for validation
11. **phase1/** - Refactor with improvements
12. **dispatch_ui.py** - Modify entry logic (try Phase 2 first)

---

# Running the Project

```bash
# Terminal at exam_phase2/

# Run with GUI
python dispatch_ui.py

# Or explicit module
python -m dispatch_ui

# Run tests
python -m pytest test/ -v

# Run specific test
python -m pytest test/test_point.py -v
```

---

# Summary Table

| Module | Responsibility | Key Classes |
|--------|-----------------|------------|
| `phase2/core/` | Domain models | Point, Request, Driver |
| `phase2/policies/` | Dispatch strategies | DispatchPolicy, NearestNeighbor, GlobalGreedy |
| `phase2/behaviours/` | Driver decisions | DriverBehaviour, GreedyDistance, EarningsMax, Lazy |
| `phase2/mutations/` | Behaviour evolution | MutationRule, PerformanceBased, Exploration |
| `phase2/engine/` | Simulation orchestration | Offer, RequestGenerator, DeliverySimulation |
| `phase2/adapter.py` | GUI interface | create_phase2_backend() |
| `phase2/reporting.py` | Analysis & plots | MetricsCollector, show_report() |
| `test/` | Validation | Unit tests for all components |
| `phase1/` | Legacy support | Improved io_mod, sim_mod, help_functions |

This structure is scalable, testable, and maintainable! 🚀
