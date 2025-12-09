# Recommended File Structure for Phase 2

## Overview
The structure maintains **full compatibility** with `dispatch_ui.py` while organizing Phase 2's OOP code cleanly and allowing Phase 1 improvements.

---

## Directory Tree

```
exam_phase2/
│
├── dispatch_ui.py                    # [TEACHER PROVIDED - DO NOT MODIFY]
│                                      # We can add code AFTER the `if __name__ == "__main__"` block
│
├── gui/                              # [TEACHER PROVIDED]
│   ├── _engine.py
│   └── __pycache__/
│
├── phase1/                           # [IMPROVED PHASE 1]
│   ├── __init__.py
│   ├── io_mod.py                     # Load/save drivers & requests
│   ├── sim_mod.py                    # simulate_step, init_state logic
│   ├── help_functions.py             # Helper functions
│   └── __pycache__/
│
├── phase2/                           # [NEW PHASE 2 - MAIN MODULE]
│   ├── __init__.py                   # Empty or minimal imports
│   │
│   ├── core/                         # Core domain classes
│   │   ├── __init__.py
│   │   ├── point.py                  # Point class
│   │   ├── request.py                # Request class
│   │   └── driver.py                 # Driver class
│   │
│   ├── policies/                     # Dispatch policies
│   │   ├── __init__.py
│   │   ├── base.py                   # DispatchPolicy abstract base
│   │   ├── nearest_neighbor.py       # NearestNeighborPolicy
│   │   └── global_greedy.py          # GlobalGreedyPolicy
│   │
│   ├── behaviours/                   # Driver behaviour classes
│   │   ├── __init__.py
│   │   ├── base.py                   # DriverBehaviour abstract base
│   │   ├── greedy_distance.py        # GreedyDistanceBehaviour
│   │   ├── earnings_max.py           # EarningsMaxBehaviour
│   │   └── lazy.py                   # LazyBehaviour
│   │
│   ├── mutations/                    # Mutation rules
│   │   ├── __init__.py
│   │   ├── base.py                   # MutationRule abstract base
│   │   ├── performance_based.py      # Performance-based mutation
│   │   └── exploration.py            # Exploration-based mutation
│   │
│   ├── engine/                       # Simulation engine
│   │   ├── __init__.py
│   │   ├── offer.py                  # Offer class
│   │   ├── generator.py              # RequestGenerator class
│   │   └── simulation.py             # DeliverySimulation class
│   │
│   ├── adapter.py                    # GUI adapter functions
│   │
│   ├── reporting.py                  # Post-simulation metrics & plotting
│   │
│   └── __pycache__/
│
├── test/                             # Unit tests
│   ├── __init__.py
│   ├── test_point.py                 # Test Point class
│   ├── test_request.py               # Test Request class
│   ├── test_driver.py                # Test Driver class
│   ├── test_policies.py              # Test dispatch policies
│   ├── test_behaviours.py            # Test driver behaviours
│   ├── test_simulation.py            # Test DeliverySimulation
│   └── __pycache__/
│
└── [Other existing files: io_mod.py, sim_mod.py, etc.]
```

---

## Key Design Decisions

### 1. **Maintain `dispatch_ui.py` Compatibility**

The current `dispatch_ui.py` tries to import from Phase 1:
```python
if __name__ == "__main__":
    try:
        from phase1 import io_mod, sim_mod
        _backend = {...}
    except Exception:
        _backend = None
    main(_backend)
```

**We need to MODIFY this to also try Phase 2:**

```python
if __name__ == "__main__":
    try:
        from phase2.adapter import create_phase2_backend
        _backend = create_phase2_backend()
    except Exception:
        try:
            from phase1 import io_mod, sim_mod
            _backend = {...}
        except Exception:
            _backend = None
    main(_backend)
```

### 2. **Core Domain Organization** (`phase2/core/`)

Separates **data models** from **logic**:
- `point.py` - Simple value class with geometric operations
- `request.py` - Immutable request representation
- `driver.py` - Active agent with behaviour policy

**Benefit:** These can be tested independently.

### 3. **Policy Pattern** (`phase2/policies/`, `phase2/behaviours/`, `phase2/mutations/`)

Each concept (dispatch, driver behaviour, mutation) is:
- An **abstract base class** defining the interface
- Multiple **concrete implementations** as separate files
- Easy to extend without modifying existing code

**Benefit:** Clean separation of concerns, testable, maintainable.

### 4. **Engine Layer** (`phase2/engine/`)

