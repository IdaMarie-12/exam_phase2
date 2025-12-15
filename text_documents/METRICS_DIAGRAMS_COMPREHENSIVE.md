# Metrics and Reporting System - Mermaid Diagrams

## Diagram 1: Overall Data Flow Architecture

```mermaid
graph TD
    SIM["🔄 DeliverySimulation<br/>Tick Loop"]
    
    P1["Phase 1-7<br/>Request Generation<br/>Expiration, Offers<br/>Assignment, Movement"]
    
    P8["Phase 8<br/>Mutation System<br/>HybridMutation.maybe_mutate<br/>for each driver"]
    
    MH["📝 mutation_history<br/>Detailed Records<br/>{time, driver_id,<br/>from_behaviour,<br/>to_behaviour,<br/>reason, avg_fare}"]
    
    P9["Phase 9<br/>Increment Time<br/>simulation.time += 1"]
    
    RT["📊 record_tick<br/>SimulationTimeSeries<br/>Capture entire state"]
    
    DCH["Extract & Aggregate<br/>- Driver behaviors<br/>- Request states<br/>- Offer history<br/>- Queue dynamics"]
    
    TS["⏱️ Time-Series Arrays<br/>55+ metrics tracked<br/>Parallel arrays for<br/>each tick"]
    
    PLOT["📈 Post-Simulation<br/>Report Generation<br/>4 matplotlib windows"]
    
    SIM --> P1
    P1 --> P8
    P8 --> MH
    MH --> P9
    P9 --> RT
    RT --> DCH
    DCH --> TS
    TS --> PLOT
    
    style SIM fill:#e1f5ff
    style P8 fill:#fff3e0
    style MH fill:#fff3e0
    style RT fill:#e8f5e9
    style TS fill:#f3e5f5
    style PLOT fill:#fce4ec
```

## Diagram 2: Mutation Data Collection Pipeline

```mermaid
graph LR
    subgraph Phase8["Phase 8: Mutation"]
        CHECK["1. Check Cooldown<br/>Last mutation?"]
        AVG["2. Calculate Avg Fare<br/>Last 10 trips"]
        EXIT["3. Check Exit<br/>Conditions"]
        PRIM["4a. Primary Mutation<br/>Performance-based"]
        SEC["4b. Secondary Mutation<br/>Stagnation-based"]
        RECORD["5. Record to<br/>mutation_history"]
    end
    
    subgraph Phase9["Phase 9"]
        INCR["Increment Time<br/>time += 1"]
    end
    
    subgraph AfterTick["After Tick"]
        RT["record_tick<br/>called"]
        LOOK["Look for mutations<br/>at time - 1"]
        COUNT["Count mutations<br/>this tick"]
        REASONS["Categorize by<br/>reason type"]
        APPEND["Append to<br/>metrics arrays"]
    end
    
    CHECK --> AVG
    AVG --> EXIT
    EXIT --> PRIM
    EXIT --> SEC
    PRIM --> RECORD
    SEC --> RECORD
    RECORD --> INCR
    INCR --> RT
    RT --> LOOK
    LOOK --> COUNT
    COUNT --> REASONS
    REASONS --> APPEND
    
    style Phase8 fill:#fff3e0
    style Phase9 fill:#ffe0b2
    style AfterTick fill:#e8f5e9
```

## Diagram 3: Mutation Reason Classification

```mermaid
graph TD
    MUT["Mutation Triggered"]
    
    subgraph Perf["Performance-Based"]
        LOW["🔴 Low Earnings<br/>avg < 3.0<br/>→ GreedyDistanceBehaviour"]
        HIGH["🟢 High Earnings<br/>avg > 10.0<br/>→ EarningsMaxBehaviour"]
    end
    
    subgraph Exit["Exit Conditions"]
        EG["🟠 Exit Greedy<br/>avg ≥ 5.0<br/>→ LazyBehaviour"]
        EE["🟠 Exit EarningsMax<br/>avg < 7.5<br/>→ LazyBehaviour"]
        EL["Exit Lazy<br/>N/A"]
    end
    
    subgraph Stag["Stagnation-Based"]
        LAZY["🔵 Stagnant Lazy<br/>70% variance ±5%<br/>→ Random active"]
        ACTIVE["🔵 Stagnant Active<br/>70% variance ±5%<br/>30% explore"]
    end
    
    MUT --> Perf
    MUT --> Exit
    MUT --> Stag
    
    style LOW fill:#ffcccc
    style HIGH fill:#ccffcc
    style EG fill:#ffe0b2
    style EE fill:#ffe0b2
    style EL fill:#f0f0f0
    style LAZY fill:#b3e5fc
    style ACTIVE fill:#b3e5fc
```

