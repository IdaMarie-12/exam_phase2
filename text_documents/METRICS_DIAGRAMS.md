# Metrics and Reporting System - Mermaid Diagrams

## 1. Data Flow Architecture (Integrated Single Flow)

```mermaid
graph LR
    A["Simulation Tick"] --> B["Phase 1-7:<br/>Simulation Logic"]
    B --> C["Phase 8:<br/>Mutation Rule<br/>maybe_mutate()"]
    C --> D["mutation_history<br/>{reason, driver_id, ...}"]
    
    B --> E["After All Phases:<br/>Record Metrics<br/>record_tick()"]
    
    E --> F["Calculate Metrics<br/>Service level, utilization,<br/>request ages, offers"]
    E --> G["Append Time-Series<br/>times, served, expired,<br/>utilization, ..."]
    
    D --> H["Within record_tick():<br/>_track_mutation_reasons()"]
    H --> I["Normalize Reasons<br/>exit_greedy, low_earnings,<br/>stagnation, ..."]
    I --> J["Append Distribution<br/>mutation_reasons List"]
    
    E --> K["Track Behaviours<br/>_track_behaviour_distribution()"]
    K --> L["Append Distribution<br/>behaviour_distribution List"]
    
    F & G & J & L --> M["Complete Tick<br/>Recording"]
    
    M --> N["get_final_summary()"]
    N --> O["Report Windows<br/>generate_report()"]
    
    O --> P["Window 1:<br/>System Efficiency"]
    O --> Q["Window 2:<br/>Behaviour Dynamics"]
    O --> R["Window 3:<br/>Mutation Analysis"]
    O --> S["Window 4:<br/>Policy & Offers"]
    
    style A fill:#e1f5ff
    style C fill:#fff3e0
    style E fill:#e8f5e9
    style H fill:#ffccbc
    style M fill:#c8e6c9
    style N fill:#f3e5f5
    style O fill:#fce4ec
```

## 2. SimulationTimeSeries Class Structure

```mermaid
graph TB
    subgraph "SimulationTimeSeries"
        direction LR
        subgraph "Time-Series Lists"
            A1["times: List[int]"]
            A2["served: List[int]"]
            A3["expired: List[int]"]
            A4["service_level: List[float]"]
            A5["utilization: List[float]"]
            A6["pending_requests: List[int]"]
            A7["avg_request_age: List[float]"]
            A8["max_request_age: List[float]"]
            A9["mutations_per_tick: List[int]"]
            A10["offers_generated: List[int]"]
            A11["matching_efficiency: List[float]"]
            A12["rejection_rate: List[float]"]
        end
        
        subgraph "Distribution Snapshots"
            B1["behaviour_distribution: List[Dict]"]
            B2["mutation_reasons: List[Dict]"]
            B3["actual_policy_used: List[str]"]
        end
        
        subgraph "Aggregation Data"
            C1["driver_mutation_freq: Dict[id, count]"]
            C2["policy_names: Set[str]"]
            C3["_mutation_reason_counts: Dict"]
        end
        
        subgraph "Methods"
            M1["record_tick(simulation)"]
            M2["get_final_summary()"]
            M3["_track_mutation_reasons()"]
            M4["_track_behaviour_distribution()"]
        end
    end
    
    M1 --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12
    M1 --> B1 & B2 & B3
    M3 --> C3
    M2 --> C1 & C2 & C3
    
    style A1 fill:#e3f2fd
    style B1 fill:#f3e5f5
    style C1 fill:#fff3e0
    style M1 fill:#c8e6c9
    style M2 fill:#ffccbc
```

## 3. Mutation Reason Tracking Flow

```mermaid
graph LR
    A["HybridMutation<br/>maybe_mutate()"] -->|records| B["mutation_history<br/>List"]
    B --> C{Reason Type}
    
    C -->|"exit_greedydistancebehaviour"| D["exit_greedy"]
    C -->|"exit_earningsmaxbehaviour"| E["exit_earnings"]
    C -->|"exit_lazybehaviour"| F["exit_lazy"]
    C -->|"performance_low_earnings"| G["low_earnings"]
    C -->|"performance_high_earnings"| H["high_earnings"]
    C -->|"stagnation_exploration"| I["stagnation"]
    
    B --> J["_track_mutation_reasons()<br/>Normalization"]
    
    D & E & F & G & H & I --> J
    
    J --> K["mutation_reason_counts<br/>Dict{reason: count}"]
    
    K --> L["Cumulative Tracking<br/>mutation_reasons List"]
    
    L --> M["Stacked Area Plot<br/>Window 3"]
    
    style A fill:#fff3e0
    style J fill:#ffccbc
    style M fill:#fce4ec
    style K fill:#f3e5f5
```

