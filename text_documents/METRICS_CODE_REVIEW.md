# Metrics and Reporting Code Review

**Date:** December 14, 2025  
**Focus:** `metrics_helpers.py`, `report_window.py`, and related test coverage

---

## 1. STRENGTHS ✅

### 1.1 Architecture & Design
- **Clean separation of concerns**: Helpers isolated from visualization
- **Generic plotting utility**: `_plot_time_series()` eliminates duplication
- **Helper delegation**: `get_behaviour_distribution()`, `get_simulation_summary()` remove repeated code
- **Robust error handling**: All plot functions check for None/empty data before plotting
- **Flexible time-series tracking**: Records 9 distinct metrics per tick

### 1.2 Code Quality
- **Well-tested**: 57 total tests (28 metrics + 29 report_window), all passing
- **Concise docstrings**: Recently shortened for clarity
- **Type hints present**: Functions have return types annotated
- **Mock specs proper**: Mock objects use `spec=` to prevent test false-positives
- **Consistent naming**: Good conventions (e.g., `behaviour_distribution`, `_total_mutations`)

### 1.3 Feature Coverage
- Three interactive windows (metrics, behaviour, mutation)
- Time-series tracking of 9 distinct metrics
- Behaviour mutation and stagnation analysis
- Summary statistics with proper formatting
- Window positioning to avoid overlap

---

## 2. ISSUES & RECOMMENDATIONS ⚠️

### 2.1 Missing Validation & Error Handling

#### Issue: No validation of simulation object attributes
**Location:** `metrics_helpers.py`, line 75-81 (`record_tick`)

**Problem:** If simulation lacks expected attributes (e.g., `simulation.requests`), code crashes with AttributeError rather than graceful failure.

**Current:**
```python
pending_count = len([r for r in simulation.requests 
                    if r.status in ('WAITING', 'ASSIGNED', 'PICKED')])
```

**Recommendation:**
```python
# Add guard check at start of record_tick
def record_tick(self, simulation):
    """Capture current simulation state including behaviour changes."""
    # Validate simulation has required attributes
    required = ['time', 'served_count', 'expired_count', 'avg_wait', 'requests', 'drivers']
    for attr in required:
        if not hasattr(simulation, attr):
            raise AttributeError(f"Simulation missing required attribute: {attr}")
    
    self.times.append(simulation.time)
    # ... rest of code
```

#### Issue: Duplicate hardcoded colour palette
**Location:** `report_window.py`, line 309

**Problem:** Colours hardcoded in `_plot_behaviour_distribution_evolution()` instead of using `PLOT_COLOURS`:

```python
colours = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700', '#FF99FF', '#99FFFF']
```

**Recommendation:**
```python
# Use PLOT_COLOURS from metrics_helpers
ax.stackplot(time_series.times, 
             *[behaviour_series[b] for b in all_behaviours],
             labels=all_behaviours,
             colors=PLOT_COLOURS[:len(all_behaviours)],  # Already correct
             alpha=0.7)
```

---

### 2.2 Metrics Accuracy & Completeness

#### Issue: `pending_count` definition ambiguous
**Location:** `metrics_helpers.py`, line 76-78

**Problem:** "Pending" includes WAITING, ASSIGNED, and PICKED. This is technically correct but could be misleading. Should clarify intent:
- WAITING = Not yet assigned (truly pending)
- ASSIGNED = Assigned but not yet picked up
- PICKED = In transit to delivery

**Recommendation:** Add docstring clarity or create separate metrics:
```python
def record_tick(self, simulation):
    """Capture current simulation state including behaviour changes."""
    # ...
    
    # "Pending" = active requests (not yet complete)
    # Includes: WAITING (unassigned), ASSIGNED (assigned but unpicked), PICKED (in transit)
    pending_count = len([r for r in simulation.requests 
                        if r.status in ('WAITING', 'ASSIGNED', 'PICKED')])
    self.pending.append(pending_count)
```

