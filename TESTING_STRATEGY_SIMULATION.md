# Testing Strategy for DeliverySimulation Class

## Overview

The `DeliverySimulation` class is a **discrete-time event orchestrator** that coordinates:
- 9-phase per-tick orchestration (generate, expire, propose, collect, resolve, assign, move, mutate, time)
- Persistent state management (drivers, requests, statistics)
- Complex interactions between multiple subsystems

**Complexity**: O(D*R*log(D*R)) per tick where D=drivers, R=requests

---

## Why This Class Needs Mocking

Unlike `Point` (pure math, zero dependencies), `DeliverySimulation` has **external dependencies**:

| Component | Why Mock | Real or Mock? |
|-----------|----------|--------------|
| `request_generator` | Stochastic (random), has `maybe_generate()` method | **MOCK** - Control output |
| `dispatch_policy` | Policy-dependent, returns proposals | **MOCK** - Test different policies |
| `mutation_rule` | Optional, has `maybe_mutate()` method | **MOCK** - Test presence/absence |
| `drivers` (list) | Can use real `Driver` objects | **REAL** - Cheap to create, helps test integration |
| `requests` (list) | Can use real `Request` objects | **REAL** - Cheap to create |

**Result:** Heavy mocking needed for orchestration logic, but some real objects for integration tests.

---

## Key Methods to Test

### 1. `__init__(drivers, dispatch_policy, request_generator, mutation_rule, timeout=20)`

**Purpose**: Initialize simulation with validation

**Test Cases**:
- ✅ Normal initialization (valid inputs)
- ✅ Empty drivers list → ValueError
- ✅ Negative timeout → ValueError
- ✅ Zero timeout → ValueError
- ✅ All attributes initialized correctly
- ✅ Counters start at 0
- ✅ Empty requests list initially
- ✅ Default timeout value (20)

**Mocking Strategy**: Mock generator, policy, mutation_rule

---

### 2. `tick()` - The Main 9-Phase Orchestrator

**Purpose**: Execute one discrete time step

**Test Categories**:

#### A. Phase Execution Order
- Test that phases execute in correct order
- Verify each phase is called exactly once per tick
- Mock all 9 helper functions to verify call sequence

#### B. State Progression
- Time increments by 1 after tick
- Requests accumulate over multiple ticks
- Statistics update correctly

#### C. Integration Tests
- Real drivers + real requests + mocked policy
- Verify handoff between phases works

**Mocking Strategy**: Mock all 9 helper functions from `engine_helpers`

---

### 3. `get_snapshot()` - JSON Snapshot

**Purpose**: Return JSON-serializable state for GUI

**Test Cases**:
- ✅ Returns dict with correct keys (time, drivers, pickups, dropoffs, statistics)
- ✅ Driver snapshot includes id, x, y, status, rid, tx, ty
- ✅ Pickup list: only WAITING/ASSIGNED requests
- ✅ Dropoff list: only PICKED requests
- ✅ Expired requests not in snapshot
- ✅ Correct coordinates and values
- ✅ Handles None current_request
- ✅ Handles None request status safely

**Mocking Strategy**: No mocking needed (pure state access)

---

## Testing Approach: Layered Strategy

### Layer 1: Initialization Tests (No Mocking)
Test `__init__()` with real and mock objects. Verify validation.

### Layer 2: Unit Tests with Mocks
Test `tick()` phases in isolation. Mock all external dependencies.

### Layer 3: Snapshot Tests (No Mocking)
Test `get_snapshot()` with real state objects.

### Layer 4: Integration Tests (Minimal Mocking)
Real drivers + real requests + mocked policy/generator.
Verify phases work together correctly.

---

## Mock Strategy Summary

```python
from unittest.mock import Mock

# Request Generator Mock
gen_mock = Mock()
gen_mock.maybe_generate = Mock(return_value=[...])  # or []

# Dispatch Policy Mock
policy_mock = Mock()
policy_mock.assign = Mock(return_value=[...])  # list of (driver, request) pairs

# Mutation Rule Mock
mutation_mock = Mock()
mutation_mock.maybe_mutate = Mock()
```

---

## Why These Tests Are Essential

1. **Validation**: Constructor validates non-empty drivers and positive timeout
2. **Orchestration**: 9-phase tick() must execute phases in order
3. **State Management**: Persistent state must update correctly across ticks
4. **Statistics Tracking**: Served count, expired count, avg wait time calculations
5. **Integration**: Real Driver/Request objects must work with mocked policies
6. **Snapshot Correctness**: JSON output must be valid and complete

---

## Test Count Estimation

- **Initialization**: 8 tests
- **Tick Orchestration**: 6-8 tests (order, phase execution, state progression)
- **Snapshot**: 8-10 tests (completeness, correctness, edge cases)
- **Integration**: 4-6 tests (real objects with mocks)

**Total**: 26-34 tests (lean but comprehensive)

---

## Key Exam Talking Points

1. **Heavy Mocking Justification**: DeliverySimulation has 4 injected dependencies (generator, policy, mutation) that are stochastic or policy-dependent → must mock
2. **Real Objects in Integration**: Driver and Request are cheap to create and help test phase handoff correctness → keep real
3. **Snapshot Correctness**: JSON output is critical for GUI → comprehensive snapshot tests essential
4. **Phase Ordering**: 9-phase orchestration must execute phases in precise order → verify with mock call assertions
5. **State Persistence**: Multi-tick simulations show state accumulation → test with sequences of ticks