## Diagram 4: SimulationTimeSeries Data Structure

```mermaid
graph TD
    STS["SimulationTimeSeries<br/>Core Metrics Container"]
    
    subgraph Core["Core Metrics"]
        C1["times[]<br/>served[]<br/>expired[]<br/>avg_wait[]"]
    end
    
    subgraph BehaviorMetrics["Behavior Tracking"]
        B1["behaviour_distribution[]<br/>mutations_per_tick[]<br/>mutation_rate[]<br/>stable_ratio[]"]
    end
    
    subgraph MutationMetrics["Mutation Analysis"]
        M1["mutation_reasons[]<br/>driver_mutation_freq{}<br/>_mutation_reason_counts{}"]
    end
    
    subgraph QueueMetrics["Queue Dynamics"]
        Q1["pending_requests[]<br/>max_request_age[]<br/>avg_request_age[]<br/>rejection_rate[]"]
    end
    
    subgraph DispatchMetrics["Dispatch Efficiency"]
        D1["offers_generated[]<br/>offer_acceptance_rate[]<br/>matching_efficiency[]<br/>conflict_count[]"]
    end
    
    subgraph PolicyMetrics["Policy Effectiveness"]
        P1["policy_distribution[]<br/>avg_offer_quality[]<br/>actual_policy_used[]"]
    end
    
    subgraph BehaviorPerf["Behavior Performance"]
        BP1["earnings_by_behaviour{}<br/>acceptance_rate_by_behaviour{}<br/>behaviour_performance_ratio[]"]
    end
    
    STS --> Core
    STS --> BehaviorMetrics
    STS --> MutationMetrics
    STS --> QueueMetrics
    STS --> DispatchMetrics
    STS --> PolicyMetrics
    STS --> BehaviorPerf
    
    style STS fill:#f3e5f5
    style Core fill:#e1f5ff
    style BehaviorMetrics fill:#fff3e0
    style MutationMetrics fill:#fce4ec
    style QueueMetrics fill:#e8f5e9
    style DispatchMetrics fill:#f1f8e9
    style PolicyMetrics fill:#ede7f6
    style BehaviorPerf fill:#fbe9e7
```

## Diagram 5: Per-Tick Mutation Detection Flow

```mermaid
sequenceDiagram
    participant SIM as Simulation
    participant MH as mutation_history
    participant TS as TimeSeries
    participant ARR as Metrics Arrays
    
    SIM->>MH: Phase 8: Record mutations<br/>at time T
    Note over MH: Entries have 'time': T
    SIM->>SIM: Phase 9: time += 1<br/>Now time = T+1
    SIM->>TS: record_tick(sim)
    Note over TS: sim.time = T+1
    TS->>MH: Query: time == T+1 - 1?
    MH-->>TS: Find entries with time == T
    TS->>TS: Count mutations<br/>Build reason breakdown<br/>Track driver frequency
    TS->>ARR: Append to all metric arrays
    Note over ARR: mutations_per_tick[T] = count
    Note over ARR: mutation_reasons[T] = reasons
    Note over ARR: stable_ratio[T] = ratio
```

## Diagram 6: Behavior Distribution Tracking

```mermaid
graph LR
    subgraph T0["Tick 0"]
        B0["LazyBehaviour: 2<br/>GreedyDistanceBehaviour: 1<br/>EarningsMaxBehaviour: 0"]
    end
    
    subgraph T10["Tick 10"]
        B10["LazyBehaviour: 1<br/>GreedyDistanceBehaviour: 1<br/>EarningsMaxBehaviour: 1"]
    end
    
    subgraph T50["Tick 50"]
        B50["LazyBehaviour: 0<br/>GreedyDistanceBehaviour: 0<br/>EarningsMaxBehaviour: 3"]
    end
    
    subgraph T100["Tick 100"]
        B100["LazyBehaviour: 0<br/>GreedyDistanceBehaviour: 1<br/>EarningsMaxBehaviour: 2"]
    end
    
    PLOT["📊 Stacked Area Plot<br/>Shows Strategy Evolution"]
    
    T0 --> T10
    T10 --> T50
    T50 --> T100
    T100 --> PLOT
    
    style T0 fill:#e1f5ff
    style T10 fill:#b3e5fc
    style T50 fill:#81d4fa
    style T100 fill:#4fc3f7
    style PLOT fill:#fff3e0
```

## Diagram 7: Report Window Generation