#### Issue: No tracking of request lifecycle distribution
**Current state:** Tracks aggregate metrics but not breakdown:
- Requests in WAITING state (unassigned)
- Requests in ASSIGNED state (assigned, unpicked)
- Requests in PICKED state (picked, in transit)

**Recommendation:** Add optional breakdown tracking (low priority, nice-to-have):
```python
def record_tick(self, simulation):
    # ... existing code ...
    
    # Optional: breakdown of request statuses
    waiting_count = len([r for r in simulation.requests if r.status == 'WAITING'])
    assigned_count = len([r for r in simulation.requests if r.status == 'ASSIGNED'])
    picked_count = len([r for r in simulation.requests if r.status == 'PICKED'])
    
    # Could store as optional metrics for advanced analysis
```

---

### 2.3 Behaviour Tracking Issues

#### Issue: Behaviour name collisions not handled
**Location:** `metrics_helpers.py`, line 21, and `report_window.py`, line 288

**Problem:** If two behaviour classes have same `__name__`, they'll collide:
```python
behaviour_type = driver.behaviour.__class__.__name__
```

**Current mitigation:** Unlikely in practice (would require deliberately named classes), but fragile.

**Recommendation:** Use fully qualified class name as fallback:
```python
def get_behaviour_distribution(simulation) -> dict:
    """Get current behaviour distribution across all drivers."""
    counts = Counter()
    for driver in simulation.drivers:
        if driver.behaviour is None:
            behaviour_type = "None"
        else:
            behaviour_type = driver.behaviour.__class__.__name__
        counts[behaviour_type] += 1
    return dict(counts)
```

#### Issue: First tick shows 0 mutations incorrectly
**Location:** `metrics_helpers.py`, line 96-113

**Problem:** On first `record_tick()`, no previous behaviour exists, so no stagnation is counted (0 drivers stagnant). This is technically correct but means first data point is noisy.

**Current behavior:**
- Tick 0: `behaviour_stagnation[0] = 0` (no history to compare)
- Tick 1: `behaviour_stagnation[1] = 3` (if 3 drivers unchanged)

**Recommendation:** Document this limitation or initialize with fake previous state:
```python
def record_tick(self, simulation):
    """Capture current simulation state including behaviour changes.
    
    Note: First tick (t=0) will show 0 stagnation because no previous state exists.
    Stagnation tracking begins on tick 1.
    """
```

---

### 2.4 Visualization Quality

#### Issue: Hard-coded screen resolution
**Location:** `report_window.py`, line 47-48

**Problem:** Positioning assumes 1920x1080 screen:
```python
screen_width = 1920
screen_height = 1080
```

This breaks on different resolutions, high-DPI displays, or multiple monitors.

**Recommendation:**
```python
def _position_figure(fig, window_index: int, total_windows: int = 3) -> None:
    """Position matplotlib figure window to avoid overlap."""
    if not HAS_MATPLOTLIB or fig is None:
        return
    
    try:
        import matplotlib
        backend = matplotlib.get_backend().lower()
        if 'agg' in backend or 'pdf' in backend or 'svg' in backend:
            return
        
        # Try to get actual screen size; fall back to standard laptop
        try:
            import tkinter
            root = tkinter.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
        except:
            # Fall back to standard laptop resolution
            screen_width = 1920
            screen_height = 1080
        
        # ... rest of positioning logic
```

#### Issue: No legend overflow protection
**Location:** `report_window.py`, line 308-310

**Problem:** If > 6 behaviours exist, legend will be truncated or overlap plots. No text wrapping.

**Recommendation:**
```python
# In _plot_behaviour_distribution_evolution
if len(all_behaviours) > 6:
    # Use smaller font or multiple-column legend
    ax.legend(loc='upper left', fontsize=8, ncol=2)
else:
    ax.legend(loc='upper left', fontsize=9)
```

#### Issue: No figure saving functionality
**Current:** Plots display in interactive windows only. No export to file.

