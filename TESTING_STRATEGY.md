# Testing Strategy for Phase 2 Simulation Project

## Overview

This document provides recommendations on where to use **unittest**, **mocking**, and **patch** in the Phase 2 simulation codebase based on testing best practices and the complexity of dependencies in the project.

---

## 1. UNITTEST Candidates - Core Unit Tests

These components should be tested with basic unittest (straightforward, deterministic behavior):

### 1.1 Point Class (`phase2/point.py`)
**Why Unit Test:**
- Mathematical operations (distance calculations, coordinate transformations)
- Pure functions with no side effects
- Input → Output validation
- Predictable results independent of system state

**What to Test:**
```
✓ distance_to(other) - Calculate Euclidean distance
✓ __add__, __sub__, __mul__ - Arithmetic operations
✓ Boundary conditions (negative coordinates, zero distance)
✓ Type validation (TypeError scenarios)
```

**Complexity:** Low - No dependencies, deterministic
**Test Type:** Unit Test (simple assertions)

---

### 1.2 Request Class (`phase2/request.py`)
**Why Unit Test:**
- State initialization and transitions
- Timestamp calculations
- Expiration logic (time-based but mockable)
- Simple getters/setters

**What to Test:**
```
✓ Request creation with valid parameters
✓ Request expiration checking (is_expired())
✓ Pickup/Dropoff point validation
✓ Distance calculation to destinations
```

**Complexity:** Low-Medium
**Test Type:** Unit Test
**Mocking Needed:** Time/datetime for expiration tests (USE MOCK)

---

### 1.3 Offer Class (`phase2/offer.py`)
**Why Unit Test:**
- Simple data container for assignment proposals
- Trip metrics calculations
- Earnings/points computations

**What to Test:**
```
✓ Offer creation and property access
✓ Trip cost calculations
✓ Earnings/points estimations
✓ Offer comparison (is offer X better than offer Y?)
```

**Complexity:** Low
**Test Type:** Unit Test

---

## 2. MOCKING - Where External Dependencies Exist

### 2.1 Driver Class (`phase2/driver.py`) - CRITICAL FOR MOCKING

**Why Mock:**
- Multiple dependencies: Request objects, Offer objects, geometry helper functions
- State mutations (position changes, earnings tracking)
- Side effects (recording trip completion, updating driver state)
- Trip simulation depends on timing and sequencing

**What to Mock:**
```
✓ Request objects (pickup/dropoff locations)
✓ core_helpers functions:
  - is_at_target() - Return True/False as needed
  - move_towards() - Control position updates
  - calculate_points() - Return fixed point values
  - record_assignment_start() - Track calls
  - record_completion() - Track completion events
  - finalize_trip() - Verify earnings updated correctly

✓ Random behavior (driver decision-making):
  - Deterministic choice selection in behaviors
  - Side effect on driver state
```

**Test Scenarios Using Mocks:**
```
1. Driver.step() behavior:
   - Mock is_at_target() to return True → verify move_towards() called
   - Mock is_at_target() to return False → verify stays in transit
   
2. Driver.assign_request() validation:
   - Mock Request with specific pickup/dropoff
   - Verify core_helpers.record_assignment_start() called correctly
   - Verify internal state updated
   
3. Driver.complete_dropoff() logic:
   - Mock finalize_trip() to verify correct earnings/points passed
   - Mock record_completion() to verify event logged
   - Verify state reset for next assignment
```

**Complexity:** High - Multiple side effects
**Test Type:** Unit Test with Mocking

---

### 2.2 Simulation Class (`phase2/simulation.py`) - HEAVY MOCKING NEEDED

**Why Mock:**
- Orchestrates entire system (drivers, requests, adapter)
- Time/state progression (tick simulation)
- Multiple interacting components
- Hard to test real interactions without integration tests

**What to Mock:**
```
✓ Driver objects and their methods:
  - driver.step() behavior
  - driver.assign_request() responses
  - driver.get_position() return values
  - driver.get_earnings() tracking

✓ Request objects:
  - Request.is_expired() behavior
  - Request generation based on RNG
  
✓ engine_helpers functions:
  - gen_requests() - Return fixed request lists
  - expire_requests() - Control expiration behavior
  - get_proposals() - Return specific proposals
  - collect_offers() - Control offer behavior
  - resolve_conflicts() - Deterministic conflict resolution
  - assign_requests() - Track assignments
  - move_drivers() - Control movement
  - mutate_drivers() - Control behavior changes
  - sim_to_state_dict() - Return structured state

✓ Adapter (if testing orchestration):
  - adapter.step() behavior
  - adapter metrics extraction
```