```mermaid
graph TD
    TS["SimulationTimeSeries<br/>Complete Metrics"]
    
    subgraph Reports["4 Report Windows"]
        R1["🔵 System Efficiency<br/>- Service Level Over Time<br/>- Driver Utilization<br/>- Avg Wait Time<br/>- Served vs Expired"]
        
        R2["🟢 Behavior Dynamics<br/>- Behavior Distribution<br/>- Earnings by Behavior<br/>- Stable Ratio<br/>- Mutation Rate"]
        
        R3["🟡 Mutation Analysis<br/>- Cumulative Mutations<br/>- Mutation Reasons<br/>- Driver Mutation Freq<br/>- Strategy Transitions"]
        
        R4["🔴 Policy & Offers<br/>- Offers Generated<br/>- Acceptance Rate<br/>- Matching Efficiency<br/>- Policy Distribution"]
    end
    
    TS --> R1
    TS --> R2
    TS --> R3
    TS --> R4
    
    style TS fill:#f3e5f5
    style R1 fill:#b3e5fc
    style R2 fill:#c8e6c9
    style R3 fill:#ffe0b2
    style R4 fill:#ffccbc
```

## Diagram 8: Mutation Reasons Over Time - Stacked Area

```mermaid
graph LR
    T0["Tick 0"]
    T20["Tick 20"]
    T40["Tick 40"]
    T60["Tick 60"]
    T80["Tick 80"]
    
    subgraph Stack["Stacked Area: Mutation Reasons"]
        S["performance_low_earnings<br/>performance_high_earnings<br/>exit_greedy<br/>exit_earnings<br/>stagnation_exploration<br/>exit_lazy"]
    end
    
    T0 --> T20 --> T40 --> T60 --> T80 --> Stack
    
    style Stack fill:#fff3e0
```

## Diagram 9: Driver Mutation Frequency Distribution

```mermaid
graph LR
    SIM["Simulation<br/>Completes"]
    
    MF["driver_mutation_freq{}<br/>{'driver_0': 3,<br/>'driver_1': 5,<br/>'driver_2': 1,<br/>...}"]
    
    CHART["📊 Bar Chart<br/>X: Driver IDs<br/>Y: Mutation Count"]
    
    INSIGHT["Insights:<br/>- Which drivers most adaptive?<br/>- Outliers high/low?<br/>- Adaptation fairness?"]
    
    SIM --> MF
    MF --> CHART
    CHART --> INSIGHT
    
    style MF fill:#fce4ec
    style CHART fill:#fff3e0
    style INSIGHT fill:#e8f5e9
```

## Diagram 10: System Efficiency Metrics

```mermaid
graph TD
    SIM["DeliverySimulation State"]
    
    subgraph CALC["Calculations Per Tick"]
        SL["Service Level<br/>= served / (served + expired)<br/>→ service_level[]"]
        
        UTIL["Driver Utilization<br/>= busy_count / total_drivers<br/>→ utilization[]"]
        
        WAIT["Average Wait<br/>= mean(wait_times)<br/>→ avg_wait[]"]
        
        KPI["Served to Expired Ratio<br/>= served / expired<br/>→ served_to_expired_ratio[]"]
    end
    
    PLOT1["📈 Line Plot<br/>Time Series"]
    PLOT2["📈 Area Chart<br/>Trends"]
    
    SIM --> CALC
    CALC --> PLOT1
    CALC --> PLOT2
    
    style CALC fill:#e8f5e9
    style PLOT1 fill:#fff3e0
    style PLOT2 fill:#fff3e0
```

## Diagram 11: Queue Health Monitoring

```mermaid
graph TD
    QUEUE["Request Queue State"]
    
    subgraph METRICS["Per-Tick Queue Metrics"]
        PR["pending_requests<br/>= count(status == WAITING)"]
        
        MRA["max_request_age<br/>= max(current_time - creation_time)"]
        
        ARA["avg_request_age<br/>= mean(current_time - creation_time)"]
        
        RR["rejection_rate<br/>= rejected_offers / total_offers"]
    end
    
    TREND["Queue Health Indicators:<br/>- Growing queue = bottleneck<br/>- High max_age = timeout risk<br/>- High rejection = picky drivers"]
    
    QUEUE --> METRICS
    METRICS --> TREND
    
    style METRICS fill:#e8f5e9
    style TREND fill:#fff3e0
```

## Diagram 12: Data Validation Pipeline

