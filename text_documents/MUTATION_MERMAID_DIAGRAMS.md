# Mutation System Mermaid Diagrams (Updated)

Based on the current mutation.py implementation with:
- Fixed 10-tick evaluation window
- Aligned thresholds and cooldown
- Exploration that excludes current behaviour
- Hysteresis-based exit conditions

## 1. Complete Decision Flow (maybe_mutate)

```mermaid
graph TD
    A["TICK N<br/>maybe_mutate called"] -->|Entry| B["Check Cooldown<br/>time - last_mutation >= 10?"]
    B -->|In Cooldown| C["RETURN<br/>Skip mutation"]
    B -->|Can Mutate| D["Calculate avg fare<br/>last 10 trips"]
    D -->|No History| E["RETURN<br/>Insufficient data"]
    D -->|Has Data| F["Get current behaviour name"]
    F --> G["Check EXIT Condition<br/>should_exit_behaviour?"]
    G -->|YES - Exit| H["Reset to LazyBehaviour"]
    H --> I["Record exit mutation<br/>Set cooldown<br/>RETURN"]
    G -->|NO - Continue| J["PRIMARY: Performance Check"]
    J -->|avg < 3.0| K["Switch to<br/>GreedyDistanceBehaviour"]
    J -->|avg > 10.0| L["Switch to<br/>EarningsMaxBehaviour"]
    J -->|3.0 ≤ avg ≤ 10.0| M["Check SECONDARY:<br/>Stagnation?"]
    K --> N["Record performance mutation<br/>Set cooldown<br/>RETURN"]
    L --> N
    M -->|Not Stagnating| O["RETURN<br/>No change"]
    M -->|Stagnating| P{Which behaviour?}
    P -->|Lazy| Q["FORCE EXPLORE<br/>100% must change"]
    P -->|Greedy/<br/>Earnings| R["Check: random < 0.3?"]
    R -->|NO 70%| O
    R -->|YES 30%| Q
    Q --> S["Pick from<br/>2 alternatives"]
    S --> T["Switch to<br/>picked behaviour"]
    T --> N

    style A fill:#e1f5ff
    style C fill:#ffcdd2
    style E fill:#ffcdd2
    style I fill:#c8e6c9
    style N fill:#c8e6c9
    style O fill:#f0f0f0
    style K fill:#ef5350
    style L fill:#42a5f5
    style Q fill:#ef5350
    style T fill:#bbdefb
```

## 2. Earnings Zones (5 Decision Zones)

```mermaid
graph LR
    A["0"] --> B["3.0"]
    B --> C["5.0"]
    C --> D["7.5"]
    D --> E["10.0"]
    E --> F["∞"]
    
    A -->|Zone 1<br/>STRUGGLING<br/>avg < 3.0| B
    B -->|Zone 2<br/>RECOVERY<br/>3.0-5.0| C
    C -->|Zone 3<br/>NORMAL<br/>5.0-7.5| D
    D -->|Zone 4<br/>GOOD<br/>7.5-10.0| E
    E -->|Zone 5<br/>THRIVING<br/>avg > 10.0| F
    
    K1["Entry: Greedy<br/>avg < 3.0"] -.->|Switch to Greedy| B
    K2["Exit: Greedy<br/>avg >= 5.0"] -.->|Reset to Lazy| C
    K3["Entry: EarningsMax<br/>avg > 10.0"] -.->|Switch to EarningsMax| E
    K4["Exit: EarningsMax<br/>avg < 7.5"] -.->|Reset to Lazy| D
    
    style B fill:#ffb74d
    style C fill:#fff9c4
    style D fill:#fff9c4
    style E fill:#81c784
    style F fill:#66bb6a
    style K1 fill:#ffb74d
    style K2 fill:#fff9c4
    style K3 fill:#81c784
    style K4 fill:#fff9c4
```

## 3. Stagnation Detection (Variance Algorithm)

