# Phase 2: Object-Oriented Food Delivery Simulation

## Overview

This project extends Phase 1 with a fully object-oriented simulation of a food delivery service. The system features adaptive driver behaviors, intelligent dispatch policies, dynamic behavior mutation, and comprehensive metrics tracking. Built using layered architecture with clear separation of concerns.

## Project Structure

```
exam_phase2/
├── phase1/                 # Phase 1 integration and I/O
│   ├── phase1.py
│   ├── io_mod.py
│   ├── sim_mod.py         # GUI wrapper
│   └── helpers_1/
├── phase2/                 # Core OOP simulation
│   ├── adapter.py         # Dict ↔ Object conversion
│   ├── simulation.py       # Main orchestrator (9-step cycle)
│   ├── point.py           # 2D coordinate with vector operations
│   ├── request.py         # Request lifecycle management
│   ├── driver.py          # Driver agents with behaviors
│   ├── policies.py        # Dispatch policies (PolicyManager, GlobalGreedy, NearestNeighbor)
│   ├── behaviours.py      # Driver decision strategies
│   ├── mutation.py        # HybridMutation system
│   ├── generator.py       # Stochastic request generation
│   ├── offer.py           # Dispatch proposals
│   └── helpers_2/         # Engine helpers and metrics
├── gui/                    # GUI components
│   ├── _engine.py
│   └── __pycache__/
├── test/                   # Unit tests (13 files)
│   ├── test_adapter.py
│   ├── test_driver.py
│   ├── test_policies.py
│   ├── test_simulation.py
│   ├── test_mutation.py
│   └── ...
├── data/                   # Sample CSV files
│   ├── drivers.csv
│   ├── requests.csv
│   └── ...
├── text_documents/         # Documentation and analysis
├── dispatch_ui.py         # GUI entry point
└── README.md              # This file
```

```bash
python dispatch_ui.py
```

Then:
1. Load drivers and requests (CSV or generate)
2. Configure simulation parameters (timeout, dispatch policy, mutation)
3. Step through simulation or run to completion
4. View metrics and reports when done

### Run Tests

```bash
# Run all tests
python -m unittest discover -s test -p "test_*.py"

# Run specific test file
python -m unittest test.test_simulation

# Run specific test
python -m unittest test.test_driver.TestDriver.test_assign_request
```

## Architecture Layers

**Data Layer**: Point, Request, Offer - immutable domain objects  
**Logic Layer**: Driver, Policies, Behaviours - business rules and strategies  
**Orchestration Layer**: DeliverySimulation, Mutation - 9-step cycle coordination  
**Interface Layer**: Adapter - OOP simulation ↔ procedural GUI  
**GUI Layer**: dispatch_ui.py, report_window.py - user interaction  


# Run tests to verify:
- Invalid states are impossible
- Status transitions are valid
- Metrics track correctly
- Policies avoid duplicate assignments
- Mutations respect thresholds and cooldown

## Metrics & Reporting

After simulation completes, 4 visualization windows display:
- **Window 1**: Core metrics (served vs expired requests, creation times, service level)
- **Window 2**: Driver behavior impact (per-driver earnings, behavior changes)
- **Window 3**: Policy and offer analytics
- **Window 4**: System performance trends

All metrics stored as parallel arrays for synchronization guarantee.


## Files Overview

- **dispatch_ui.py**: GUI entry point, calls sim_mod.py
- **phase1/sim_mod.py**: Wrapper delegating to adapter.py
- **phase2/adapter.py**: Main adapter, converts dicts ↔ objects
- **phase2/simulation.py**: 9-step tick cycle orchestrator
- **phase2/helpers_2/engine_helpers.py**: Step 1-8 implementations
- **phase2/helpers_2/metrics_helpers.py**: SimulationTimeSeries tracking
- **text_documents/**: Detailed architecture and implementation documentation
