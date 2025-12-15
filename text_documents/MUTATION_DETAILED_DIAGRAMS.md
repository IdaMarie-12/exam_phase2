# Mutation System - Detailed Mermaid Diagrams

Comprehensive visual representations of the HybridMutation strategy with all decision points, thresholds, and exploration mechanics.

## 1. Complete Mutation Decision Flow

```mermaid
graph TD
    A["TICK N<br/>maybe_mutate called"] -->|Entry| B["Check Cooldown<br/>time - last_mutation >= 10?"]
    B -->|In Cooldown| C["RETURN<br/>No mutation allowed"]
    B -->|Can Mutate| D["Calculate avg fare<br/>last 10 trips"]
    D -->|No History| E["RETURN<br/>Insufficient data"]
    D -->|Has Data| F["Get current behaviour"]
    F --> G["Check EXIT Condition<br/>should_exit_behaviour?"]
    G -->|YES - Exit| H["Reset to LazyBehaviour"]
    H --> I["Record exit mutation<br/>Set cooldown<br/>RETURN"]
    G -->|NO - Continue| J["Check Performance<br/>avg fare level"]
    J -->|avg < 3.0<br/>STRUGGLING| K["Switch to<br/>GreedyDistanceBehaviour"]
    J -->|avg > 10.0<br/>THRIVING| L["Switch to<br/>EarningsMaxBehaviour"]
    J -->|3.0 ≤ avg ≤ 10.0<br/>NORMAL RANGE| M["Check Stagnation"]
    K --> N["Record mutation<br/>Set cooldown<br/>RETURN"]
    L --> N
    M -->|Not Stagnating| O["RETURN<br/>No change"]
    M -->|Stagnating| P{Current Behaviour?}
    P -->|LazyBehaviour| Q["FORCE EXPLORE<br/>100% must change"]
    P -->|Greedy or Earnings| R["Generate random [0,1)"]
    R -->|>= 0.3<br/>70%| O
    R -->|< 0.3<br/>30%| Q
    Q --> S["Pick from<br/>2 alternatives<br/>exclude current"]
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

## 2. Earnings Zones and Exit Conditions

```mermaid
graph LR
    A["0"] --> B["3.0"]
    B --> C["5.0"]
    C --> D["7.5"]
    D --> E["10.0"]
    E --> F["∞"]
    
    subgraph Z1["Zone 1: STRUGGLING"]
        A -->|avg < 3.0| B
        T1["Action: Switch to Greedy<br/>Accept more jobs"]
    end
    
    subgraph Z2["Zone 2: RECOVERY"]
        B -->|3.0 ≤ avg < 5.0| C
        T2["Greedy driver here<br/>Exit threshold: 5.0"]
    end
    
    subgraph Z3["Zone 3: NORMAL"]
        C -->|5.0 ≤ avg < 7.5| D
        T3["Evaluate stability<br/>Watch for stagnation"]
    end
    
    subgraph Z4["Zone 4: GOOD"]
        D -->|7.5 ≤ avg < 10.0| E
        T4["Stable performance<br/>Exit threshold: 7.5"]
    end
    
    subgraph Z5["Zone 5: THRIVING"]
        E -->|avg > 10.0| F
        T5["Action: Switch to EarningsMax<br/>Become selective"]
    end
    
    X1["Greedy exits at 5.0<br/>Recovered 1.67x entry"] -.-> C
    X2["EarningsMax exits at 7.5<br/>Dropped 25% from entry"] -.-> D
    
    style Z1 fill:#ffcccc
    style Z2 fill:#fff9c4
    style Z3 fill:#fffacd
    style Z4 fill:#fffacd
    style Z5 fill:#ccffcc
    style X1 fill:#fff0f5
    style X2 fill:#fff0f5