## 4. Report Window Layout

```mermaid
graph TB
    subgraph "Window 1: System Efficiency (6 plots)"
        W1A["Request Evolution<br/>Served vs Expired"]
        W1B["Service Level %"]
        W1C["Pending Requests"]
        W1D["Driver Utilization<br/>+ 100% threshold"]
        W1E["Request Age Pressure<br/>+ Timeout line"]
        W1F["Summary Statistics<br/>Text box"]
    end
    
    subgraph "Window 2: Behaviour Dynamics (4 plots)"
        W2A["Behaviour Distribution<br/>Evolution<br/>Stacked Area"]
        W2B["Final Distribution<br/>Pie Chart"]
        W2C["All Behaviour Types<br/>Bar Chart"]
        W2D["Behaviour Statistics<br/>Text box"]
    end
    
    subgraph "Window 3: Mutation Analysis (3 plots)"
        W3A["Cumulative Mutations<br/>Line Chart"]
        W3B["Mutation Reasons<br/>Stacked Area<br/>by Reason Type"]
        W3C["Driver Mutation<br/>Frequency<br/>Histogram"]
    end
    
    subgraph "Window 4: Policy & Offers (5 plots)"
        W4A["Offers Generated<br/>Per Tick"]
        W4B["Matching Efficiency %"]
        W4C["Offer Quality<br/>Reward/Time"]
        W4D["Rejection Rate %"]
        W4E["Policy Adoption<br/>Over Time<br/>Cumulative"]
        W4F["Policy & Offer<br/>Summary<br/>Text box"]
    end
    
    style W1A fill:#e3f2fd
    style W2A fill:#f3e5f5
    style W3B fill:#ffe0b2
    style W4E fill:#c8e6c9
```

## 5. Plotting Function Architecture

```mermaid
graph TB
    A["generate_report()"]
    
    A --> B["_show_metrics_window()"]
    A --> C["_show_behaviour_window()"]
    A --> D["_show_mutation_root_cause_window()"]
    A --> E["_show_policy_offer_window()"]
    
    B --> B1["_plot_requests_evolution()"]
    B --> B2["_plot_service_level_evolution()"]
    B --> B3["_plot_utilization_evolution()"]
    B --> B4["_plot_pending_requests()"]
    B --> B5["_plot_request_age_evolution()"]
    B --> B6["_plot_summary_statistics()"]
    
    C --> C1["_plot_behaviour_distribution_evolution()"]
    C --> C2["Pie chart<br/>final distribution"]
    C --> C3["Bar chart<br/>all types"]
    C --> C4["_plot_behaviour_statistics()"]
    
    D --> D1["_plot_cumulative_mutations()"]
    D --> D2["_plot_mutation_reasons_evolution()"]
    D --> D3["_plot_driver_mutation_frequency()"]
    
    E --> E1["_plot_offers_generated()"]
    E --> E2["_plot_matching_efficiency()"]
    E --> E3["_plot_offer_quality()"]
    E --> E4["_plot_rejection_rate()"]
    E --> E5["_plot_policy_distribution()"]
    E --> E6["_plot_policy_offer_summary()"]
    
    B1 & B2 & B3 & B4 & E1 & E3 --> UTIL["_plot_time_series()"]
    
    style UTIL fill:#ffccbc
    style A fill:#e1f5ff
    style B fill:#e3f2fd
    style C fill:#f3e5f5
    style D fill:#ffe0b2
    style E fill:#c8e6c9
```

## 6. Metrics Collection Sequence (Single Integrated Flow)

