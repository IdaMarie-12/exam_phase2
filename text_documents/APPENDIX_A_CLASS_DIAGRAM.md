# Appendix A: Class Diagram and Architecture

## A.1 Core Domain Classes

```
┌─────────────────────┐
│      Point          │
├─────────────────────┤
│ x: float            │
│ y: float            │
├─────────────────────┤
│ distance_to()       │
│ __add__/__sub__      │
│ __mul__/__rmul__     │
│ __eq__/__hash__      │
└─────────────────────┘
         ▲
         │ uses (2 per Request)
         │
    ┌────┴─────┐
    │           │
┌──────────────────────────┐
│       Request            │
├──────────────────────────┤
│ id: int                  │
│ pickup: Point            │
│ dropoff: Point           │
│ creation_time: int       │
│ status: str              │
│   (WAITING, ASSIGNED,    │
│    PICKED, DELIVERED,    │
│    EXPIRED)              │
│ assigned_driver_id: int  │
│ wait_time: int           │
├──────────────────────────┤
│ is_active()              │
│ mark_assigned()          │
│ mark_picked()            │
│ mark_delivered()         │
│ mark_expired()           │
│ update_wait()            │
└──────────────────────────┘
         ▲
         │ contains (many)
         │
┌─────────────────────────────────┐
│   DeliverySimulation            │
├─────────────────────────────────┤
│ time: int                       │
│ drivers: list[Driver]           │
│ requests: list[Request]         │
│ dispatch_policy: DispatchPolicy │
│ request_generator: RequestGen   │
│ mutation_rule: MutationRule     │
│ timeout: int                    │
│ served_count: int               │
│ expired_count: int              │
│ avg_wait: float                 │
├─────────────────────────────────┤
│ tick()                          │
│ get_snapshot()                  │
└─────────────────────────────────┘
         ▲
         │ contains (many)
         │
    ┌────┴─────┐
    │           │
┌──────────────────────┐
│      Driver          │
├──────────────────────┤
│ id: int              │
│ position: Point      │
│ speed: float         │
│ status: str          │
│   (IDLE, TO_PICKUP,  │
│    TO_DROPOFF)       │
│ behaviour: ∗Behaviour│
│ current_request: Req │
│ history: list        │
│ idle_since: int      │
│ earnings: float      │
├──────────────────────┤
│ assign_request()     │
│ target_point()       │
│ step()               │
│ complete_pickup()    │
│ complete_dropoff()   │
│ is_idle()            │
└──────────────────────┘
         ▲
         │ has-a
         │
    ┌────┴────────────────────────────┐
    │                                 │
 ┌─────────────────┐         ┌─────────────────────┐
 │  Offer          │         │ DriverBehaviour (ABC)│
 ├─────────────────┤         ├─────────────────────┤
 │ driver: Driver  │         │                     │
 │ request: Request│         │ decide()            │
 │ est_travel_time │         └─────────────────────┘
 │ est_reward      │                  ▲
 │ created_at      │                  │ implements
 │ policy_name     │        ┌─────────┼─────────┐
 ├─────────────────┤        │         │         │
 │ reward_per_time │   ┌─────────┐ ┌──────────┐ ┌───────────┐
 │ pickup_distance │   │ Greedy  │ │ Earnings │ │  Lazy     │
 │ as_dict()       │   │ Distance│ │   Max    │ │ Behaviour │
 └─────────────────┘   └─────────┘ └──────────┘ └───────────┘
```

## A.2 Policy and Mutation Classes

```
┌──────────────────────────────┐
│   DispatchPolicy (ABC)       │
├──────────────────────────────┤
│ assign(drivers, requests,    │
│         time)                │
│ → list[tuple[Driver,Request]]│
└──────────────────────────────┘
         ▲
         │ implements
         ├──────────────────────────────┐
         │                              │
 ┌──────────────────────┐    ┌────────────────────────┐
 │ NearestNeighbor      │    │   GlobalGreedy         │
 │ Policy               │    │   Policy               │
 ├──────────────────────┤    ├────────────────────────┤
 │ assign()             │    │ assign()               │
 │ Greedy nearest-      │    │ Build all pairs,       │
 │ neighbour matching   │    │ sort by distance,      │
 │ O(n²m²)              │    │ match greedily         │
 │                      │    │ O(nm log(nm))          │
 └──────────────────────┘    └────────────────────────┘


┌──────────────────────────────┐
│   MutationRule (ABC)         │
├──────────────────────────────┤
│ maybe_mutate(driver, time)   │
└──────────────────────────────┘
         ▲
         │ implements
         │
 ┌──────────────────────────────────────┐
 │      HybridMutation                  │
 ├──────────────────────────────────────┤
 │ Performance-based primary            │
 │ Exploration-based secondary          │
 │ • LOW earnings → switch to GREEDY    │
 │ • HIGH earnings → switch to EARNINGS │
 │ • STAGNATING → explore (30% prob)    │
 │ • COOLDOWN between mutations         │
 └──────────────────────────────────────┘
```