```

## 3. Stagnation Detection Algorithm

```mermaid
graph TD
    A["Driver has history"] --> B["Extract last 10 trips"]
    B --> C["Calculate average fare<br/>avg = sum fares / 10"]
    C --> D["Set tolerance band<br/>tol = avg × 0.05"]
    D --> E["Count fares within band<br/>abs fare - avg ≤ tol?"]
    E --> F["Calculate percentage<br/>within_band_count / 10"]
    F --> G{percentage >= 70%?}
    
    G -->|YES| H["STAGNATING<br/>Low variance detected"]
    G -->|NO| I["HEALTHY VARIATION<br/>Good diversity"]
    
    J["Example:<br/>avg=5.0, tol=0.25<br/>band=[4.75, 5.25]<br/>8/10 in band → 80% ≥ 70%"] -.->|confirms| H
    K["Example:<br/>avg=5.0, tol=0.25<br/>fares=[2,3,7,8,4,9,3,6,2,7]<br/>0/10 in band → 0% < 70%"] -.->|confirms| I
    
    style H fill:#ef5350
    style I fill:#66bb6a
    style J fill:#fff9c4
    style K fill:#fff9c4
```

## 4. Exploration Mechanism (Stagnation Response)

```mermaid
graph TD
    A["Stagnation Detected<br/>Driver is stagnating"] --> B["Get current behaviour"]
    B --> C{Which behaviour?}
    
    C -->|LazyBehaviour| D["FORCED EXPLORATION<br/>100% probability"]
    C -->|GreedyDistanceBehaviour<br/>or EarningsMaxBehaviour| E["PROBABILISTIC EXPLORATION<br/>30% probability"]
    
    D --> F["Must pick different behaviour<br/>2 choices available"]
    E --> G["Random check: < 0.3?"]
    G -->|NO 70%| H["STAY in current<br/>No exploration this tick"]
    G -->|YES 30%| F
    
    F --> I["Available choices<br/>filter out current"]
    I --> J["Random.choice from<br/>remaining 2 behaviours"]
    J --> K{Choice made}
    
    K -->|GreedyDistanceBehaviour| L["Switch to Greedy<br/>Record exploration"]
    K -->|EarningsMaxBehaviour| M["Switch to EarningsMax<br/>Record exploration"]
    K -->|LazyBehaviour| N["Switch to Lazy<br/>Record exploration"]
    
    L --> O["Set cooldown<br/>Next mutation ≥ 10 ticks"]
    M --> O
    N --> O
    H --> P["Continue current<br/>No cooldown change"]
    
    style D fill:#ef5350
    style E fill:#fff9c4
    style H fill:#f0f0f0
    style F fill:#bbdefb
    style O fill:#c8e6c9
    style P fill:#f0f0f0
```

## 5. Exit Conditions by Behaviour

```mermaid
graph TD
    A["Driver in behaviour"] --> B{Which behaviour?}
    
    B -->|GreedyDistanceBehaviour| C["Check exit condition"]
    B -->|EarningsMaxBehaviour| D["Check exit condition"]
    B -->|LazyBehaviour| E["No exit condition<br/>Neutral fallback"]
    
    C --> C1["Is avg >= 5.0?"]
    C1 -->|YES| C2["RECOVERED<br/>Earnings improved 1.67x<br/>from entry threshold 3.0"]
    C1 -->|NO| C3["Still struggling<br/>Stay in Greedy"]
    C2 --> C4["EXIT to LazyBehaviour<br/>Reset cooldown<br/>Next mutation ≥ 10 ticks"]
    C3 --> C5["Continue Greedy"]
    
    D --> D1["Is avg < 7.5?"]
    D1 -->|YES| D2["DETERIORATED<br/>Earnings dropped 25%<br/>from entry threshold 10.0"]
    D1 -->|NO| D3["Still thriving<br/>Stay in EarningsMax"]
    D2 --> D4["EXIT to LazyBehaviour<br/>Reset cooldown<br/>Next mutation ≥ 10 ticks"]
    D3 --> D5["Continue EarningsMax"]
    
    E --> E1["Return False<br/>No exit possible"]
    
    C4 --> F["Record: exit_greedy"]
    D4 --> G["Record: exit_earnings"]
    
    style C2 fill:#ef5350
    style D2 fill:#ef5350
    style E fill:#66bb6a
    style F fill:#c8e6c9
    style G fill:#c8e6c9
