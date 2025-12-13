# Phase 2 Architecture Diagram - Latest Version

## 1. Complete System Architecture

```mermaid
graph TB
    subgraph GUI["🎨 GUI Layer (DearPyGui)"]
        MainWindow["Main Window<br/>Simulation Control"]
        DispatchUI["Dispatch UI<br/>Real-time Visualization"]
        ReportWindow["Report Window<br/>Post-Simulation Analysis"]
    end
    
    subgraph Adapter["🔌 Adapter Layer"]
        AdapterAPI["Adapter Module<br/>(adapter.py)<br/>Bridge Functions"]
        StateConv["State Conversion<br/>Object ↔ Dict<br/>engine_helpers"]
        MetricsExt["Metrics Extraction<br/>get_adapter_metrics<br/>engine_helpers"]
    end
    
    subgraph Phase2["🔄 Phase 2: OOP Engine"]
        Simulation["DeliverySimulation<br/>9-Stage Orchestrator<br/>O(D*R) per tick"]
        EngineHelpers["Engine Helpers<br/>9-Step Functions<br/>- gen_requests<br/>- expire_requests<br/>- get_proposals<br/>- collect_offers<br/>- resolve_conflicts<br/>- assign_requests<br/>- move_drivers<br/>- mutate_drivers"]
        
        subgraph OOP["Core OOP Classes"]
            Driver["Driver<br/>- position: Point<br/>- behaviour: Behaviour<br/>- status, earnings, points<br/>- step(), assign(), complete()"]
            Request["Request<br/>- pickup/dropoff: Point<br/>- time, status<br/>- is_expired()<br/>- mark_assigned/picked/delivered"]
            Offer["Offer<br/>- driver, request<br/>- trip_distance<br/>- trip_points, trip_earnings<br/>- comparison operators"]
            Point["Point<br/>- x, y coordinates<br/>- distance_to()<br/>- arithmetic operations"]
        end
        
        subgraph Behaviors["Behavior Strategies"]
            DriverBehaviour["DriverBehaviour<br/>Abstract Base Class<br/>decide()"]
            GreedyDist["GreedyDistanceBehaviour<br/>Accept if pickup<br/>distance ≤ threshold"]
            EarningsMax["EarningsMaxBehaviour<br/>Accept if reward/time<br/>≥ threshold"]
            Lazy["LazyBehaviour<br/>Probability-based<br/>accept with random"]
        end
        
        subgraph Policies["Dispatch Policies"]
            GlobalGreedy["GlobalGreedyPolicy<br/>dispatch_policy<br/>Best offer per request<br/>Resolves conflicts"]
        end
        
        subgraph Generation["Request Generation"]
            ReqGenerator["RequestGenerator<br/>Poisson-like arrivals<br/>Stochastic process"]
            ConfigParams["Params: rate, width,<br/>height, timeout"]
        end
        
        subgraph Mutation["Behavior Mutation"]
            HybridMutation["HybridMutation<br/>mutation_rule<br/>Adapt driver behaviors<br/>during simulation"]
        end
        
        CoreHelpers["Core Helpers<br/>Driver Lifecycle<br/>- is_at_target()<br/>- move_towards()<br/>- calculate_points()<br/>- record_assignment_start()<br/>- record_completion()<br/>- finalize_trip()"]
        
        MetricsHelpers["Metrics Helpers<br/>SimulationTimeSeries<br/>Track per-tick metrics<br/>earned, expired, wait_time"]
    end
    
    subgraph Phase1["📋 Phase 1: I/O & Helpers"]
        IOMod["io_mod.py<br/>Shared I/O Functions<br/>- load_drivers()<br/>- load_requests()<br/>- generate_drivers()"]
        CSVData["CSV Data Files<br/>drivers.csv<br/>requests.csv"]
        Phase1Helpers["Phase 1 Helpers<br/>- load_helper<br/>- generate_helper<br/>- geometri_helper<br/>- sim_helper"]
    end
    
    GUI -->|"calls adapter"| AdapterAPI
    AdapterAPI -->|"init_simulation()"| Simulation
    AdapterAPI -->|"step_simulation()"| Simulation
    AdapterAPI -->|"get_metrics()"| MetricsExt
    AdapterAPI -->|"convert_state()"| StateConv
    
    Simulation -->|"9-stage loop"| EngineHelpers
    EngineHelpers -->|"uses"| OOP
    EngineHelpers -->|"uses"| Policies
    EngineHelpers -->|"uses"| CoreHelpers
    
    Driver -->|"has"| Point
    Driver -->|"uses"| Behaviors
    Driver -->|"calls"| CoreHelpers
    
    Request -->|"has"| Point
    Offer -->|"references"| Driver
    Offer -->|"references"| Request
    
    DriverBehaviour -->|"inherited by"| GreedyDist
    DriverBehaviour -->|"inherited by"| EarningsMax
    DriverBehaviour -->|"inherited by"| Lazy
    
    GlobalGreedy -->|"uses"| Behaviors
    GlobalGreedy -->|"proposes to"| Driver
    
    ReqGenerator -->|"creates"| Request
    HybridMutation -->|"modifies"| Driver
    
    Simulation -->|"tracks"| MetricsHelpers
    MetricsHelpers -->|"recorded by"| ReportWindow
    StateConv -->|"converts"| OOP
    
    AdapterAPI -->|"imports from"| IOMod
    IOMod -->|"loads from"| CSVData
    IOMod -->|"uses"| Phase1Helpers
    
    DispatchUI -->|"displays"| Simulation
    ReportWindow -->|"analyzes"| Simulation
    ReportWindow -->|"plots"| MetricsHelpers
```