```mermaid
graph TD
    A["Get last 10 trips<br/>_is_stagnating()"] --> B["Extract fares<br/>e.g., [5.0, 5.1, 4.9, 5.2, ...]"]
    B --> C["Calculate average<br/>avg_fare = sum / len"]
    C --> D["Calculate tolerance<br/>tolerance = avg * 0.05"]
    D --> E["Create band<br/>[avg - tol, avg + tol]<br/>e.g., [4.821, 5.329]"]
    E --> F["For each fare:<br/>abs(fare - avg) <= tolerance?"]
    F --> G["Count within band<br/>e.g., 8/8 trips"]
    G --> H["Calculate percentage<br/>8/8 = 100%"]
    H --> I{percentage >= 70%?}
    I -->|YES| J["STAGNATING<br/>Return True"]
    I -->|NO| K["HEALTHY<br/>Return False"]
    
    style J fill:#ef5350
    style K fill:#66bb6a
    
    L["Example Stagnating:<br/>fares=[5.0,5.1,4.9,5.2,...]<br/>avg=5.075, tol=0.254<br/>All within band → 100% >= 70%"] -.->|confirms| J
    M["Example Healthy:<br/>fares=[2.5,8.3,3.8,9.2,...]<br/>avg=5.0, tol=0.25<br/>None within band → 0% < 70%"] -.->|confirms| K
    
    style L fill:#fff9c4
    style M fill:#fff9c4
```

## 4. Exploration Mechanism (30% Rule with Lazy Forcing)

```mermaid
graph TD
    A["Stagnation Detected<br/>avg in 3.0-10.0 range"] --> B["Get current behaviour<br/>e.g., GreedyDistanceBehaviour"]
    B --> C["Extract shorthand<br/>lazy, greedy, or earnings"]
    C --> D{Which behaviour?}
    
    D -->|lazy| E["FORCE EXPLORE<br/>100% must change"]
    D -->|greedy or earnings| F["Generate random: [0, 1)"]
    F --> G["Compare to 0.3"]
    G -->|>= 0.3<br/>70%| H["STAY<br/>No exploration"]
    G -->|< 0.3<br/>30%| E
    
    E --> I["Available behaviours<br/>[greedy, earnings, lazy]"]
    I --> J["Filter out current<br/>2 items remain"]
    J --> K["Random choice from 2"]
    K --> L["Switch to<br/>picked behaviour"]
    L --> M["Record exploration<br/>Set cooldown"]
    H --> N["No change<br/>Keep current"]
    
    style E fill:#ef5350
    style H fill:#fff9c4
    style L fill:#bbdefb
    style M fill:#c8e6c9
    style N fill:#f0f0f0
    
    O["Key Insight:<br/>Lazy drivers always escape stagnation<br/>Active drivers only explore 30%"] -.-> E
    style O fill:#fff9c4
```

## 5. Exit Conditions (Hysteresis)

```mermaid
graph TD
    A["Check EXIT Condition<br/>should_exit_behaviour?"] --> B["Get current behaviour"]
    B --> C{Which behaviour?}
    
    C -->|GreedyDistanceBehaviour| D["Check: avg >= 5.0?"]
    D -->|YES - Recovered| E["EXIT to LazyBehaviour<br/>Earnings improved 1.67x"]
    D -->|NO - Still struggling| F["STAY in Greedy"]
    
    C -->|EarningsMaxBehaviour| G["Check: avg < 7.5?"]
    G -->|YES - Deteriorated| H["EXIT to LazyBehaviour<br/>Earnings dropped 25%"]
    G -->|NO - Still good| I["STAY in EarningsMax"]
    
    C -->|LazyBehaviour| J["NO EXIT<br/>Neutral behaviour"]
    
    E --> K["Record exit_greedy<br/>Set cooldown"]
    H --> L["Record exit_earnings<br/>Set cooldown"]
    J --> M["Return False"]
    F --> M
    I --> M
    
    style E fill:#ef5350
    style H fill:#ef5350
    style K fill:#c8e6c9
    style L fill:#c8e6c9
    style J fill:#66bb6a
```

