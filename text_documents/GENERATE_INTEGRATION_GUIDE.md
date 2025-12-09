# Integration Guide: How to Use Updated Generate Functions in sim_mod.py

## The Problem Addressed

**Feedback from Phase 1 review:**
> "We need to generate requests when there are no more requests in the CSV file. This should work with the req_rate toggle in the UI."

**Current sim_mod.py issue:**
```python
def simulate_step(state):
    # Only processes requests from state["future"] (CSV file)
    # When CSV is exhausted, simulation stops generating new requests
    # req_rate is stored but never used!
```

---

## The Solution

### Where to Add the Call

In `simulate_step()`, add this at the **very beginning** (after incrementing time):

```python
def simulate_step(state):
    # 1. Update the simulation time by one step
    state["t"] += 1
    
    # 2. ✅ GENERATE NEW REQUESTS (NEW!)
    io_mod.generate_requests(
        state["t"],
        state["future"],
        state["req_rate"],
        state["width"],
        state["height"]
    )
    
    # 3. Start any new requests that are ready to run (EXISTING)
    new_requests = [req for req in state["future"] if req["t"] == state["t"]]
    for req in new_requests:
        req["status"] = "waiting"
    state["pending"].extend(new_requests)
    state["future"] = [req for req in state["future"] if req["t"] > state["t"]]
    
    # 4. Rest of simulation continues...
    # ... (rest of existing code)
```

---

## How It Works

### Timeline
```
Time 0: simulate_step() called
    ├─ Increment time: state["t"] = 1
    ├─ Generate requests: add ~2 requests to state["future"]
    │                    (using Poisson distribution)
    ├─ Process requests: move those with t == 1 to pending
    └─ Continue simulation...

Time 1: simulate_step() called
    ├─ Increment time: state["t"] = 2
    ├─ Generate requests: add ~2 more requests to state["future"]
    ├─ Process requests: move those with t == 2 to pending
    └─ Continue simulation...

Time 100: simulate_step() called (CSV exhausted long ago!)
    ├─ Increment time: state["t"] = 101
    ├─ Generate requests: add ~2 requests to state["future"]
    │                    (STILL WORKS! No CSV needed)
    ├─ Process requests: move those with t == 101 to pending
    └─ Continue simulation...
```

### Poisson Distribution Effect

**With req_rate = 2.0:**
```python
Time 1: generate_requests() → 3 requests added (lucky!)
Time 2: generate_requests() → 1 request added
Time 3: generate_requests() → 2 requests added
Time 4: generate_requests() → 0 requests added
Time 5: generate_requests() → 4 requests added
...
Average over 100 steps: ~200 requests (realistic!)
```

---

## Code Change (Detailed)

### Current Code
```python
def simulate_step(state):
    # 1. Update the simulation time by one step
    state["t"] += 1

    # 2. Start any new requests that are ready to run
    new_requests = [req for req in state["future"] if req["t"] == state["t"]]
    # ... rest of code
```

### Updated Code
```python
def simulate_step(state):
    # 1. Update the simulation time by one step
    state["t"] += 1

    # 2. Generate new requests using req_rate (POISSON DISTRIBUTION)
    #    This allows continuous generation after CSV is exhausted
    io_mod.generate_requests(
        state["t"],               # Current time
        state["future"],          # Append to this list
        state["req_rate"],        # Rate from UI (0.5 to 5.0+)
        state["width"],           # Grid width (50)
        state["height"]           # Grid height (30)
    )

    # 3. Start any new requests that are ready to run
    new_requests = [req for req in state["future"] if req["t"] == state["t"]]
    # ... rest of code
```

---

## Parameters Explained

### `state["t"]` → Current simulation time
- Type: int
- Used for: Request creation timestamp
- Example: When t=5, generated requests have t=5

### `state["future"]` → List to append new requests to
- Type: list[dict]
- Used for: Accumulating generated requests
- Note: Existing requests from CSV also here
- Result: Mix of CSV requests and generated requests

### `state["req_rate"]` → User's slider value from GUI
- Type: float
- Range: Usually 0.5 to 5.0+ per UI configuration
- Effect: Controls average requests per step
- Example: req_rate=2.0 → ~2 requests/step on average

### `state["width"]` and `state["height"]`
- Type: int
- Value: Usually 50 and 30 (grid bounds)
- Use: Random position generation for pickup/dropoff