---

## 2. Data Flow: One Complete Simulation Tick

```mermaid
graph LR
    subgraph Tick["One Simulation Tick (time → time+1) - 9 Stages"]
        Step1["1️⃣ gen_requests<br/>O(R)<br/>Generate new<br/>requests"]
        Step2["2️⃣ expire_requests<br/>O(R)<br/>Remove timed-out<br/>requests"]
        Step3["3️⃣ get_proposals<br/>O(D×R)<br/>Policy proposes<br/>driver-request pairs"]
        Step4["4️⃣ collect_offers<br/>O(P)<br/>Drivers accept/reject<br/>via behaviour"]
        Step5["5️⃣ resolve_conflicts<br/>O(O log O)<br/>One driver per<br/>request"]
        Step6["6️⃣ assign_requests<br/>O(A)<br/>Finalize assignments<br/>update statuses"]
        Step7["7️⃣ move_drivers<br/>O(D)<br/>Move toward targets<br/>detect arrivals"]
        Step8["8️⃣ mutate_drivers<br/>O(D)<br/>Evolve behaviours<br/>probabilistically"]
        Step9["9️⃣ increment time<br/>O(1)<br/>time += 1"]
    end
    
    Step1 -->|"proposals"| Step3
    Step2 -->|"active requests"| Step3
    Step3 -->|"D×R pairs"| Step4
    Step4 -->|"offers"| Step5
    Step5 -->|"final assignments"| Step6
    Step6 -->|"driver-request links"| Step7
    Step7 -->|"arrival events"| Step8
    Step8 -->|"behaviour changes"| Step1
    Step9 -->|"next tick"| Step1
    
    style Step1 fill:#e1f5ff
    style Step2 fill:#e1f5ff
    style Step3 fill:#f3e5f5
    style Step4 fill:#f3e5f5
    style Step5 fill:#fff3e0
    style Step6 fill:#fff3e0
    style Step7 fill:#e8f5e9
    style Step8 fill:#fce4ec
    style Step9 fill:#f1f8e9
```

---

## 3. Driver Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> IDLE
    
    IDLE -->|assign_request()| TO_PICKUP: Driver accepts<br/>offer from policy
    
    TO_PICKUP -->|is_at_target()| PICKUP: Driver reaches<br/>pickup location
    
    PICKUP -->|complete_pickup()| TO_DROPOFF: Passenger<br/>boards
    
    TO_DROPOFF -->|is_at_target()| DROPOFF: Driver reaches<br/>dropoff location
    
    DROPOFF -->|complete_dropoff()| IDLE: Trip complete<br/>Earnings updated<br/>Behaviour mutates
    
    IDLE -->|mutate_drivers()| IDLE: Behaviour may<br/>change probabilistically<br/>during idle
    
    note right of IDLE
        speed * dt distance per tick
        earnings accumulate
        points accumulate
    end note
    
    note right of TO_PICKUP
        Move toward request.pickup
        Move cost calculated
    end note
    
    note right of TO_DROPOFF
        Move toward request.dropoff
        Points = fare + wait bonus
    end note