## 6. State Transition Graph

```mermaid
stateDiagram-v2
    [*] --> Lazy: Initial assignment
    
    Lazy --> Greedy: avg < 3.0<br/>performance
    Lazy --> EarningsMax: avg > 10.0<br/>performance
    Lazy --> Greedy: stagnating<br/>100% explore
    Lazy --> EarningsMax: stagnating<br/>100% explore
    
    Greedy --> Lazy: avg >= 5.0<br/>exit
    Greedy --> Greedy: avg < 5.0
    Greedy --> Greedy: stagnating + 70%<br/>stay
    Greedy --> EarningsMax: stagnating + 30%<br/>explore
    Greedy --> Lazy: stagnating + 30%<br/>explore
    
    EarningsMax --> Lazy: avg < 7.5<br/>exit
    EarningsMax --> EarningsMax: avg >= 7.5
    EarningsMax --> EarningsMax: stagnating + 70%<br/>stay
    EarningsMax --> Greedy: stagnating + 30%<br/>explore
    EarningsMax --> Lazy: stagnating + 30%<br/>explore
    
    style Lazy fill:#fff9c4
    style Greedy fill:#ef5350
    style EarningsMax fill:#42a5f5
```

## 7. Cooldown and Evaluation Windows (Timeline)

```mermaid
timeline
    title Mutation Cycle: 10-Tick Windows

    section Driver 1
        Ticks 0-10 : Initial Behaviour : Collecting history
        Tick 10 : Evaluation & Mutation : avg=2.8 < 3.0 → Greedy
        Ticks 11-20 : Greedy Cooldown : Executing Greedy strategy
        Ticks 11-20 : New History : 10 trips collected
        Tick 20 : Next Evaluation : Decide based on new avg
        
    section Cooldown Rules
        Mutation Time : tick 10 : _last_mutation_time = 10
        Cooldown Period : ticks 11-19 : (time - 10) < 10
        Cooldown Ends : tick 20 : (20 - 10) = 10 >= 10 ✓
        Next Mutation Allowed : tick 20+
```

## 8. HybridMutation Initialization

```mermaid
graph TD
    A["HybridMutation()"] --> B["Parameters<br/>Only 4 required:"]
    B --> C["low_threshold<br/>default: 3.0"]
    B --> D["high_threshold<br/>default: 10.0"]
    B --> E["cooldown_ticks<br/>default: 10"]
    B --> F["exploration_prob<br/>default: 0.3"]
    
    A --> G["Internal State<br/>Fixed/Derived:"]
    G --> H["eval_window: 10 ticks<br/>FIXED - not configurable"]
    G --> I["mutation_transitions<br/>Dict tracking counts"]
    G --> J["mutation_history<br/>List tracking details"]
    G --> K["greedy_exit: 5.0<br/>earnings_max_exit: 7.5"]
    
    style C fill:#fff9c4
    style D fill:#fff9c4
    style E fill:#fff9c4
    style F fill:#fff9c4
    style H fill:#bbdefb
```

## 9. Behaviour Parameters

```mermaid
graph TD
    A["Behaviour Strategies"] --> B["GreedyDistanceBehaviour<br/>GREEDY_MAX_DISTANCE = 10.0"]
    A --> C["EarningsMaxBehaviour<br/>EARNINGS_MIN_REWARD_PER_TIME = 0.8"]
    A --> D["LazyBehaviour<br/>LAZY_IDLE_TICKS_NEEDED = 5<br/>LAZY_MAX_DISTANCE = 5.0"]
    
    B --> B1["decide(): distance <= 10.0?<br/>When: avg < 3.0<br/>Goal: Increase job volume"]
    C --> C1["decide(): reward/time >= 0.8?<br/>When: avg > 10.0<br/>Goal: Optimize profit margin"]
    D --> D1["decide(): idle >= 5 AND distance < 5?<br/>When: reset/normal<br/>Goal: Neutral/exploratory"]
    
    style B fill:#ef5350
    style C fill:#42a5f5
    style D fill:#fff9c4
```

