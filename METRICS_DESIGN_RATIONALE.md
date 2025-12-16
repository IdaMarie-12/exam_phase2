# Metrics Design Rationale

## Overview
The four-window metrics system is designed to provide layered insights into the delivery simulation engine, enabling observation of how policies make decisions, how mutations affect driver behavior, and whether the system achieves its optimization goals.

---

## Window 1: Request Statistics & Generation

**Purpose:** Monitor the simulation's task processing efficiency and demand dynamics

**Metrics Tracked (6 plots in 4x2 grid):**
- **Cumulative Served vs Expired** (full width): Tracks fulfillment outcomes over time
- **Service Level %**: Percentage of requests served vs expired (quality KPI)
- **Request Generation Rate**: Actual requests generated per tick (supply timeline)
- **Driver Utilization**: Percentage of drivers actively assigned (capacity utilization)
- **Request Age Pressure**: Maximum and average age of waiting requests vs timeout threshold
- **Summary Statistics** (full width): Final metrics and performance indicators

**Why These Metrics:**
These metrics provide the foundational view of the simulation's **operational effectiveness and supply-demand balance**. They answer:
- "Is the system processing work efficiently?" (Served vs Expired)
- "How well is the system meeting demand?" (Service Level %)
- "What is the incoming demand pattern?" (Generation Rate - NEW)
- "Are drivers being fully utilized?" (Utilization)
- "Is the system getting overwhelmed?" (Request Age Pressure)

The addition of **Request Generation Rate** (replacing Pending Requests Queue) shows the supply stream entering the system, revealing whether the system is demand-constrained, capacity-constrained, or load-balanced. Combined with cumulative served/expired, it tells the complete supply-demand story.


---

## Window 2: Driver Statistics & Earnings

**Purpose:** Observe individual driver behavior and policy impact

**Metrics Tracked:**
- Driver status (idle, assigned, on-route)
- Earnings per driver
- Distance traveled
- Requests served per driver

**Why These Metrics:**
These metrics reveal **how the dispatch policy allocates work** across drivers. By comparing earnings and assignments, we can see:
- Whether the policy is fair or creates imbalances
- Whether high-earning drivers are being exploited (over-assigned)
- Whether the policy creates rational incentives for driver behavior

This is critical for **testing the policy engine** and understanding whether dispatch decisions make sense from individual driver perspectives.

---

## Window 3: Mutation Root Cause Analysis

**Purpose:** Understand driver decision-making and mutation drivers

**Metrics Tracked (3 Categories):**
- **Entry (Performance-Based):** Mutations driven by market opportunities (low/high earnings)
- **Entry (Stagnation-Exploration):** Mutations driven by plateau-breaking exploration
- **Exit (Safety Valve):** Mutations driven by strategy failure or greedy behavior

**Secondary Detail (6 Individual Reasons):**
- Low earnings entry
- High earnings entry
- Plateau breaking
- Greedy exit
- Earnings failure exit
- Lazy exit

**Why These Metrics:**
Window 3 is the **engine diagnostics dashboard**. It shows:
- **Mutation distribution** reveals whether drivers are exploring rationally or if the system is creating pathological behavior
- **3-category breakdown** shows the relative importance of different mutation drivers (market vs. plateau vs. failure)
- **6-reason detail** allows debugging specific driver behaviors and identifying unintended incentives

This window directly exposes **how mutations are being triggered** and whether they represent intelligent adaptation or signs of broken incentives.

---

## Window 4: Simulation Snapshot

**Purpose:** Real-time state verification and detailed debugging

**Metrics Tracked:**
- Current simulation time
- Active driver assignments
- Pending requests with details
- Driver route information

**Why These Metrics:**
This window provides **granular state inspection** during simulation execution. It allows:
- Verification that the engine state is consistent and valid
- Tracing specific decision paths (why was *this* driver assigned *this* request?)
- Debugging anomalies by inspecting the exact state when they occurred

---

## Design Philosophy

The metrics architecture follows a **hierarchical insight model**:

1. **Window 1 (Overview):** "Is the system working?"
2. **Window 2 (Policy Effects):** "How is the policy distributing work?"
3. **Window 3 (Mutation Analysis):** "Why are drivers mutating? Is the engine healthy?"
4. **Window 4 (State Detail):** "What is the exact state right now?"

Each window zooms deeper into the engine, from aggregate outcomes → policy behavior → mutation drivers → raw state. This enables systematic debugging and validation of both the dispatch policy and the mutation mechanism.