```

---

## 4. Request Lifecycle

```mermaid
stateDiagram-v2
    [*] --> WAITING: RequestGenerator<br/>creates request at time T
    
    WAITING -->|is_expired()| EXPIRED: Age > timeout<br/>expire_requests()
    
    WAITING -->|mark_assigned()| ASSIGNED: Driver assigned<br/>via assign_requests()
    
    ASSIGNED -->|mark_picked()| PICKED: Driver reaches<br/>pickup location
    
    PICKED -->|mark_delivered()| DELIVERED: Driver reaches<br/>dropoff location<br/>Trip complete
    
    EXPIRED --> [*]
    DELIVERED --> [*]
    
    note right of WAITING
        Wait for driver
        Can expire if timeout exceeded
    end note
    
    note right of ASSIGNED
        Driver heading to pickup
        Status: "ASSIGNED"
    end note
    
    note right of PICKED
        Driver heading to dropoff
        Status: "PICKED"
    end note
    
    note right of DELIVERED
        Trip recorded in driver history
        Earnings transferred to driver
    end note
```

---

## 5. Class Dependencies and Inheritance

```mermaid
classDiagram
    class Point {
        float x
        float y
        distance_to(other) float
        __add__(other) Point
        __sub__(other) Point
        __mul__(scalar) Point
    }
    
    class Request {
        int id
        Point pickup
        Point dropoff
        int time_created
        str status
        is_expired() bool
        mark_assigned(driver_id)
        mark_picked(time)
        mark_delivered(time)
        wait_time int
    }
    
    class Driver {
        int id
        Point position
        DriverBehaviour behaviour
        float speed
        str status
        Request current_request
        float earnings
        float points
        is_idle() bool
        assign_request(req, time)
        step(dt)
        complete_pickup(time)
        complete_dropoff(time)
    }
    
    class Offer {
        Driver driver
        Request request
        float trip_distance
        float trip_points
        float trip_earnings
        __lt__(other) bool
        __eq__(other) bool
    }
    
    class DriverBehaviour {
        <<abstract>>
        decide(driver, offer, time) bool
    }
    
    class GreedyDistanceBehaviour {
        float max_distance
        decide(driver, offer, time) bool
    }
    
    class EarningsMaxBehaviour {
        float min_reward_per_time
        decide(driver, offer, time) bool
    }
    
    class LazyBehaviour {
        float max_pickup_distance
        float accept_probability
        decide(driver, offer, time) bool
    }
    
    class GlobalGreedyPolicy {
        dispatch(sim) list[Offer]
        resolve_conflicts(offers) dict
    }
    
    class RequestGenerator {
        float rate
        int width, height
        maybe_generate(time) list[Request]
    }
    
    class HybridMutation {
        apply(driver, time)
    }
    
    class DeliverySimulation {
        list drivers
        list requests
        GlobalGreedyPolicy dispatch_policy
        RequestGenerator request_generator
        HybridMutation mutation_rule
        int time
        tick()
        get_snapshot() dict
    }
    
    Request "1" --> "1" Point : pickup
    Request "1" --> "1" Point : dropoff
    Driver "1" --> "1" Point : position
    Driver "1" --> "0..1" Request : current_request
    Driver "1" --> "0..1" DriverBehaviour : behaviour
    Offer "1" --> "1" Driver
    Offer "1" --> "1" Request
    DriverBehaviour <|-- GreedyDistanceBehaviour
    DriverBehaviour <|-- EarningsMaxBehaviour
    DriverBehaviour <|-- LazyBehaviour
    DeliverySimulation "1" --> "*" Driver : drivers
    DeliverySimulation "1" --> "*" Request : requests
    DeliverySimulation "1" --> "1" GlobalGreedyPolicy
    DeliverySimulation "1" --> "1" RequestGenerator
    DeliverySimulation "1" --> "1" HybridMutation