## 10. Complete Simulation Tick Sequence

```mermaid
graph TD
    A["TICK N"] --> B["Phase 1: Generate Requests"]
    B --> C["Phase 2: Expire Requests"]
    C --> D["Phase 3: Get Proposals"]
    D --> E["Phase 4: Collect Offers<br/>Uses CURRENT behaviour"]
    E --> F["Phase 5: Resolve Conflicts"]
    F --> G["Phase 6: Assign Requests"]
    G --> H["Phase 7: Move Drivers"]
    H --> I["Phase 8: MUTATE DRIVERS<br/>Behaviour changed here"]
    I --> J["Phase 9: Increment Time"]
    J --> K["TICK N+1"]
    K --> L["Phase 4: Collect Offers<br/>Uses NEW behaviour"]
    
    style E fill:#fff9c4
    style I fill:#bbdefb
    style L fill:#c8e6c9
```

## 11. Mutation Recording & Data Tracking

```mermaid
graph TD
    A["Mutation Occurs"] --> B["Record in mutation_history"]
    B --> C["Entry Dict:<br/>- time: int<br/>- driver_id: int<br/>- from_behaviour: str<br/>- to_behaviour: str<br/>- reason: str<br/>- avg_fare: float"]
    C --> D["Track in mutation_transitions"]
    D --> E["Key: Tuple<br/>(from_behaviour, to_behaviour)"]
    E --> F["Value: int<br/>Count of transitions"]
    
    C --> G["Reason Types:<br/>- performance_low_earnings<br/>- performance_high_earnings<br/>- exit_greedy<br/>- exit_earnings<br/>- stagnation_exploration"]
    
    style C fill:#fff9c4
    style G fill:#fff9c4
```

## 12. Data Flow: History to Mutation

```mermaid
graph LR
    A["driver.history"] -->|Last 10 trips| B["get_driver_history_window()<br/>default window=10"]
    B --> C["List[Dict]<br/>fare entries"]
    C --> D["calculate_average_fare()"]
    D --> E["avg_fare: float"]
    E --> F["maybe_mutate()"]
    F --> G{Decision<br/>made}
    G -->|avg < 3.0| H["Switch to Greedy<br/>accept more volume"]
    G -->|avg > 10.0| I["Switch to EarningsMax<br/>become selective"]
    G -->|Stagnating| J["Explore<br/>try something new"]
    G -->|Normal| K["Stay<br/>current behaviour"]
    
    style A fill:#e3f2fd
    style E fill:#fff9c4
    style H fill:#ef5350
    style I fill:#42a5f5
    style J fill:#bbdefb
    style K fill:#f0f0f0
```

## 13. Stagnation Variance Algorithm Details

```mermaid
graph TD
    A["Stagnation Detection<br/>_is_stagnating()"] --> B["Require minimum<br/>len history >= 2"]
    B --> C["Extract fares list<br/>fares = [...]"]
    C --> D["Calculate average<br/>sum(fares) / len"]
    D --> E["Validate avg > 0.1<br/>Avoid division issues"]
    E --> F["Calculate tolerance<br/>tol = avg * 0.05"]
    F --> G["For each fare f:<br/>abs f - avg <= tol?"]
    G --> H["Count within-band fares<br/>stagnant_count"]
    H --> I["Check threshold<br/>count >= len * 0.7"]
    I -->|YES| J["Return True"]
    I -->|NO| K["Return False"]
    
    style J fill:#ef5350
    style K fill:#66bb6a
```

## 14. Exploration with Current Behaviour Exclusion