```

## 6. Behaviour State Transitions

```mermaid
stateDiagram-v2
    [*] --> Lazy: Initial assignment
    
    Lazy --> Greedy: Performance:<br/>avg < 3.0
    Lazy --> EarningsMax: Performance:<br/>avg > 10.0
    Lazy --> Greedy: Stagnation:<br/>100% explore
    Lazy --> EarningsMax: Stagnation:<br/>100% explore
    
    Greedy --> Lazy: Exit:<br/>avg >= 5.0
    Greedy --> Greedy: Performance:<br/>avg < 5.0<br/>stay stable
    Greedy --> Greedy: Stagnation:<br/>70% stay
    Greedy --> Earnings: Stagnation:<br/>30% explore
    Greedy --> Lazy: Stagnation:<br/>30% explore
    
    EarningsMax --> Lazy: Exit:<br/>avg < 7.5
    EarningsMax --> EarningsMax: Performance:<br/>avg >= 7.5<br/>stay stable
    EarningsMax --> EarningsMax: Stagnation:<br/>70% stay
    EarningsMax --> Greedy: Stagnation:<br/>30% explore
    EarningsMax --> Lazy: Stagnation:<br/>30% explore
    
    style Lazy fill:#fff9c4
    style Greedy fill:#ef5350
    style EarningsMax fill:#42a5f5
```

## 7. Cooldown Timeline and Mutation Windows

```mermaid
timeline
    title Driver Mutation Cycle with 10-Tick Windows

    section Initial Phase
        Tick 0-9 : Collecting history : Building 10-trip window
        Tick 9 : Ready to evaluate : avg calculated
        
    section Mutation Event
        Tick 10 : EVALUATION & DECISION : avg=2.8 < 3.0<br/>→ Switch to Greedy
        
    section Cooldown Phase
        Tick 10 : _last_mutation_time = 10 : Cooldown starts
        Tick 11-19 : COOLDOWN PERIOD : (time - 10) < 10<br/>No mutations allowed
        Tick 11-19 : New history : Collecting trips with Greedy
        
    section Next Mutation Opportunity
        Tick 20 : Cooldown expires : (20 - 10) = 10 ✓<br/>Next mutation allowed
        Tick 20+ : Can evaluate again : New avg calculated<br/>Next decision made
```

## 8. Performance-Based Primary Mutations

```mermaid
graph TD
    A["Calculate avg fare<br/>last 10 trips"] --> B["Not in cooldown?<br/>Not exiting?"]
    B -->|YES| C["Check Performance Level"]
    B -->|NO| D["No primary mutation"]
    
    C --> E{avg value?}
    
    E -->|avg < 3.0<br/>STRUGGLING| F["PRIMARY MUTATION:<br/>Switch to Greedy"]
    E -->|avg > 10.0<br/>THRIVING| G["PRIMARY MUTATION:<br/>Switch to EarningsMax"]
    E -->|3.0 ≤ avg ≤ 10.0<br/>NORMAL RANGE| H["No primary mutation<br/>Check stagnation"]
    
    F --> I["Action:<br/>Accept more jobs<br/>Increase volume"]
    G --> J["Action:<br/>Be more selective<br/>Optimize profit"]
    H --> K["Continue to<br/>secondary check"]
    
    I --> L["Record:<br/>performance_low_earnings"]
    J --> M["Record:<br/>performance_high_earnings"]
    
    style F fill:#ef5350
    style G fill:#42a5f5
    style L fill:#c8e6c9
    style M fill:#c8e6c9
    style K fill:#bbdefb
```

## 9. Secondary Stagnation-Based Mutations

```mermaid
graph TD
    A["In normal earnings range<br/>3.0 ≤ avg ≤ 10.0"] --> B["Check: _is_stagnating?"]
    
    B -->|Not Stagnating| C["RETURN<br/>No change<br/>Keep behaviour"]
    
    B -->|Stagnating| D["SECONDARY MUTATION:<br/>Exploration triggered"]
    
    D --> E{"Current<br/>Behaviour?"}
    
    E -->|Lazy| F["FORCE EXPLORATION<br/>100% chance<br/>Must change"]
    E -->|Greedy| G["PROBABILISTIC EXPLORATION<br/>30% chance<br/>May change"]
    E -->|Earnings| G
    
    F --> H["Pick from 2 options<br/>exclude Lazy"]
    H --> H1{Choice}
    H1 -->|50% each| I["Greedy or Earnings"]
    
    G --> J["Roll random [0,1)"]
    J --> K{<0.3?}
    K -->|YES 30%| L["Pick from 2 options<br/>exclude current"]
    K -->|NO 70%| C
    L --> L1{Choice}
    L1 -->|equal prob| M["3rd behaviour"]
    
    I --> N["Record:<br/>stagnation_exploration"]
    M --> N
    
    style F fill:#ef5350
    style G fill:#fff9c4
    style C fill:#f0f0f0
    style N fill:#c8e6c9
