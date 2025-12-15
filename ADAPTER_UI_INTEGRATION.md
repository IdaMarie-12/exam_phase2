# Adapter: Bridging the UI and OOP Simulation

## Overview

The **adapter** layer is the critical glue that connects the GUI (which expects a procedural interface) to the Phase 2 OOP simulation. It translates between two different programming paradigms:

- **GUI side:** Procedural functions with plain dictionaries (`dict`)
- **Simulation side:** Object-oriented classes with type safety and encapsulation

Without the adapter, the UI couldn't communicate with the simulation at all. They speak different languages.

---

## Architecture: Translating Between Worlds

```
┌─────────────────────────────────────┐
│   GUI / dispatch_ui.py              │
│   (Expects dict-based backend)      │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │   adapter   │  ◄─── WE ARE HERE
        │ (Translation)│
        └──────┬──────┘
               │
┌──────────────▼──────────────────────┐
│ Phase 2 OOP Simulation              │
│ (Classes: Driver, Request, Point...)│
└─────────────────────────────────────┘
```

The adapter maintains **global state** (`_simulation`, `_time_series`) so the GUI can pass control back and forth repeatedly.

---

## Key Responsibilities

### 1. **Conversion Functions** (Dict ↔ Object)

The adapter provides helper functions to convert between representations:

```python
# Dict → Object conversions
create_driver_from_dict(d)      # dict → Driver object
create_request_from_dict(r)     # dict → Request object

# Object → Dict conversions
request_to_dict(req)            # Request object → dict
sim_to_state_dict(sim)          # Simulation → state dict
```

**Why?** The GUI works with plain dictionaries (simple, serializable). The simulation works with objects (typed, validated, encapsulated). These functions bridge that gap.

### 2. **Initialization** (`init_state`)

When the UI starts a new simulation:

```python
def init_state(drivers_data, requests_data, timeout, req_rate, width, height):
    # Convert dict representations to OOP objects
    drivers = [create_driver_from_dict(d, idx) for idx, d in enumerate(drivers_data)]
    requests = [create_request_from_dict(r) for r in requests_data]
    
    # Create the OOP infrastructure
    policy = GlobalGreedyPolicy()
    mutation_rule = HybridMutation(...)
    generator = RequestGenerator(...)
    
    # Build the simulation engine
    _simulation = DeliverySimulation(drivers, policy, generator, mutation_rule, timeout)
    _simulation.requests = requests
    
    # Initialize metrics tracking
    _time_series = SimulationTimeSeries()
    
    return sim_to_state_dict(_simulation)
```

Key decisions hardcoded here:
- Always use `GlobalGreedyPolicy` (not NearestNeighborPolicy)
- Always use `HybridMutation` with fixed thresholds
- Decide whether to generate requests dynamically or use loaded CSV

### 3. **Stepping** (`simulate_step`)

Each time the UI calls step:

```python
def simulate_step(state: dict):
    # Advance OOP simulation by one tick
    _simulation.tick()
    
    # Extract metrics from OOP objects
    metrics = get_adapter_metrics(_simulation)
    
    # Record time-series data
    _time_series.record(_simulation.time, metrics)
    
    # Convert state back to dict for UI
    new_state = sim_to_state_dict(_simulation)
    
    return (new_state, metrics)
```

**The flow:** GUI calls step → Adapter advances simulation → Adapter extracts data → GUI renders visualization.

### 4. **Request Generation** (`generate_requests`)

Wraps Phase 2's `RequestGenerator`:

```python
def generate_requests(start_t, out_list, req_rate, width, height):
    gen = RequestGenerator(rate=req_rate, width=width, height=height)
    new_requests = gen.maybe_generate(start_t)
    
    for req in new_requests:
        out_list.append(request_to_dict(req))  # Convert to dict for UI
```

---

## Data Flow Example: One Complete Tick

```
1. GUI calls simulate_step(current_state)
                    │
                    ▼
2. Adapter unpacks state (drivers, requests, etc.)
                    │
                    ▼
3. Adapter calls _simulation.tick()
   Inside tick():
   - Phase 1: Generate new requests (returns Request objects)
   - Phase 2-9: Run 9-phase orchestration on OOP objects
                    │
                    ▼
4. Adapter extracts metrics from OOP simulation
   - Driver positions, earnings, statuses
   - Request locations, statuses, wait times
                    │
                    ▼
5. Adapter converts state to dicts
   - Driver(id=1, position=Point(5, 10)) → {"id": 1, "x": 5, "y": 10, ...}
                    │
                    ▼
6. Adapter records time-series data for post-simulation reporting
                    │
                    ▼
7. Return (new_state_dict, metrics_dict) to GUI
                    │
                    ▼
8. GUI renders visualization from dicts
```

---

## Module-Level State

The adapter maintains persistent state across calls:

```python
_simulation: DeliverySimulation | None = None
_time_series: SimulationTimeSeries | None = None
```

**Why module-level?** The GUI is stateless—it calls adapter functions sequentially. Between calls, the adapter needs to remember the current simulation and metrics. These globals are the "memory" of the running simulation.

---

## Helper Functions (Imported from Engine Helpers)

The adapter imports conversion utilities from [engine_helpers.py](phase2/helpers_2/engine_helpers.py):

```python
from .helpers_2.engine_helpers import (
    sim_to_state_dict,           # Simulation → GUI state
    get_adapter_metrics,         # Simulation → metrics
    create_driver_from_dict,     # Dict → Driver
    create_request_from_dict,    # Dict → Request
    request_to_dict,             # Request → dict
    get_plot_data_from_state,    # State → plot tuples
)
```

These functions handle all the mechanical conversion work, keeping the adapter clean and focused.

---

## Why This Architecture Makes Sense

1. **Separation of Concerns:**
   - GUI doesn't need to know about OOP internals
   - Simulation doesn't need to know about the GUI
   - Adapter handles translation in one place

2. **Flexibility:**
   - Could swap policies/mutations without changing UI code
   - Could use different backends (not just Phase 2)
   - Could test simulation independently from GUI

3. **Testing:**
   - Test adapter functions with mock data
   - Test simulation with OOP objects directly
   - Test GUI with mock adapter responses

4. **Maintainability:**
   - All conversion logic in one file
   - Clear handoff points between procedural and OOP
   - Easy to trace data flow end-to-end

---

## Common Pitfalls

**1. Forgetting to convert types:**
```python
# ❌ Wrong: Simulation needs Point, not dict
driver.position = {"x": 5, "y": 10}

# ✓ Right: Use constructor
driver.position = Point(5, 10)
```

**2. Not updating global state:**
```python
# ❌ Wrong: Creates local simulation, UI never sees it
sim = DeliverySimulation(...)

# ✓ Right: Update module-level reference
global _simulation
_simulation = DeliverySimulation(...)
```

**3. Forgetting to record metrics:**
```python
# ❌ Wrong: Post-simulation reporting fails
_simulation.tick()
return sim_to_state_dict(_simulation)

# ✓ Right: Record for reporting
_simulation.tick()
_time_series.record(_simulation.time, metrics)
return sim_to_state_dict(_simulation)
```

---

## Summary

The adapter is a **thin but essential translation layer**:

- **Input:** Procedural dict-based calls from GUI
- **Process:** Convert to OOP objects, run simulation, extract results
- **Output:** Procedural dict-based results back to GUI

It's the bridge that lets the GUI talk to an object-oriented simulation without either one needing to know about the other's internal structure.