```mermaid
graph TD
    A["Exploration Check<br/>_is_stagnating() AND<br/>random() < 0.3"] --> B["Get current behaviour name<br/>old_behaviour_name"]
    B --> C["Extract shorthand<br/>split on 'B' + lowercase<br/>e.g., Greedy→greedy"]
    C --> D["All available<br/>[greedy, earnings, lazy]"]
    D --> E["Filter exclusion<br/>remove current_short"]
    E --> F["available_choices<br/>2 items remaining"]
    F --> G["random.choice<br/>from available_choices"]
    G --> H{which choice?}
    H -->|greedy| I["GreedyDistanceBehaviour"]
    H -->|earnings| J["EarningsMaxBehaviour"]
    H -->|lazy| K["LazyBehaviour"]
    I --> L["Switch behaviour<br/>Record exploration<br/>Set cooldown"]
    J --> L
    K --> L
    
    style E fill:#fff9c4
    style F fill:#fff9c4
    style L fill:#c8e6c9
```

## 15. Mutation Metrics and Reporting

```mermaid
graph TD
    A["Mutation System<br/>Output Data"] --> B["mutation_transitions<br/>Dict[Tuple, int]"]
    B --> C["Aggregate Counts<br/>Example:<br/>Greedy→Earnings: 12<br/>Earnings→Lazy: 8<br/>Lazy→Greedy: 15"]
    
    A --> D["mutation_history<br/>List[Dict]"]
    D --> E["Detailed Records<br/>Each mutation:<br/>time, driver_id<br/>from/to, reason<br/>avg_fare, ..."]
    
    C --> F["Analysis Possible<br/>- Strategy distribution<br/>- Transition patterns<br/>- Success rate<br/>- Duration in each"]
    
    E --> F
    
    style C fill:#fff9c4
    style E fill:#fff9c4
    style F fill:#c8e6c9
```

    HybridMutation --> Driver
    HybridMutation --> DriverBehaviour
    Driver --> DriverBehaviour
```

## Simplified View (Focus on Mutation)

```mermaid
classDiagram
    class MutationRule {
        maybe_mutate(driver Driver, time int)
    }

    class HybridMutation {
        last_mutation_time dict
        maybe_mutate(driver Driver, time int)
    }

    class DriverBehaviour {
        decide(driver Driver, offer Offer, time int)
    }

    class GreedyDistanceBehaviour {
        max_distance float
    }

    class EarningsMaxBehaviour {
        threshold float
    }

    class LazyBehaviour {
        idle_ticks_needed int
    }

    class Driver {
        id int
        behaviour DriverBehaviour
        history list
        earnings float
        idle_since int
    }

    MutationRule <|-- HybridMutation
    DriverBehaviour <|-- GreedyDistanceBehaviour
    DriverBehaviour <|-- EarningsMaxBehaviour
    DriverBehaviour <|-- LazyBehaviour
    HybridMutation --> Driver : mutates
    HybridMutation --> DriverBehaviour : creates
    Driver --> DriverBehaviour
```

## Mutation Flow Diagram

```mermaid
graph TD
    A["Driver at time T"] --> B["HybridMutation.maybe_mutate"]
    B --> C{Cooldown active?}
    C -->|Yes| D["No mutation"]
    C -->|No| E{Check Earnings}
    E -->|avg < 3.0| F["Switch to GREEDY"]
    E -->|avg > 10.0| G["Switch to EARNINGS_MAX"]
    E -->|3.0 <= avg <= 10.0| H{Stagnation 8 ticks?}
    H -->|Yes| I["30% explore new"]
    H -->|No| D
    I --> J["Update driver.behaviour"]
    F --> J
    G --> J
    J --> K["Record mutation time"]
    K --> L["Continue with new behaviour"]
```

## State Machine: Behaviour Transitions

```mermaid
stateDiagram-v2
    [*] --> Lazy
    Lazy --> Greedy: Low earnings 3.0
    Lazy --> EarningsMax: High earnings 10.0
    Lazy --> Random: Stagnation 30pct
    Greedy --> Lazy: High earnings
    Greedy --> EarningsMax: Improvement
    Greedy --> Random: Stagnation
    EarningsMax --> Lazy: Low earnings
    EarningsMax --> Greedy: Decline
    EarningsMax --> Random: Stagnation
    Random --> Lazy: Complete
    Random --> Greedy: Complete
    Random --> EarningsMax: Complete