**Test Scenarios:**
```
1. Single Tick Orchestration:
   - Mock all engine_helpers to return controlled values
   - Verify exact call sequence: gen → expire → propose → collect → resolve → assign → move → mutate
   - Verify order-dependent behavior (e.g., can't assign before proposing)

2. Driver-Request Matching:
   - Mock get_proposals() to return specific proposals
   - Mock collect_offers() to return specific offers
   - Verify resolve_conflicts() chooses correctly
   - Verify assign_requests() updates driver/request state

3. State Consistency:
   - Mock driver movements
   - Verify arrival detection triggers completion
   - Verify earnings/points updated correctly
```

**Complexity:** Very High - Orchestration layer
**Test Type:** Unit Test with Heavy Mocking

---

### 2.3 Behaviours Classes (`phase2/behaviours.py`) - MOCKING + PATCH

**Why Mock:**
- Policy classes implement different decision strategies
- Dependencies on request/offer comparisons
- Side effects on driver state
- Need to test isolation from other policies

**What to Mock:**
```
✓ Request objects:
  - pickup location
  - dropoff location
  - distance from driver
  
✓ Offer objects:
  - earnings estimate
  - points estimate
  - trip distance

✓ Driver state:
  - current position
  - balance
  - available_capacity
```

**Test Scenarios Using Patch:**
```
1. GreedyDistance Policy:
   - Mock multiple offers with different distances
   - Verify policy selects closest offer
   - Mock tied distances → verify deterministic ordering

2. EarningsMax Policy:
   - Mock offers with different earnings
   - Verify highest earnings selected
   - Verify numeric precision edge cases

3. Lazy Policy:
   - Mock various offer states
   - Verify probability-based selection
   - Verify randomness seeded for deterministic testing
```

**Complexity:** Medium - Isolated decision logic
**Test Type:** Unit Test with Mocking

---

## 3. PATCH - Where to Replace External Code

### 3.1 Random Number Generation - PATCH CANDIDATE

**Where:** `phase2/behaviours.py` (Lazy policy uses random choice)

**Why Patch:**
- Random behavior makes tests non-deterministic
- Need predictable results for validation
- RNG is external dependency

**How to Patch:**
```python
from unittest.mock import patch

@patch('random.choice')
def test_lazy_policy_selection(mock_choice):
    # Make choice deterministic
    mock_choice.return_value = selected_offer
    
    # Test policy behavior
    policy = LazyPolicy()
    result = policy.decide(offers)
    
    # Verify behavior
    assert result == selected_offer
```

---

### 3.2 Time-Based Operations - PATCH CANDIDATE

**Where:** `phase2/request.py` (expiration checking), time tracking

**Why Patch:**
- Real time progression not needed for unit tests
- Makes tests slow and dependent on execution time
- External system state (current time)

**How to Patch:**
```python
from unittest.mock import patch
from datetime import datetime, timedelta

@patch('datetime.datetime')
def test_request_expiration(mock_datetime):
    # Set creation time
    mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
    
    request = Request(...)
    
    # Advance time by 10 seconds
    mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 10)
    
    # Test expiration with fixed time
    assert request.is_expired()
```

---

### 3.3 Generator/Helper Functions - PATCH CANDIDATE

**Where:** `phase2/helpers_2/engine_helpers.py` functions called by Simulation

**Why Patch:**
- Engine helpers implement complex logic with multiple steps
- Testing Simulation should test orchestration, not helper implementation
- Helpers should be tested separately (unit tests)
- Reduces test coupling to helper implementations

**How to Patch:**
```python
from unittest.mock import patch

@patch('phase2.simulation.engine_helpers.gen_requests')
@patch('phase2.simulation.engine_helpers.expire_requests')
def test_simulation_tick_ordering(mock_expire, mock_gen):
    # Control what helpers return
    mock_gen.return_value = [request1, request2]
    mock_expire.return_value = [request1]  # request2 expired
    
    sim = Simulation(...)
    sim.tick()
    
    # Verify calls in correct order
    assert mock_gen.called
    assert mock_expire.called
    mock_gen.assert_called_before(mock_expire)
```

---

## 4. Integration Testing - When to Use Real Objects

### 4.1 Driver + core_helpers Integration
**Test Type:** Integration Test (No mocking)
**When to Use:** 
- Verify real movement logic
- Verify trip completion flow
- Verify earnings calculations

**Example:**
```python
def test_driver_complete_trip_integration():
    # Use REAL core_helpers
    driver = Driver(...)
    request = Request(pickup=(0,0), dropoff=(10,10))
    
    driver.assign_request(request)
    
    # Simulate movement ticks (real is_at_target checking)
    while driver.active_request:
        driver.step()
    
    # Verify real earnings calculations happened
    assert driver.earnings > 0
    assert driver.total_points > 0
```

### 4.2 Request + Adapter Integration
**Test Type:** Integration Test
**When to Use:**
- Verify adapter correctly interfaces with Phase 1
- Verify state transitions between systems

---

## 5. Testing Checklist by Component

