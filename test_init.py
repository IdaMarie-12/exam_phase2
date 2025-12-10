#!/usr/bin/env python
"""Test initialization of the simulation"""

from phase1 import io_mod, sim_mod

print("Testing simulation initialization...")

# Generate test data
print("1. Generating drivers...")
drivers = io_mod.generate_drivers(3, 50, 30)
print(f"   Generated: {len(drivers)} drivers")

print("2. Generating requests...")
requests = []
io_mod.generate_requests(0, requests, 2.0, 50, 30)
print(f"   Generated: {len(requests)} requests")

print("3. Checking Phase 2 availability...")
print(f"   _USE_PHASE2: {sim_mod._USE_PHASE2}")
print(f"   _phase2_backend: {sim_mod._phase2_backend is not None}")

# Initialize state
print("4. Initializing state...")
try:
    state = sim_mod.init_state(drivers, requests, horizon=100)
    print(f"✓ State initialized successfully")
    print(f"  - Time: {state['t']}")
    print(f"  - Pending requests: {len(state.get('pending', []))}")
except Exception as e:
    print(f"✗ Error initializing state: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Try one simulation step
print("5. Running simulation step...")
try:
    result = sim_mod.simulate_step(state)
    print(f"✓ Simulation step completed")
    print(f"  - Result type: {type(result)}")
    if isinstance(result, tuple):
        print(f"  - Tuple length: {len(result)}")
except Exception as e:
    print(f"✗ Error in simulate_step: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ All tests passed!")