```mermaid
graph LR
    RT["record_tick<br/>Called"]
    
    VAL1["✓ Check required attrs<br/>- time<br/>- served_count<br/>- expired_count<br/>- drivers<br/>- requests"]
    
    VAL2["✓ Validate ranges<br/>- percentages: 0-100<br/>- counts: ≥ 0<br/>- times: non-negative"]
    
    VAL3["✓ Check array consistency<br/>- All arrays same length<br/>- No NaN values"]
    
    PASS["✅ Valid Data<br/>Append to metrics"]
    
    FAIL["❌ Validation Failed<br/>Raise Error"]
    
    RT --> VAL1
    VAL1 --> VAL2
    VAL2 --> VAL3
    VAL3 -->|Pass| PASS
    VAL3 -->|Fail| FAIL
    
    style PASS fill:#c8e6c9
    style FAIL fill:#ffcccc
```

## Diagram 13: Plot Type Selection

```mermaid
graph TD
    METRIC["Metric Type"]
    
    subgraph LineTime["Time-Series Line Plots"]
        LT["service_level[]<br/>utilization[]<br/>avg_wait[]<br/>mutation_rate[]"]
    end
    
    subgraph StackedArea["Stacked Area Charts"]
        SA["behaviour_distribution[]<br/>mutation_reasons[]<br/>policy_distribution[]"]
    end
    
    subgraph BarChart["Bar Charts"]
        BC["driver_mutation_freq{}<br/>mutation_reason_counts{}"]
    end
    
    subgraph FilledArea["Filled Area Charts"]
        FA["Cumulative trends<br/>Cumulative mutations"]
    end
    
    USE["Plot Type Selection<br/>Based on Data Dimensionality<br/>and Analytical Goal"]
    
    METRIC --> LineTime
    METRIC --> StackedArea
    METRIC --> BarChart
    METRIC --> FilledArea
    
    LineTime --> USE
    StackedArea --> USE
    BarChart --> USE
    FilledArea --> USE
    
    style LineTime fill:#b3e5fc
    style StackedArea fill:#c8e6c9
    style BarChart fill:#ffe0b2
    style FilledArea fill:#ffccbc
```

## Diagram 14: Behavior Adaptation Analysis

```mermaid
graph TD
    SIM["Simulation State<br/>per Tick"]
    
    subgraph TRACK["Track Per Behavior Type"]
        SNAP["behaviour_distribution<br/>Snapshot count"]
        
        EARN["earnings_by_behaviour<br/>Avg earnings"]
        
        ACC["acceptance_rate_by_behaviour<br/>Offer acceptance %"]
        
        PERF["behaviour_performance_ratio<br/>Service level per type"]
    end
    
    ANALYSIS["Adaptation Success Analysis<br/>- Does mutation improve earnings?<br/>- Which strategy dominates?<br/>- Do behaviors converge?"]
    
    SIM --> TRACK
    TRACK --> ANALYSIS
    
    style TRACK fill:#fff3e0
    style ANALYSIS fill:#e8f5e9
```

## Diagram 15: Complete Metrics Architecture

```mermaid
graph TB
    subgraph INPUT["Input Sources"]
        SIM["DeliverySimulation"]
        MH["mutation_history"]
        DR["Driver Objects"]
        RQ["Request Objects"]
    end
    
    subgraph COLLECT["Data Collection<br/>Per Tick"]
        RT["record_tick"]
        TC["_track_behaviour_changes"]
        TO["_track_offers_and_policies"]
        TQ["_track_request_queue_dynamics"]
        TDS["_track_driver_state_distribution"]
        TSL["_track_system_load_indicators"]
    end
    
    subgraph STORE["Storage"]
        TS["SimulationTimeSeries<br/>55+ Metrics"]
    end
    
    subgraph REPORT["Report Generation"]
        R1["System Efficiency"]
        R2["Behavior Dynamics"]
        R3["Mutation Analysis"]
        R4["Policy Effectiveness"]
    end
    
    INPUT --> RT
    RT --> TC
    RT --> TO
    RT --> TQ
    RT --> TDS
    RT --> TSL
    TC --> STORE
    TO --> STORE
    TQ --> STORE
    TDS --> STORE
    TSL --> STORE
    STORE --> R1
    STORE --> R2
    STORE --> R3
    STORE --> R4
    
    style INPUT fill:#e1f5ff
    style COLLECT fill:#e8f5e9
    style STORE fill:#f3e5f5
    style REPORT fill:#fce4ec
```

---

These 15 diagrams cover:
- **Overall architecture** (1)
- **Mutation pipeline** (2-3, 5)
- **Data structures** (4)
- **Behavior evolution** (6, 14)
- **Report generation** (7, 13)
- **Specific metrics** (8-12, 15)
- **Analysis & validation** (9-12, 14)

Each diagram is self-contained and can be used independently in your thesis!