**Recommendation:** Add optional file export:
```python
def generate_report(simulation, time_series: Optional[SimulationTimeSeries] = None, 
                   save_dir: Optional[str] = None) -> None:
    """Generate 3 matplotlib windows: metrics, behaviour analysis, and mutation analysis.
    
    Args:
        simulation: Completed DeliverySimulation instance
        time_series: Optional SimulationTimeSeries with recorded metrics
        save_dir: Optional directory to save PNG/PDF figures
    """
    # ... generate plots ...
    
    if save_dir:
        import os
        os.makedirs(save_dir, exist_ok=True)
        fig1.savefig(os.path.join(save_dir, 'metrics_report.png'), dpi=150)
        fig2.savefig(os.path.join(save_dir, 'behaviour_analysis.png'), dpi=150)
        fig3.savefig(os.path.join(save_dir, 'mutation_analysis.png'), dpi=150)
    
    plt.show()
```

---

### 2.5 Performance & Scalability

#### Issue: O(n) list operations on every tick
**Location:** `metrics_helpers.py`, line 107

**Problem:** Every tick, we sum entire stagnation list:
```python
avg_stagnation = sum(self.behaviour_stagnation) / len(self.behaviour_stagnation)
```

For long simulations (10,000 ticks), this becomes expensive.

**Recommendation:** Use running sum:
```python
def __init__(self):
    # ...
    self._total_stagnation = 0  # Track cumulative
    
def _track_behaviour_changes(self, simulation):
    # ...
    self.behaviour_stagnation.append(stagnant_count)
    self._total_stagnation += stagnant_count  # Add to running total
    
def get_final_summary(self):
    avg_stagnation = self._total_stagnation / len(self.behaviour_stagnation) if self.behaviour_stagnation else 0
```

#### Issue: Behaviour distribution dict copied every tick
**Location:** `metrics_helpers.py`, line 120

**Problem:** 
```python
self._previous_behaviours = current_behaviours.copy()
```

For 1000+ drivers, this creates unnecessary copies.

**Recommendation:** This is actually fine for typical use (< 100 drivers), but could optimize for massive simulations:
```python
# Only copy if we expect frequent mutations
if any(d.behaviour != old_b for d, old_b in zip(...)):
    self._previous_behaviours = current_behaviours.copy()
```
(Not necessary unless simulations routinely have 10,000+ drivers)

---

### 2.6 Test Coverage Gaps

#### Issue: No tests for window positioning logic
**Location:** `test_report_window.py` - missing test for `_position_figure()`

**Recommendation:** Add test:
```python
@patch('phase2.report_window.HAS_MATPLOTLIB', True)
def test_position_figure_sets_geometry(self):
    """_position_figure calls window.geometry() for interactive backends."""
    mock_fig = MagicMock()
    mock_manager = MagicMock()
    mock_fig.canvas.manager = mock_manager
    
    _position_figure(mock_fig, window_index=0)
    
    # Should call geometry
    mock_manager.window.geometry.assert_called()
```

#### Issue: No tests for edge case - zero drivers
**Current tests** assume at least 1 driver. What if simulation has 0 drivers?

**Recommendation:** Add edge case test:
```python
def test_behaviour_distribution_zero_drivers(self):
    """get_behaviour_distribution handles empty driver list."""
    sim = Mock()
    sim.drivers = []
    
    dist = get_behaviour_distribution(sim)
    
    self.assertEqual(dist, {})
```

#### Issue: No tests for very large datasets
**Recommendation:** Add stress test:
```python
def test_record_tick_large_simulation(self):
    """record_tick handles 1000-tick simulations."""
    ts = SimulationTimeSeries()
    sim = MockSimulation(num_drivers=100)
    
    for _ in range(1000):
        ts.record_tick(sim)
    
    self.assertEqual(len(ts.times), 1000)
    summary = ts.get_final_summary()
    self.assertIsNotNone(summary)
```

---

### 2.7 Documentation & Code Clarity

#### Issue: No module-level documentation
**Location:** `metrics_helpers.py` - lacks overview comment