```

## Sequence Diagram: Mutation During Tick

```mermaid
sequenceDiagram
    participant Sim as Simulation
    participant HR as HybridMutation
    participant D as Driver
    
    Sim->>HR: maybe_mutate(driver, time)
    HR->>HR: Check cooldown
    alt Cooldown expires
        HR->>D: Get history
        D-->>HR: history list
        HR->>HR: calc_avg_earnings
        alt avg < 3.0
            HR->>D: Create GreedyBehaviour
            D-->>HR: new behaviour
        else avg > 10.0
            HR->>D: Create EarningsMaxBehaviour
            D-->>HR: new behaviour
        else stagnation + 30pct
            HR->>D: Create random behaviour
            D-->>HR: new behaviour
        end
        HR->>D: Update behaviour
        HR->>HR: Record mutation time
        HR-->>Sim: Done
    else Cooldown active
        HR-->>Sim: Skip
    end
```

## Configuration Constants as Diagram

```mermaid
graph LR
    subgraph HParams["HybridMutation Parameters"]
        A["LOW_THRESHOLD = 3.0"]
        B["HIGH_THRESHOLD = 10.0"]
        C["COOLDOWN = 10 ticks"]
        D["STAGNATION_WINDOW = 8"]
        E["EXPLORE_PROB = 0.3"]
    end
    
    subgraph BParams["Behaviour Parameters"]
        F["GREEDY_DISTANCE = 10.0"]
        G["EARNINGS_RATIO = 0.8"]
        H["LAZY_TICKS = 5"]
        I["LAZY_DISTANCE = 5.0"]
    end
    
    A -.-> A1["Greedy"]
    B -.-> B1["EarningsMax"]
    C -.-> C1["No Churn"]
    D -.-> D1["Detect Plateau"]
    E -.-> E1["Explore"]
```

## Metrics Data Collection Pipeline

```mermaid
graph TD
    Sim["DeliverySimulation<br/>per tick"] --> T1["1. Generate Requests"]
    T1 --> T2["2. Expire Requests"]
    T2 --> T3["3. Propose Offers"]
    T3 --> T4["4. Collect Decisions"]
    T4 --> T5["5. Resolve Conflicts"]
    T5 --> T6["6. Assign Requests"]
    T6 --> T7["7. Move Drivers"]
    T7 --> T8["8. Mutate Drivers"]
    T8 --> T9["9. Increment Time"]
    
    T9 --> Snapshot["get_snapshot()"]
    Snapshot --> TS["SimulationTimeSeries<br/>record_tick"]
    
    TS --> M1["Track: served_count"]
    TS --> M2["Track: expired_count"]
    TS --> M3["Track: avg_wait"]
    TS --> M4["Track: pending_count"]
    TS --> M5["Track: utilization"]
    TS --> M6["Track: behaviour_dist"]
    TS --> M7["Track: mutations"]
    TS --> M8["Track: stagnation"]
    TS --> M9["Track: times"]
    
    M1 --> Storage["SimulationTimeSeries<br/>Storage"]
    M2 --> Storage
    M3 --> Storage
    M4 --> Storage
    M5 --> Storage
    M6 --> Storage
    M7 --> Storage
    M8 --> Storage
    M9 --> Storage
```

## Metrics to Visualizations Flow

```mermaid
graph TD
    Storage["SimulationTimeSeries<br/>Stored Data"] --> Report["generate_report"]
    
    Report --> W1["Window 1: Metrics Report"]
    Report --> W2["Window 2: Behaviour Analysis"]
    Report --> W3["Window 3: Mutation Analysis"]
    
    W1 --> P1A["Plot: Served vs Expired"]
    W1 --> P1B["Plot: Wait Time Evolution"]
    W1 --> P1C["Plot: Pending Requests"]
    W1 --> P1D["Plot: Driver Utilization"]
    W1 --> P1E["Plot: Summary Statistics"]
    
    W2 --> P2A["Plot: Behaviour Distribution"]
    W2 --> P2B["Plot: Behaviour Evolution"]
    W2 --> P2C["Stats: Behaviour Summary"]
    
    W3 --> P3A["Plot: Rule Configuration"]
    W3 --> P3B["Plot: Impact Metrics"]
    W3 --> P3C["Plot: Mutations/Stagnation"]