---

## Example Scenarios

### Scenario 1: Small req_rate (low demand)
```
GUI Setting: req_rate = 0.5
simulate_step() behavior:
  Step 1: Generate 0 requests
  Step 2: Generate 1 request
  Step 3: Generate 0 requests
  Step 4: Generate 1 request
  ...
Result: ~50 requests per 100 steps
Interpretation: Quiet food delivery business
```

### Scenario 2: Medium req_rate (normal demand)
```
GUI Setting: req_rate = 2.0
simulate_step() behavior:
  Step 1: Generate 3 requests
  Step 2: Generate 2 requests
  Step 3: Generate 1 request
  Step 4: Generate 2 requests
  ...
Result: ~200 requests per 100 steps
Interpretation: Busy food delivery business
```

### Scenario 3: High req_rate (peak hours)
```
GUI Setting: req_rate = 5.0
simulate_step() behavior:
  Step 1: Generate 6 requests
  Step 2: Generate 4 requests
  Step 3: Generate 5 requests
  Step 4: Generate 7 requests
  ...
Result: ~500 requests per 100 steps
Interpretation: Peak time (rush hour delivery)
```

---

## Testing the Integration

### Test 1: Verify generation works
```python
# Before integrate ion: CSV requests only
state = sim_mod.init_state(drivers, load_requests('data/requests.csv'), ...)
print(f"Initial future requests: {len(state['future'])}")  # e.g., 11

# After CSV exhausted
for _ in range(50):
    state, metrics = sim_mod.simulate_step(state)

print(f"Total generated: {len(state['future']) + len(state['pending'])}")
# Should be > 11 (CSV + generated)
```

### Test 2: Verify req_rate affects generation
```python
# Test 1: Low rate
state1 = init_state(..., req_rate=0.5, ...)
for _ in range(100):
    simulate_step(state1)
count1 = len(state1['served']) + len(state1['expired'])

# Test 2: High rate
state2 = init_state(..., req_rate=5.0, ...)
for _ in range(100):
    simulate_step(state2)
count2 = len(state2['served']) + len(state2['expired'])

print(f"Low rate: {count1}")   # ~50
print(f"High rate: {count2}")  # ~500
assert count2 > count1  # High rate should generate more
```

### Test 3: Verify field names
```python
requests = []
generate_requests(0, requests, 1.0, 50, 30)

# Check driver field names
drivers = generate_drivers(5, 50, 30)
assert all('id' in d for d in drivers)        # Not 'driver_id'!
assert all(0 <= d['x'] <= 50 for d in drivers)

# Check request field names
assert all('id' in r for r in requests)
assert all('t' in r for r in requests)
assert all('px' in r for r in requests)
```

---

## Backward Compatibility

### What Still Works
```python
# Loading from CSV still works
drivers = io_mod.load_drivers('data/drivers.csv')
requests = io_mod.load_requests('data/requests.csv')

# Generating random drivers still works
drivers = io_mod.generate_drivers(10, 50, 30)

# Initializing state still works
state = sim_mod.init_state(drivers, requests, timeout=20, req_rate=2.0)
```

### What Changed
```python
# simulate_step() now calls generate_requests internally
# (if you add the integration code)
state, metrics = sim_mod.simulate_step(state)
# Now handles continuous request generation!
```

---

## Benefits of This Integration

### ✅ Addresses Feedback
- "Generate requests when CSV is exhausted" → Done!
- "Work with req_rate toggle" → Done!

### ✅ Realistic Simulation
- Poisson distribution = real-world request patterns
- No artificial cutoff when CSV ends

### ✅ UI Responsiveness
- Users can adjust req_rate slider during simulation
- Affects generation immediately

### ✅ Scalability
- Works for 10 requests or 10,000 requests
- Memory efficient (generates on-the-fly)

### ✅ Maintainability
- Clean integration (one function call)
- Uses existing generate_requests() function
- No complex logic needed

---

## Summary

1. **Add one function call** in simulate_step() after incrementing time
2. **Pass 5 parameters** from state (t, future, req_rate, width, height)
3. **Result:** Continuous request generation after CSV exhausted
4. **Benefit:** req_rate slider now fully functional
5. **Behavior:** Realistic Poisson-distributed request arrival

**Total code change:** ~6 lines of code! 🎯

The integration is ready to implement in your next Phase 1 update!