## A.3 Request Generator

```
┌──────────────────────────────┐
│   RequestGenerator           │
├──────────────────────────────┤
│ rate: float                  │
│ width: int                   │
│ height: int                  │
│ next_id: int                 │
│ enabled: bool                │
├──────────────────────────────┤
│ maybe_generate(time)         │
│ → list[Request]              │
│                              │
│ Uses Poisson distribution    │
│ for stochastic arrivals      │
└──────────────────────────────┘
```

## A.4 Helper Modules

```
phase2/
├── helpers_2/
│   ├── core_helpers.py
│   │   ├── is_at_target()
│   │   ├── move_towards()
│   │   ├── record_assignment_start()
│   │   ├── record_completion()
│   │   └── ...
│   │
│   ├── engine_helpers.py
│   │   ├── gen_requests()
│   │   ├── expire_requests()
│   │   ├── get_proposals()
│   │   ├── collect_offers()
│   │   ├── resolve_conflicts()
│   │   ├── assign_requests()
│   │   ├── move_drivers()
│   │   ├── handle_pickup()
│   │   ├── handle_dropoff()
│   │   └── mutate_drivers()
│   │
│   └── metrics_helpers.py
│       ├── SimulationTimeSeries (tracks 9 metrics)
│       ├── get_behaviour_distribution()
│       ├── get_simulation_summary()
│       └── ...
│
└── report_window.py
    ├── generate_report()
    ├── _show_metrics_window()
    ├── _show_behaviour_window()
    ├── _show_mutation_window()
    └── ...
```

## A.5 Relationships Summary

| From | To | Type | Cardinality |
|------|----|----|-------------|
| DeliverySimulation | Driver | contains | 1 to many |
| DeliverySimulation | Request | contains | 1 to many |
| DeliverySimulation | DispatchPolicy | has-a | 1 to 1 |
| DeliverySimulation | RequestGenerator | has-a | 1 to 1 |
| DeliverySimulation | MutationRule | has-a | 1 to 1 |
| Driver | Point | has-a | 1 to 1 |
| Driver | DriverBehaviour | has-a | 1 to 1 |
| Driver | Request | current | 0 to 1 |
| Request | Point | has-a | 2 (pickup, dropoff) |
| Offer | Driver | references | 1 to 1 |
| Offer | Request | references | 1 to 1 |

## A.6 Data Flow Through Simulation Tick

```
┌─────────────────────────────────────────────────────────────────┐
│                      DeliverySimulation.tick()                  │
│                     (9-Phase Orchestration)                     │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Generate
    RequestGenerator.maybe_generate(time) 
    → new Request objects added to simulation.requests

Phase 2: Expire
    Check request.wait_time >= timeout
    → mark_expired(), increment expired_count

Phase 3: Propose
    DispatchPolicy.assign(idle_drivers, waiting_requests, time)
    → list of (Driver, Request) proposal tuples

Phase 4: Collect Offers
    For each (driver, request) proposal:
        create Offer(driver, request, travel_time, reward)
        DriverBehaviour.decide(driver, offer, time)
        → collect accepted offers

Phase 5: Resolve Conflicts
    Multiple drivers accepted same request?
    → apply nearest-wins strategy
    → finalize (driver, request) assignments

Phase 6: Assign Requests
    Driver.assign_request(request, time)
    → update status to ASSIGNED, TO_PICKUP

Phase 7: Move Drivers
    For each driver:
        Driver.step(dt)  # move toward target
        on_pickup_event()
            → mark_picked(), status = TO_DROPOFF
        on_dropoff_event()
            → mark_delivered(), record history, earnings
            → status = IDLE

Phase 8: Mutate Drivers
    For each driver:
        MutationRule.maybe_mutate(driver, time)
        → possibly change driver.behaviour

Phase 9: Increment Time
    simulation.time += 1
```