```

---

## 6. Adapter Functions - Bridge Between GUI and Simulation

```mermaid
graph TB
    subgraph AdapterFunctions["Adapter API (adapter.py)"]
        InitSim["init_simulation(drivers_dict,<br/>requests_dict, policy_config)<br/>→ None"]
        
        StepSim["step_simulation()<br/>→ None<br/>Calls sim.tick()"]
        
        GetMetrics["get_metrics()<br/>→ dict<br/>Extracts all metrics"]
        
        GetState["get_state_for_gui()<br/>→ dict<br/>Positions, statuses,<br/>destinations"]
        
        GenReq["generate_requests(start_t,<br/>out_list, rate, w, h)<br/>→ None<br/>Appends to list"]
    end
    
    subgraph Phase1IO["Phase 1 I/O (io_mod.py)"]
        LoadDrv["load_drivers(path)<br/>→ list[dict]<br/>From CSV"]
        LoadReq["load_requests(path)<br/>→ list[dict]<br/>From CSV"]
        GenDrv["generate_drivers(count,<br/>width, height)<br/>→ list[dict]<br/>Synthetic"]
    end
    
    subgraph StateHelpers["State Conversion (engine_helpers.py)"]
        DictToDriver["create_driver_from_dict(d)<br/>→ Driver"]
        DictToRequest["create_request_from_dict(d)<br/>→ Request"]
        ReqToDict["request_to_dict(r)<br/>→ dict"]
        SimToDict["sim_to_state_dict(sim)<br/>→ dict<br/>Full snapshot"]
        PlotData["get_plot_data_from_state(state)<br/>→ tuples<br/>For visualization"]
    end
    
    InitSim -->|"reads"| LoadDrv
    InitSim -->|"reads"| LoadReq
    InitSim -->|"creates objects via"| DictToDriver
    InitSim -->|"creates objects via"| DictToRequest
    
    StepSim -->|"calls"| GetState
    
    GetState -->|"uses"| SimToDict
    GetState -->|"uses"| PlotData
    
    GenReq -->|"creates"| DictToRequest
    GenReq -->|"appends to"| LoadReq
    
    GetMetrics -->|"extracts from sim"| StepSim
```

---

## 7. Complexity Analysis: Per Tick (9-Stage Orchestration)

```
Stage 1: gen_requests()        O(R)           Generate new requests
Stage 2: expire_requests()     O(R)           Check all requests for timeout
Stage 3: get_proposals()       O(D×R) worst   Policy checks each driver vs each request
Stage 4: collect_offers()      O(P)           P ≤ D×R, drivers evaluate proposals
Stage 5: resolve_conflicts()   O(O log O)     Sort offers per request, O = offers
Stage 6: assign_requests()     O(A)           A ≤ O, finalize assignments
Stage 7: move_drivers()        O(D)           Move D drivers toward targets
Stage 8: mutate_drivers()      O(D)           Apply mutations to D drivers
Stage 9: increment time        O(1)           time += 1

TOTAL per tick: O(D×R×log(D×R) + D + R)

With typical values (D=10 drivers, R=100 requests):
  → ~10,000 operations per tick
  → 1,000 ticks = ~10 million operations
  → < 1 second on modern hardware
```

---

## 8. Key Components Summary

| Component | Type | Role | Location |
|-----------|------|------|----------|
| **Point** | Value Class | 2D coordinates + distance | point.py |
| **Request** | State Machine | Pickup/dropoff task with lifecycle | request.py |
| **Driver** | Agent | Mobile unit with behaviour + earnings | driver.py |
| **Offer** | Decision Artifact | Driver-request pair for assignment | offer.py |
| **DriverBehaviour** | Strategy Pattern | Abstract behaviour (Greedy, Earnings, Lazy) | behaviours.py |
| **GlobalGreedyPolicy** | Dispatch Rule | Best offer per request | policies.py |
| **RequestGenerator** | Stochastic | Poisson arrivals | generator.py |
| **HybridMutation** | Evolution Rule | Adapt driver behaviours | mutation.py |
| **DeliverySimulation** | Orchestrator | 9-phase tick loop | simulation.py |
| **Engine Helpers** | Procedural | Step implementations | helpers_2/engine_helpers.py |
| **Core Helpers** | Lifecycle | Driver movement/trip logic | helpers_2/core_helpers.py |
| **Adapter** | Bridge | GUI ↔ Simulation interface | adapter.py |
| **Report Window** | Analysis | Post-sim metrics visualization | report_window.py |

---

## 9. Information Flow: GUI to Simulation

```mermaid
sequenceDiagram
    participant GUI as GUI<br/>(DearPyGui)
    participant Adapter as Adapter
    participant Sim as Simulation
    participant Helpers as Engine<br/>Helpers
    participant Objects as OOP<br/>Objects
    
    GUI->>Adapter: init_simulation(drivers, requests, config)
    Adapter->>Adapter: create_driver_from_dict()
    Adapter->>Adapter: create_request_from_dict()
    Adapter->>Sim: __init__(drivers, policy, generator, mutation)
    Sim-->>Adapter: simulation ready
    
    loop Every frame (9-stage tick)
        GUI->>Adapter: step_simulation()
        Adapter->>Sim: tick()
        
        Sim->>Helpers: gen_requests() - Stage 1
        Sim->>Helpers: expire_requests() - Stage 2
        Sim->>Helpers: get_proposals() - Stage 3
        Sim->>Helpers: collect_offers() - Stage 4
        Sim->>Helpers: resolve_conflicts() - Stage 5
        Sim->>Helpers: assign_requests() - Stage 6
        Sim->>Objects: driver.step() - Stage 7
        Sim->>Helpers: move_drivers() - Stage 7
        Sim->>Helpers: mutate_drivers() - Stage 8
        
        Sim-->>Adapter: tick complete
        
        Adapter->>Sim: get_snapshot()
        Sim-->>Adapter: state dict
        Adapter->>Adapter: sim_to_state_dict()
        Adapter->>Adapter: get_plot_data_from_state()
        Adapter-->>GUI: positions, statuses, destinations
        
        GUI->>GUI: render drivers, requests
    end
    
    GUI->>Adapter: get_metrics()
    Adapter->>Sim: access metrics
    Adapter-->>GUI: served, expired, avg_wait, earnings