Contains orchestration:
- `offer.py` - Simple data holder
- `generator.py` - Request generation logic
- `simulation.py` - Main `DeliverySimulation` class

The `simulation.py` is the **heart** that coordinates all components.

**Benefit:** Single responsibility for the main simulation loop.

### 5. **Adapter Pattern** (`phase2/adapter.py`)

Translates between:
- **GUI requirements** (procedural dict-based interface from Phase 1)
- **OOP architecture** (objects and classes in Phase 2)

Provides the backend dict that `dispatch_ui.py` expects:
```python
def create_phase2_backend():
    """Returns dict with keys: load_drivers, load_requests, ..., simulate_step"""
    return {
        "load_drivers": adapter_load_drivers,
        "load_requests": adapter_load_requests,
        "generate_drivers": adapter_generate_drivers,
        "generate_requests": adapter_generate_requests,
        "init_state": adapter_init_state,
        "simulate_step": adapter_simulate_step,
    }
```

**Benefit:** GUI doesn't change; we control the implementation.

### 6. **Reporting** (`phase2/reporting.py`)

Collects and visualizes metrics post-simulation:
- Store metrics at each step during `tick()`
- Generate plots after GUI closes
- Compare different policies/behaviours

**Benefit:** Validates correctness and demonstrates design.

### 7. **Tests** (`test/`)

Comprehensive unit tests for:
- Individual classes (`Point`, `Request`, `Driver`)
- Policies and behaviours
- Full simulation scenarios

**Benefit:** Required for Phase 2; ensures correctness.

---

## Phase 1 Improvements (in `phase1/`)

To address feedback, improve:

1. **`io_mod.py`**
   - Add proper error handling for file existence
   - Validate types (int, float, str)
   - Raise descriptive exceptions

2. **`sim_mod.py`**
   - Use `req_rate` in `simulate_step`
   - Fix tolerance check for `at_target`
   - Include comprehensive docstrings
   - Collect and return metrics properly

3. **`help_functions.py`**
   - Don't modify input parameters
   - Add docstrings

---

## How dispatch_ui.py Works With This Structure

```
dispatch_ui.py
    │
    ├─→ phase2/adapter.py (create_phase2_backend)
    │   └─→ Returns dict with 6 functions
    │
    └─→ gui/_engine.py (run_app)
        └─→ Calls backend functions with state dicts
            └─→ Internally calls OOP classes
```

**User experience:** Same visual result, cleaner code underneath.

---

## Module Import Pattern

**In `phase2/adapter.py`:**
```python
from phase2.core.point import Point
from phase2.core.request import Request
from phase2.core.driver import Driver
from phase2.engine.simulation import DeliverySimulation
from phase2.policies.nearest_neighbor import NearestNeighborPolicy
from phase2.behaviours.greedy_distance import GreedyDistanceBehaviour
from phase2.mutations.performance_based import PerformanceMutation
from phase2.engine.generator import RequestGenerator

# Create OOP objects, then expose procedural interface for GUI
```

---

## File Implementation Order

1. **Core domain** (`point.py`, `request.py`, `driver.py`)
2. **Policies** (base + concrete implementations)
3. **Behaviours** (base + concrete implementations)
4. **Mutations** (base + concrete implementations)
5. **Engine** (`offer.py`, `generator.py`, `simulation.py`)
6. **Adapter** (tie everything together)
7. **Reporting** (metrics and plots)
8. **Tests** (cover all components)
9. **Phase 1 improvements** (refactor for better error handling)

---

## Summary Table

| Component | Location | Purpose |
|-----------|----------|---------|
| Point, Request, Driver | `phase2/core/` | Domain models |
| Dispatch strategies | `phase2/policies/` | How to assign drivers to requests |
| Driver decision logic | `phase2/behaviours/` | How drivers accept/reject offers |
| Behaviour changes | `phase2/mutations/` | How drivers evolve |
| Simulation orchestration | `phase2/engine/simulation.py` | Main loop |
| GUI translation | `phase2/adapter.py` | Procedural interface for GUI |
| Analysis | `phase2/reporting.py` | Metrics and plots |
| Validation | `test/` | Unit tests |

---

## To Make This Work

1. Create the directory structure above
2. Implement classes in each module
3. **Modify `dispatch_ui.py` bottom section** to try Phase 2 first
4. Run `python dispatch_ui.py` or `python -m dispatch_ui`

The GUI will automatically use Phase 2 if available, otherwise fall back to Phase 1.
