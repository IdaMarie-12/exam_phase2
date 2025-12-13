# Adapter Pattern - Data Transformation Flow

```mermaid
graph LR
    subgraph GUI["🖥️ GUI (dispatch_ui.py)"]
        LOAD["load_drivers<br/>(csv path)"]
        LOAD_REQ["load_requests<br/>(csv path)"]
        GEN_D["generate_drivers<br/>(n, w, h)"]
        GEN_R["generate_requests<br/>(t, rate, w, h)"]
        INIT["init_state<br/>(drivers, requests)"]
        STEP["simulate_step<br/>(state)"]
    end

    subgraph ADAPTER["🔌 ADAPTER (phase2/adapter.py)"]
        direction TB
        
        subgraph LOAD_SIDE["📥 LOADING"]
            AL["load_drivers<br/>CSV → List[Dict]"]
            AR["load_requests<br/>CSV → List[Dict]"]
        end
        
        subgraph GEN_SIDE["🎲 GENERATION"]
            GD["generate_drivers<br/>Random → List[Dict]"]
            GR["generate_requests<br/>Append → List[Dict]"]
        end
        
        subgraph INIT_SIDE["⚙️ INITIALIZATION"]
            DIC2OOP["List[Dict] → OOP Objects<br/>(Point, Driver, Request)"]
            CREATE_SIM["Create DeliverySimulation<br/>with policies"]
            CONVERT1["OOP → State Dict<br/>(using get_snapshot)"]
        end
        
        subgraph STEP_SIDE["🎬 SIMULATION STEP"]
            ACCEPT_DICT["Accept state dict<br/>(from GUI)"]
            OOP_SIM["Call simulation.tick()<br/>(9-phase orchestration)"]
            METRICS["Extract metrics<br/>(served, expired, avg_wait)"]
            CONVERT2["Convert OOP → Dict<br/>(sim_to_state_dict)"]
            RETURN_DICT["Return (state_dict, metrics)"]
        end
        
        AL --> AR
        AR --> GD
        GD --> GR
        GR --> DIC2OOP
        DIC2OOP --> CREATE_SIM
        CREATE_SIM --> CONVERT1
        
        ACCEPT_DICT --> OOP_SIM
        OOP_SIM --> METRICS
        METRICS --> CONVERT2
        CONVERT2 --> RETURN_DICT
    end

    subgraph BACKEND["⚡ PHASE 2 BACKEND"]
        direction TB
        
        subgraph DOMAIN["Core Domain"]
            POINT["Point<br/>(x, y)"]
            REQUEST["Request<br/>(status, pickup, dropoff)"]
            DRIVER["Driver<br/>(position, behaviour)"]
        end
        
        subgraph ENGINE["Simulation Engine"]
            SIM["DeliverySimulation<br/>(orchestrator)"]
            HELPERS["9-Step Helpers<br/>(gen, expire, propose,<br/>collect, resolve, assign,<br/>move, mutate, time)"]
        end
        
        subgraph STRATEGY["Strategy Pattern"]
            POLICY["DispatchPolicy<br/>(NearestNeighbour,<br/>GlobalGreedy)"]
            BEHAVIOUR["DriverBehaviour<br/>(GreedyDistance,<br/>EarningsMax, Lazy)"]
        end
        
        POINT --> REQUEST
        REQUEST --> DRIVER
        DRIVER --> SIM
        SIM --> HELPERS
        POLICY -.->|assign()| SIM
        BEHAVIOUR -.->|decide()| SIM
    end

    subgraph STATE_CONVERSION["🔄 DATA TRANSFORMATION"]
        direction LR
        
        CSV["CSV File<br/>id,x,y,px,py,dx,dy"]
        DICT1["Dict<br/>{id, x, y, px, py}"]
        OOP["OOP Objects<br/>Driver(Point, Request)"]
        DICT2["State Dict<br/>{t, drivers, pending,<br/>served, expired}"]
    end

    LOAD -->|CSV path| AL
    LOAD_REQ -->|CSV path| AR
    GEN_D --> GD
    GEN_R --> GR
    INIT -->|List[Dict]| DIC2OOP
    
    AL -.->|read CSV| CSV
    CSV -.->|parse| DICT1
    DICT1 -.->|Point(x,y)| OOP
    
    OOP --> SIM
    SIM --> CREATE_SIM
    CONVERT1 -.->|get_snapshot()| OOP
    OOP -.->|extract data| DICT2
    
    STEP -->|Dict state| ACCEPT_DICT
    OOP_SIM -->|tick()| HELPERS
    RETURN_DICT -->|Dict, metrics| STEP

    style ADAPTER fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style GUI fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style BACKEND fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style STATE_CONVERSION fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
```

## Data Transformation Summary

| Direction | Function | Input | Output | What Happens |
|-----------|----------|-------|--------|--------------|
| → | `load_drivers()` | CSV file path | `List[Dict]` | Read CSV, parse rows to dicts |
| → | `load_requests()` | CSV file path | `List[Dict]` | Read CSV, parse rows to dicts |
| → | `generate_drivers()` | n, width, height | `List[Dict]` | Random Point, create driver dicts |
| → | `generate_requests()` | rate, width, height | Append to list | Poisson generation, add dicts |
| → | `init_state()` | `List[Dict]`, config | State `Dict` | **Create OOP objects → Get snapshot** |
| ↔ | `simulate_step()` | State `Dict` | (State `Dict`, metrics) | **Call tick() on OOP → Convert back to dict** |

## Key Transformations

### 1️⃣ **CSV → Dict** (Loading)
```python
# CSV: id,x,y
# becomes:
{"id": 1, "x": 10.5, "y": 20.3}
```

### 2️⃣ **Dict → OOP** (Initialization)
```python
# Dict:
{"id": 1, "x": 10.5, "y": 20.3}

# becomes:
Driver(
    id=1,
    position=Point(10.5, 20.3),
    behaviour=GreedyDistanceBehaviour(20)
)
```

### 3️⃣ **OOP → Dict** (Snapshot)
```python
# OOP DeliverySimulation object
# becomes:
{
    "t": 5,
    "drivers": [{"id": 1, "x": 10.2, "y": 20.1, ...}],
    "pending": [{"id": 1, "px": 0, "py": 0, ...}],
    "served": 3,
    "expired": 0,
    "avg_wait": 4.2
}
```

## Why Adapter Pattern?

✅ **GUI expects dicts** (Phase 1 interface)  
✅ **Backend uses OOP** (Phase 2 design)  
✅ **Adapter translates** without changing either  
✅ **Decouples UI from logic**  
✅ **Can swap backends easily**