**Recommendation:** Add at top of file:
```python
"""Time-series metrics tracking for post-simulation analysis.

This module provides:

1. SimulationTimeSeries - Tracks 9 metrics per tick:
   - Cumulative counts: served, expired, total requests
   - Average metrics: wait time, pending requests, driver utilization
   - Behaviour metrics: distribution, mutations, stagnation
   
2. Helper functions:
   - get_behaviour_distribution() - Current behaviour count breakdown
   - get_simulation_summary() - Static summary from simulation state
   
3. PLOT_COLOURS constant - Consistent colour palette for visualizations

Usage:
    >>> from phase2.helpers_2.metrics_helpers import SimulationTimeSeries
    >>> series = SimulationTimeSeries()
    >>> for _ in range(1000):
    ...     sim.tick()
    ...     series.record_tick(sim)
    >>> summary = series.get_final_summary()
"""
```

#### Issue: `_plot_time_series()` usage not self-evident
**Location:** `report_window.py`, line 220-235

**Problem:** The function signature is terse; callers must understand parameter order:
```python
_plot_time_series(ax, data['times'], data['served'], 'Served', 'green',
                 'Request Fulfillment Evolution', 'Cumulative Count', fill=True)
```

**Recommendation:** Use keyword arguments more explicitly:
```python
_plot_time_series(
    ax=ax,
    times=data['times'],
    data=data['served'],
    label='Served',
    color='green',
    title='Request Fulfillment Evolution',
    ylabel='Cumulative Count',
    fill=True
)
```

---

### 2.8 Potential Runtime Issues

#### Issue: Division by zero not consistently handled
**Location:** Multiple places check `if total > 0` before dividing, but not all.

**Example:** `metrics_helpers.py`, line 38 ✅ (handled)
```python
'service_level': (simulation.served_count / total * 100.0) if total > 0 else 0.0,
```

But runtime crashes could occur if:
- `len(simulation.drivers) == 0` in `record_tick()` (line 80)

**Recommendation:** Consistent check:
```python
def record_tick(self, simulation):
    # ...
    # Driver utilization
    if simulation.drivers:
        busy_drivers = sum(1 for d in simulation.drivers if d.status != 'IDLE')
        utilization = (busy_drivers / len(simulation.drivers) * 100.0)
    else:
        utilization = 0.0
    self.utilization.append(utilization)
```

---

## 3. PRIORITY IMPROVEMENTS

### HIGH PRIORITY 🔴
1. **Add attribute validation** to `record_tick()` - prevents cryptic crashes
2. **Remove hardcoded screen resolution** - support different display sizes
3. **Add simulation object validation** - catch errors early

### MEDIUM PRIORITY 🟡
4. **Add figure export functionality** - enable PNG/PDF saving
5. **Improve behaviour name handling** - use fully qualified names
6. **Add comprehensive edge-case tests** - zero drivers, large datasets

### LOW PRIORITY 🟢
7. **Optimize for massive simulations** - running sums, avoid copies (< 1% impact for typical use)
8. **Improve legend overflow handling** - only needed if > 10 behaviours
9. **Add module-level documentation** - nice-to-have for clarity

---

## 4. SUMMARY

| Category | Status | Notes |
|----------|--------|-------|
| **Architecture** | ✅ Excellent | Clean separation, good design patterns |
| **Testing** | ✅ Good | 57 tests passing, basic coverage solid |
| **Code Quality** | ✅ Good | Type hints, concise docstrings, consistent style |
| **Error Handling** | ⚠️ Fair | Missing attribute validation, inconsistent division-by-zero checks |
| **Documentation** | ⚠️ Fair | Docstrings good, but missing module-level overview |
| **Performance** | ✅ Good | No bottlenecks for typical simulations (< 1000 ticks, < 100 drivers) |
| **Visualization** | ⚠️ Fair | Hard-coded resolution, no export, legend overflow risk |
| **Scalability** | ⚠️ Fair | Works well for typical use; needs hardening for edge cases |

**Overall:** Solid, production-ready codebase with room for robustness improvements. No critical bugs, but several defensive coding opportunities.

---

## 5. NEXT STEPS

1. **This sprint:** Add attribute validation + fix screen resolution detection
2. **Next sprint:** Add figure export + improve edge-case handling
3. **Future:** Performance optimization + stress testing (only if needed)