```

## 10. Exploration Choice Mechanism (Current Exclusion)

```mermaid
graph TD
    A["Exploration triggered<br/>Need new behaviour"] --> B["Get current behaviour name<br/>e.g., GreedyDistanceBehaviour"]
    
    B --> C["Extract shorthand:<br/>if 'Greedy' in name → 'greedy'<br/>elif 'Earnings' in name → 'earnings'<br/>else → 'lazy'"]
    
    C --> D["Available pool:<br/>[greedy, earnings, lazy]"]
    
    D --> E["EXCLUDE current<br/>Remove from pool"]
    
    E --> F["Remaining choices<br/>2 options"]
    
    F --> G["Random.choice()"]
    
    G --> H{Selected?}
    
    H -->|greedy| I["GreedyDistanceBehaviour<br/>max_distance=10.0"]
    H -->|earnings| J["EarningsMaxBehaviour<br/>min_reward=0.8"]
    H -->|lazy| K["LazyBehaviour<br/>idle_ticks=5"]
    
    I --> L["Switch behaviour<br/>Record transition<br/>Set cooldown"]
    J --> L
    K --> L
    
    style E fill:#fff9c4
    style F fill:#fff9c4
    style L fill:#c8e6c9
```

## 11. Mutation Recording and Tracking

```mermaid
graph TD
    A["Mutation Occurs"] --> B["Record in<br/>mutation_history"]
    
    B --> C["Dictionary entry:<br/>- time: int<br/>- driver_id: int<br/>- from_behaviour: str<br/>- to_behaviour: str<br/>- reason: str<br/>- avg_fare: float"]
    
    A --> D["Track in<br/>mutation_transitions"]
    
    D --> E["Key: Tuple<br/>from_behaviour, to_behaviour"]
    E --> F["Value: int<br/>count += 1"]
    
    C --> G["Reason Categories:<br/>1. performance_low_earnings<br/>2. performance_high_earnings<br/>3. exit_greedy<br/>4. exit_earnings<br/>5. stagnation_exploration"]
    
    style C fill:#fff9c4
    style G fill:#fff9c4
    style F fill:#c8e6c9
```

## 12. Complete Tick Sequence with Mutation

```mermaid
graph TD
    A["TICK N"] --> B["Phase 1: Generate Requests"]
    B --> C["Phase 2: Expire Requests"]
    C --> D["Phase 3: Get Proposals"]
    D --> E["Phase 4: Collect Offers<br/>Driver uses CURRENT behaviour"]
    E --> F["Phase 5: Resolve Conflicts"]
    F --> G["Phase 6: Assign Requests"]
    G --> H["Phase 7: Move Drivers"]
    H --> I["Phase 8: MUTATE DRIVERS<br/>maybe_mutate called<br/>Behaviour may change"]
    I --> J["Phase 9: Increment Time"]
    J --> K["TICK N+1"]
    K --> L["Phase 4: Collect Offers<br/>Driver uses NEW behaviour<br/>if mutated"]
    
    E -.->|Uses old<br/>behaviour| M["(e.g., Lazy)"]
    I -.->|May switch to<br/>new behaviour| N["(e.g., Greedy)"]
    L -.->|Next tick uses<br/>new behaviour| O["(e.g., Greedy)"]
    
    style E fill:#fff9c4
    style I fill:#bbdefb
    style L fill:#c8e6c9
    style M fill:#f0f0f0
    style N fill:#f0f0f0
    style O fill:#f0f0f0