```mermaid
sequenceDiagram
    participant SIM as Simulation
    participant MUT as HybridMutation
    participant TS as TimeSeries

    loop Each Tick
        Note over SIM: Phases 1-7
        SIM ->> SIM: Process requests,<br/>match drivers, etc.
        
        Note over SIM: Phase 8 - Mutation
        SIM ->> MUT: maybe_mutate()
        MUT ->> MUT: _record_mutation()
        MUT ->> MUT: mutation_history.append({<br/>reason, driver_id, ...})
        
        Note over SIM: After All Phases
        SIM ->> TS: record_tick(simulation)
        
        Note over TS: Calculate & Snapshot
        TS ->> TS: Service level %
        TS ->> TS: Utilization %
        TS ->> TS: Request ages
        TS ->> TS: Offer statistics
        
        Note over TS: Append Time-Series
        TS ->> TS: Append to times,<br/>served, expired, etc.
        
        Note over TS: Track Mutations<br/>(Read from mutation_history)
        TS ->> TS: _track_mutation_reasons()
        TS ->> TS: Normalize & count
        TS ->> TS: mutation_reasons.append(dict)
        
        Note over TS: Track Behaviours
        TS ->> TS: _track_behaviour_distribution()
        TS ->> TS: behaviour_distribution.append(dict)
    end
    
    SIM ->> TS: get_final_summary()
    TS -->> SIM: {30+ aggregated fields}
    
    SIM ->> TS: generate_report()
    TS -->> SIM: Report windows
```

## 7. Mutation Reason Normalization

```mermaid
graph LR
    A["mutation_history from<br/>HybridMutation"]
    
    A --> B["Raw Reason Strings"]
    B --> B1["'exit_greedydistancebehaviour'"]
    B --> B2["'exit_earningsmaxbehaviour'"]
    B --> B3["'exit_lazybehaviour'"]
    B --> B4["'performance_low_earnings'"]
    B --> B5["'performance_high_earnings'"]
    B --> B6["'stagnation_exploration'"]
    
    B1 --> C["_track_mutation_reasons()<br/>Normalize & Count"]
    B2 --> C
    B3 --> C
    B4 --> C
    B5 --> C
    B6 --> C
    
    C --> D["Normalized Keys<br/>mutation_reason_counts"]
    D --> D1["'exit_greedy'"]
    D --> D2["'exit_earnings'"]
    D --> D3["'exit_lazy'"]
    D --> D4["'performance_low_earnings'"]
    D --> D5["'performance_high_earnings'"]
    D --> D6["'stagnation_exploration'"]
    
    D --> E["Store Cumulative<br/>mutation_reasons List<br/>per Tick"]
    
    E --> F["Visualization<br/>Stacked Area<br/>Window 3"]
    
    style B1 fill:#ffccbc
    style D1 fill:#ffeb3b
    style E fill:#c8e6c9
    style F fill:#fce4ec
```

## 8. No-Data Handling Flow

```mermaid
graph TB
    A["Plotting Function<br/>e.g., _plot_time_series()"]
    
    A --> B{Data Check:<br/>Is data None<br/>or empty?}
    
    B -->|YES| C["Display<br/>No data message"]
    C --> D["Gray text in<br/>center of plot"]
    D --> E["Return early"]
    
    B -->|NO| F["Plot normally<br/>Lines, fills,<br/>labels"]
    F --> G["Apply formatting<br/>Title, labels,<br/>grid"]
    G --> H["Legend if needed"]
    
    E --> I["Graceful<br/>Degradation"]
    H --> I
    
    style B fill:#fff3e0
    style C fill:#ffccbc
    style F fill:#c8e6c9
    style I fill:#e1f5ff
```

## 9. Policy Adoption Tracking (AdaptiveHybridPolicy)

```mermaid
graph LR
    A["Simulation<br/>get_proposals()"]
    
    A --> B{Which sub-policy<br/>selected?}
    
    B -->|Request count ≤<br/>Driver count| C["NearestNeighborPolicy"]
    B -->|Request count ><br/>Driver count| D["GlobalGreedyPolicy"]
    
    C --> E["actual_policy_used<br/>List"]
    D --> E
    
    E --> F["_track_policy_usage()"]
    
    F --> G["Policy cumulative<br/>tracking"]
    
    G --> H["Stacked Area Plot<br/>Window 4"]
    
    H --> I["Shows which<br/>sub-policy was<br/>used each tick"]
    
    style C fill:#c8e6c9
    style D fill:#ffccbc
    style H fill:#fce4ec
```

## 10. Summary Statistics Generation

