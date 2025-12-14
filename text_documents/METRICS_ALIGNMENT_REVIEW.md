# Metrics and Report Window Alignment Check

## Executive Summary
The `report_window.py` and `metrics_helpers.py` generally correspond with the codebase, but there are some **discrepancies and outdated references** that need attention.

---

## Issues Found

### 1. **CRITICAL: Stagnation Metric Mismatch** ❌

**In `metrics_helpers.py` (Line 64):**
```python
self.behaviour_stagnation = []     # List tracking drivers stable in same behaviour
```

**Problem:** This is tracking **behaviour stability** (drivers staying in same behaviour), NOT **earnings stagnation** (which actually triggers mutations).

**What it measures:** Counts drivers whose behaviour didn't change from previous tick.
**What it should measure:** Counts drivers whose earnings are stagnating (70% within ±5% of average).

**Impact:** The metrics show a misleading picture of what's actually triggering mutations.

**Recommendation:** Rename to `behaviour_stability` and add real earnings stagnation tracking from `mutation.mutation_history`.

---

### 2. **Outdated/Missing Attributes in format_mutation_rule_info()** ⚠️

**In `metrics_helpers.py` (Lines 307-325):**

```python
if hasattr(rule, 'window'):
    rule_text += f"Performance Window:  {rule.window} ticks\n"
...
if hasattr(rule, 'stagnation_window'):
    rule_text += f"Stagnation Window:  {rule.stagnation_window} ticks\n"
```

**Problem:** These attributes don't exist in current `HybridMutation`:
- `window` - ❌ Does not exist (evaluation window is fixed at 10, not a parameter)
- `stagnation_window` - ❌ Does not exist (was unified into fixed 10-tick window)

**Current attributes in HybridMutation:**
- ✅ `low_threshold` (3.0)
- ✅ `high_threshold` (10.0)
- ✅ `cooldown_ticks` (10)
- ✅ `exploration_prob` (0.3)
- ✅ `greedy_exit_threshold` (5.0)
- ✅ `earnings_max_exit_threshold` (7.5)

**Impact:** The display will skip these attributes silently (due to `hasattr` check).

**Recommendation:** Remove obsolete `window` and `stagnation_window` references. Add `greedy_exit_threshold` and `earnings_max_exit_threshold` display.

---

### 3. **Missing Mutation Reason Breakdown** ⚠️

**Current tracking:** The mutation system records 5 reason types in `mutation_history`:
1. `performance_low_earnings`
2. `performance_high_earnings`
3. `exit_greedy`
4. `exit_earnings`
5. `stagnation_exploration`

**Problem:** Metrics don't track counts of each reason type.

**Current code (Lines 307-312):**
```python
# Add mutation transitions data
if hasattr(rule, 'mutation_transitions') and rule.mutation_transitions:
    rule_text += "\nBehaviour Transitions:\n"
    total_mutations = sum(rule.mutation_transitions.values())
    for (from_behaviour, to_behaviour), count in sorted(rule.mutation_transitions.items()):
        pct = (count / total_mutations * 100) if total_mutations > 0 else 0
        rule_text += f"  {from_behaviour} → {to_behaviour}: {count}\n"
```

**Impact:** Good start, but doesn't break down **why** mutations happened (performance vs exploration vs exit).

**Recommendation:** Add a function to count mutations by reason from `mutation_history`.

---

### 4. **Simulation Attributes Not Documented** ℹ️

**In `metrics_helpers.py` (Line 38):**

Missing from docstring but used in code:
- `simulation.timeout` - ✅ Used implicitly (request expiration)
- `simulation.earnings_by_behaviour` - ✅ Initialized but never documented or used in metrics

**Impact:** Minor - documentation gap, not a functional issue.

---

### 5. **Inconsistent Reference to "Behaviour Stagnation" Throughout** ⚠️

**In `report_window.py`:**
- Line 168: `_plot_mutations_and_stagnation()` title: "Mutations & Stagnation Trends"
- Line 180: Plots `time_series.behaviour_stagnation` with label "Stagnant Drivers"
- Line 305: Window title: "Mutation Rule & Stagnation Analysis"

**Problem:** All references call it "stagnation" but it actually measures "behaviour stability".

**Impact:** Documentation and visualization are semantically incorrect.

---

## Summary of Required Updates

| Issue | File | Lines | Fix Type | Priority |
|-------|------|-------|----------|----------|
| Stagnation metric wrong | `metrics_helpers.py` | 64, 120-158 | Rename + redesign | 🔴 HIGH |
| Outdated window attributes | `metrics_helpers.py` | 307-325 | Update to current attrs | 🔴 HIGH |
| Missing exit thresholds display | `metrics_helpers.py` | 307-325 | Add new fields | 🟡 MEDIUM |
| Missing mutation reason breakdown | `metrics_helpers.py` | ~new | Add new function | 🟡 MEDIUM |
| Misleading terminology | `report_window.py` | 168, 180, 305 | Rename references | 🟡 MEDIUM |
| Earnings stagnation not tracked | Both files | N/A | Add real stagnation metric | 🔴 HIGH |

---

## Recommended Actions

### Priority 1 (High): Fix Stagnation Tracking
1. Rename `behaviour_stagnation` → `behaviour_stability` throughout
2. Add new `earnings_stagnation_detected` metric that counts drivers actually stagnating in earnings
3. Source this from `mutation.mutation_history` with reason `"stagnation_exploration"`

### Priority 2 (High): Update Mutation Rule Display
1. Remove references to non-existent `window` and `stagnation_window`
2. Add display of `greedy_exit_threshold` (5.0) and `earnings_max_exit_threshold` (7.5)
3. Add breakdown of mutations by reason (5 types)

### Priority 3 (Medium): Consistent Terminology
1. Replace "Stagnation" with "Behaviour Stability" in all UI text
2. Add new section for "Earnings Stagnation Events"

### Priority 4 (Medium): Enhanced Metrics
1. Create function `get_mutation_breakdown(mutation_rule)` that categorizes mutations by reason
2. Display this breakdown in the mutation window