```

## 13. Data Flow: History → Decision → Mutation

```mermaid
graph LR
    A["driver.history<br/>List of trips"] -->|Last 10| B["get_driver_history_window()"]
    B --> C["List of fare dicts"]
    C --> D["calculate_average_fare()"]
    D --> E["avg_fare: float"]
    
    E --> F["maybe_mutate()"]
    F --> G["HybridMutation<br/>Decision Logic"]
    
    G -->|Low earnings| H["Switch to Greedy<br/>Accept volume"]
    G -->|High earnings| I["Switch to EarningsMax<br/>Be selective"]
    G -->|Stagnating| J["Explore new<br/>Break pattern"]
    G -->|Normal/Healthy| K["No change<br/>Stay current"]
    
    H --> L["driver.behaviour =<br/>GreedyDistanceBehaviour()"]
    I --> M["driver.behaviour =<br/>EarningsMaxBehaviour()"]
    J --> N["driver.behaviour =<br/>picked behaviour"]
    K --> O["driver.behaviour<br/>unchanged"]
    
    L --> P["Next tick:<br/>Uses new behaviour"]
    M --> P
    N --> P
    O --> P
    
    style E fill:#fff9c4
    style G fill:#bbdefb
    style P fill:#c8e6c9
```

## 14. Hysteresis: Entry vs Exit Thresholds

```mermaid
graph LR
    subgraph Entry["Entry Thresholds"]
        A1["avg < 3.0<br/>ENTER Greedy"]
        A2["avg > 10.0<br/>ENTER EarningsMax"]
    end
    
    subgraph Exit["Exit Thresholds"]
        B1["avg >= 5.0<br/>EXIT Greedy<br/>1.67× multiplier"]
        B2["avg < 7.5<br/>EXIT EarningsMax<br/>0.75× reduction"]
    end
    
    subgraph Recovery["Recovery Zone"]
        C["5.0 - 7.5<br/>Transition area<br/>Driver stability"]
    end
    
    A1 -->|Gap: 2.0| B1
    A2 -->|Gap: 2.5| B2
    B1 -.->|Prevents<br/>rapid churn| C
    B2 -.->|Prevents<br/>rapid churn| C
    
    D["Hysteresis Design:<br/>Exit thresholds are NOT the inverse of entry<br/>Creates stable holding zones<br/>Prevents constant switching"] -.-> Recovery
    
    style Entry fill:#ffcccc
    style Exit fill:#ccffff
    style Recovery fill:#ffffcc
    style D fill:#fff0f5
```

## 15. Summary: Mutation Decision Tree

```mermaid
graph TD
    A["maybe_mutate called"] --> B{"Can mutate?<br/>cooldown expired"}
    B -->|NO| Z1["SKIP"]
    B -->|YES| C{"Has history?"}
    C -->|NO| Z2["SKIP"]
    C -->|YES| D{"Should exit<br/>behaviour?"}
    D -->|YES| E["→ Lazy<br/>Record: exit_*"]
    D -->|NO| F{"avg < 3.0?"}
    F -->|YES| G["→ Greedy<br/>Record: performance_low"]
    F -->|NO| H{"avg > 10.0?"}
    H -->|YES| I["→ EarningsMax<br/>Record: performance_high"]
    H -->|NO| J{"Stagnating?"}
    J -->|NO| Z3["STAY"]
    J -->|YES| K{"Lazy?"}
    K -->|YES| L["EXPLORE 100%<br/>→ Greedy or Earnings<br/>Record: exploration"]
    K -->|NO| M{"rand < 0.3?"}
    M -->|YES| L
    M -->|NO| Z3
    
    E --> N["Set cooldown<br/>RETURN"]
    G --> N
    I --> N
    L --> N
    Z1 --> O["END"]
    Z2 --> O
    Z3 --> O
    
    style E fill:#ef5350
    style G fill:#ef5350
    style I fill:#42a5f5
    style L fill:#bbdefb
    style Z1 fill:#f0f0f0
    style Z2 fill:#f0f0f0
    style Z3 fill:#f0f0f0
    style N fill:#c8e6c9
```