```mermaid
graph TB
    A["get_final_summary()"]
    
    A --> B["System Metrics"]
    B --> B1["total_served"]
    B --> B2["total_expired"]
    B --> B3["avg_service_level"]
    B --> B4["avg_utilization"]
    B --> B5["utilization_variance"]
    
    A --> C["Behaviour Metrics"]
    C --> C1["behaviour_distribution"]
    C --> C2["behaviour_transition_count"]
    
    A --> D["Mutation Metrics"]
    D --> D1["total_mutations"]
    D --> D2["mutation_reason_breakdown"]
    D --> D3["driver_mutation_freq"]
    
    A --> E["Policy Metrics"]
    E --> E1["policy_names"]
    E --> E2["actual_policy_usage"]
    E --> E3["avg_acceptance_rate"]
    
    A --> F["Offer Metrics"]
    F --> F1["total_offers_generated"]
    F --> F2["avg_matching_efficiency"]
    F --> F3["avg_offer_quality"]
    F --> F4["avg_rejection_rate"]
    
    B1 & B2 & B3 & B4 & B5 & C1 & C2 & D1 & D2 & D3 & E1 & E2 & E3 & F1 & F2 & F3 & F4 --> G["Dict: 30+ fields"]
    
    style A fill:#e1f5ff
    style B fill:#e3f2fd
    style C fill:#f3e5f5
    style D fill:#ffe0b2
    style E fill:#c8e6c9
    style F fill:#ffccbc
    style G fill:#fff9c4
```

## 11. Record Tick Method Flow

```mermaid
graph TD
    A["record_tick(simulation)"]
    
    A --> B["Get Current State"]
    B --> B1["simulation.time"]
    B --> B2["Driver statuses"]
    B --> B3["Request queues"]
    B --> B4["mutation_rule"]
    
    B1 & B2 & B3 & B4 --> C["Calculate Metrics"]
    C --> C1["Service level %"]
    C --> C2["Utilization %"]
    C --> C3["Request ages"]
    C --> C4["Offer statistics"]
    
    C1 & C2 & C3 & C4 --> D["Append to Lists"]
    D --> D1["times.append(now)"]
    D --> D2["service_level.append(pct)"]
    D --> D3["utilization.append(pct)"]
    
    B4 --> E["Track Mutations"]
    E --> E1["_track_mutation_reasons()"]
    E --> E2["mutation_reasons.append(dict)"]
    
    B2 --> F["Track Behaviours"]
    F --> F1["_track_behaviour_distribution()"]
    F --> F2["behaviour_distribution.append(dict)"]
    
    D1 & E2 & F2 --> G["Complete"]
    
    style A fill:#e1f5ff
    style C fill:#c8e6c9
    style D fill:#ffccbc
    style E fill:#ffe0b2
    style F fill:#f3e5f5
```

## 12. Stacked Area Data Structure for Mutations

```mermaid
graph TB
    A["mutation_reasons List<br/>per Tick"]
    
    A --> T1["Tick 0: {<br/>low_earnings: 0,<br/>high_earnings: 0,<br/>exit_greedy: 0,<br/>exit_earnings: 0,<br/>exit_lazy: 0,<br/>stagnation: 1<br/>}"]
    
    A --> T2["Tick 1: {<br/>low_earnings: 0,<br/>high_earnings: 0,<br/>exit_greedy: 1,<br/>exit_earnings: 0,<br/>exit_lazy: 0,<br/>stagnation: 2<br/>}"]
    
    A --> T3["Tick N: {<br/>low_earnings: 5,<br/>high_earnings: 3,<br/>exit_greedy: 12,<br/>exit_earnings: 8,<br/>exit_lazy: 0,<br/>stagnation: 45<br/>}"]
    
    T1 & T2 & T3 --> B["Values are<br/>CUMULATIVE<br/>from start"]
    
    B --> C["Stacked Area<br/>Chart"]
    C --> C1["Bottom: low_earnings"]
    C --> C2["Next: high_earnings"]
    C --> C3["Next: exit_greedy"]
    C --> C4["Next: exit_earnings"]
    C --> C5["Next: exit_lazy"]
    C --> C6["Top: stagnation"]
    
    style B fill:#fff9c4
    style C fill:#fce4ec
```

---

These diagrams cover:
1. **Overall data flow** from simulation to visualization
2. **Class structure** of SimulationTimeSeries
3. **Mutation reason tracking** and normalization
4. **Report window organization** (4 windows, ~18 plots total)
5. **Function call hierarchy** for plotting
6. **Execution sequence** over simulation ticks
7. **Reason normalization** process
8. **Error handling** for no-data cases
9. **Policy adoption tracking** (AdaptiveHybrid)
10. **Final summary generation** (30+ fields)
11. **record_tick method** internal flow
12. **Stacked area data** structure for mutations

Would you like me to add or modify any of these diagrams?