| Component | Unit Test | Mock | Patch | Integration |
|-----------|-----------|------|-------|-------------|
| **Point** | ✓ Core | - | - | - |
| **Request** | ✓ Core | ✓ Time (optional) | ✓ datetime | - |
| **Offer** | ✓ Core | - | - | - |
| **Driver** | ✓ Heavy Mock | ✓ Request, Offer, helpers | ✓ core_helpers | ✓ With helpers |
| **Behaviours** | ✓ Heavy Mock | ✓ Offers, Requests | ✓ random | - |
| **Simulation** | ✓ Heavy Mock | ✓ All dependencies | ✓ engine_helpers | ✓ Adapter |
| **Adapter** | ✓ Core | ✓ Phase1 responses | ✓ simulation calls | ✓ Full system |

---

## 6. Mocking Strategy Summary

### HIGH Priority Mocking (Do First):
```
1. Driver class:
   - Mock core_helpers functions
   - Mock Request objects
   - Test trip assignment/completion flow

2. Simulation class:
   - Mock engine_helpers functions  
   - Mock Driver objects
   - Test orchestration order

3. Behaviours classes:
   - Mock Offer objects
   - Mock Request objects
   - Test decision logic
```

### MEDIUM Priority Mocking:
```
1. Request expiration:
   - Patch datetime for time-based testing
   - Test timeout logic deterministically

2. Random behavior:
   - Patch random.choice for LazyPolicy
   - Make probability-based tests deterministic
```

### LOW Priority Mocking:
```
1. Point class - No mocking needed (pure math)
2. Offer class - No mocking needed (simple data)
3. Adapter - Integration test more valuable
```

---

## 7. Current Test Files Status

### Existing Test Coverage:
```
✓ test_point.py - Point class tests
✓ test_request.py - Request class tests
✓ test_policies.py - Behaviours class tests
✓ test_driver.py - Driver class tests
✓ test_behaviours.py - Additional behaviour tests
✓ test_simulation.py - Simulation tests
```

### Enhancement Recommendations:
```
→ Add mocking to test_driver.py for core_helpers functions
→ Add mocking to test_simulation.py for engine_helpers functions
→ Add patching for random/datetime in appropriate tests
→ Add integration tests for Driver + helpers flow
→ Add integration tests for Simulation full tick cycle
```

---

## 8. Quick Reference: When to Use Each Technique

### Use unittest When:
- Testing pure functions (no side effects)
- Testing simple state changes
- Testing input/output validation
- Components have no external dependencies
- **Examples:** Point class, basic Request tests, Offer calculations

### Use Mocking When:
- Component has many dependencies
- Want to isolate behavior for unit testing
- Need to control external object behavior
- Testing complex orchestration in isolation
- **Examples:** Driver (depends on helpers), Simulation (depends on many classes)

### Use Patch When:
- Need to replace external/standard library calls
- Time-based operations need to be deterministic
- Random behavior needs to be controlled
- Want to verify function was called correctly
- **Examples:** datetime for Request expiration, random.choice for LazyPolicy, engine_helpers in Simulation

### Use Integration Tests When:
- Testing real interactions between components
- Want to verify end-to-end workflows
- Testing data flow through multiple layers
- Components need real state from each other
- **Examples:** Driver completing full trip, Simulation processing full tick

---

## 9. Implementation Priority

### Phase 1: Core Unit Tests (No Mocking)
```
1. Point class - Pure math
2. Request basic tests - State validation
3. Offer basic tests - Data validation
```

### Phase 2: Add Mocking (Isolate Behavior)
```
1. Driver tests - Mock core_helpers
2. Behaviours tests - Mock Offers/Requests
3. Simulation tests - Mock engine_helpers
```

### Phase 3: Add Patch (Control External Dependencies)
```
1. Request expiration - Patch datetime
2. Lazy policy - Patch random.choice
3. RNG-dependent behaviors - Patch random
```

### Phase 4: Integration Tests (Real Interactions)
```
1. Driver + core_helpers workflow
2. Simulation full tick cycle
3. Adapter + Phase 1 integration
```

---

## 10. Key Principles

1. **Test in isolation first (Mock)** → Then test together (Integration)
2. **Replace external dependencies** → Makes tests fast and deterministic
3. **Control randomness** → Patch random for reproducible tests
4. **Control time** → Patch datetime for time-based logic
5. **Verify call order** → Use mock assertions for orchestration
6. **Test side effects** → Verify state changes happen correctly
7. **Keep tests readable** → Use descriptive mock names and clear assertions

---

## Notes

- Your current test structure is excellent - keep tests in `test/` folder
- Each test file focuses on one component (good separation)
- Next step: Add mocking to existing tests for better coverage
- Consider pytest as runner (more readable than unittest for complex tests)
- The TypeErrors in your code suggest intentional validation - test these!