```

## Data Collection During Single Tick

```mermaid
graph LR
    subgraph "Tick Start"
        T1["time = N<br/>served = X<br/>expired = Y"]
    end
    
    subgraph "Phase Execution"
        P1["Generate"]
        P2["Expire"]
        P3["Propose"]
        P4["Collect"]
        P5["Resolve"]
        P6["Assign"]
        P7["Move"]
        P8["Mutate"]
    end
    
    subgraph "Tick End"
        T2["Accumulate:<br/>- New requests<br/>- Expired count<br/>- Completed trips<br/>- Updated earnings"]
    end
    
    subgraph "Record Metrics"
        R1["Calculate:<br/>- served += completed<br/>- expired += expired<br/>- avg_wait = total/count<br/>- pending = active<br/>- utilization = busy/total"]
    end
    
    subgraph "Store in TimeSeries"
        S1["times.append N"]
        S2["served.append X+delta"]
        S3["expired.append Y+delta"]
        S4["behaviour_dist.append dict"]
        S5["mutations.append total"]
        S6["stagnation.append count"]
    end
    
    T1 --> P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7 --> P8
    P8 --> T2
    T2 --> R1
    R1 --> S1
    R1 --> S2
    R1 --> S3
    R1 --> S4
    R1 --> S5
    R1 --> S6
```

## Metrics Calculation Formulas

```mermaid
graph TD
    A["served_count"] -->|cumulative| A1["Total delivered"]
    B["expired_count"] -->|cumulative| B1["Total expired"]
    C["wait_time per request"] -->|average| C1["avg_wait = sum/count"]
    D["requests in system"] -->|count| D1["pending = WAITING+ASSIGNED+PICKED"]
    E["drivers with requests"] -->|ratio| E1["utilization = busy/total * 100%"]
    F["behaviour.__class__.__name__"] -->|histogram| F1["behaviour_dist = Counter"]
    G["mutation events"] -->|cumulative| G1["mutations = total_count"]
    H["unchanged behaviour"] -->|count| H1["stagnation = static_drivers"]
    
    A1 --> Calc["Statistical Summary"]
    B1 --> Calc
    C1 --> Calc
    D1 --> Calc
    E1 --> Calc
    F1 --> Calc
    G1 --> Calc
    H1 --> Calc
    
    Calc --> Out["Ready for Plotting"]
```

## Request Lifecycle Metrics

```mermaid
graph TD
    R["Request Created<br/>time=T0"] --> W["WAITING<br/>increment pending"]
    W --> A["ASSIGNED<br/>track target"]
    A --> P["PICKED<br/>wait_time updated"]
    P --> D["DELIVERED<br/>increment served<br/>record wait_time"]
    
    R --> E["EXPIRED<br/>age >= timeout<br/>increment expired"]
    
    D --> Stats["Update Statistics:<br/>served_count++<br/>avg_wait recalc"]
    E --> Stats
    
    Stats --> TS["Record in<br/>SimulationTimeSeries"]
```

## Behaviour Distribution Tracking

```mermaid
graph TD
    Drivers["All Drivers"] --> Extract["For each driver:<br/>get behaviour type"]
    Extract --> Count["Counter()"]
    
    Count --> C1["GreedyDistance<br/>count = 5"]
    Count --> C2["EarningsMax<br/>count = 3"]
    Count --> C3["LazyBehaviour<br/>count = 2"]
    
    C1 --> Dict["Dict:<br/>GreedyDistance: 5<br/>EarningsMax: 3<br/>LazyBehaviour: 2"]
    C2 --> Dict
    C3 --> Dict
    
    Dict --> TS["Append to<br/>behaviour_distribution<br/>list"]
    
    TS --> Time["Repeat every tick<br/>shows evolution"]
```