```

---

## 10. File Organization

```
exam_phase2/
├── phase1/
│   ├── __init__.py
│   ├── io_mod.py                 ← Shared I/O (load/generate)
│   ├── phase1.py
│   ├── sim_mod.py
│   └── helpers_1/
│       ├── load_helper.py
│       ├── generate_helper.py
│       ├── geometri_helper.py
│       ├── metrics_helper.py
│       └── sim_helper.py
│
├── phase2/                        ← OOP Simulation Engine
│   ├── __init__.py
│   ├── point.py                  ← Value: 2D point
│   ├── request.py                ← State machine: request lifecycle
│   ├── driver.py                 ← Agent: delivers requests
│   ├── offer.py                  ← Decision artifact
│   ├── behaviours.py             ← Strategy: Greedy, Earnings, Lazy
│   ├── policies.py               ← Dispatch rule: GlobalGreedyPolicy
│   ├── generator.py              ← Stochastic request generation
│   ├── mutation.py               ← Behaviour evolution
│   ├── simulation.py             ← Orchestrator: 9-phase tick
│   ├── adapter.py                ← GUI bridge
│   ├── report_window.py          ← Post-sim visualization
│   └── helpers_2/
│       ├── core_helpers.py       ← Driver lifecycle (used by driver.py)
│       ├── engine_helpers.py     ← 9-step orchestration (used by simulation.py)
│       ├── metrics_helpers.py    ← Time-series tracking
│       ├── generator_helpers.py  ← (reference, unused)
│       ├── mutation_helpers.py   ← (reference, unused)
│       └── offer_helpers.py      ← (reference, unused)
│
├── gui/
│   ├── _engine.py
│   └── __pycache__/
│
├── data/
│   ├── drivers.csv
│   ├── drivers2.csv
│   ├── drivers3.csv
│   ├── drivers4.csv
│   ├── requests.csv
│   ├── requests2.csv
│   └── requests3.csv
│
├── test/
│   ├── test_point.py
│   ├── test_request.py
│   ├── test_driver.py
│   ├── test_offer.py
│   ├── test_behaviours.py
│   ├── test_policies.py
│   ├── test_simulation.py
│   └── __pycache__/
│
└── ARCHITECTURE_LATEST.md        ← This file
```

---

## Notes on Latest Changes

✅ **Updated Components:**
- `adapter.py`: Full bridge API with state conversion functions
- `behaviours.py`: Enhanced with type validation, clear decision logic
- `engine_helpers.py`: Added comprehensive Big O complexity docstring
- `driver.py`: Integrated with core_helpers for lifecycle management
- `simulation.py`: 9-phase orchestration with proper state tracking
- `report_window.py`: Post-simulation analysis and visualization

✅ **Key Architecture Principles:**
1. **Adapter Pattern**: GUI talks only to adapter, not direct simulation
2. **Strategy Pattern**: Pluggable behaviour strategies for drivers
3. **State Machines**: Request and Driver have well-defined lifecycle states
4. **Separation of Concerns**: 9-stage orchestration (engine_helpers) vs. core logic (classes)
5. **Type Safety**: Type checks in behaviours for robust validation
6. **Complexity Awareness**: O(D×R) orchestration understood and documented
7. **Stage-Based Orchestration**: 9 discrete stages per tick for clear flow control
