# Error Handling & Visualization Improvements

**Date:** December 14, 2025  
**Status:** ✅ Complete - All 57 tests passing

---

## Changes Implemented

### 1. ERROR HANDLING IMPROVEMENTS ✅

#### 1.1 Attribute Validation in `record_tick()`
**File:** `metrics_helpers.py`

**Before:**
```python
def record_tick(self, simulation):
    """Capture current simulation state including behaviour changes."""
    self.times.append(simulation.time)  # Crashes if 'time' missing
```

**After:**
```python
def record_tick(self, simulation):
    """Capture current simulation state including behaviour changes.
    
    Raises:
        AttributeError: If simulation missing required attributes.
    """
    # Validate simulation has all required attributes
    required_attrs = ['time', 'served_count', 'expired_count', 'avg_wait', 'requests', 'drivers']
    for attr in required_attrs:
        if not hasattr(simulation, attr):
            raise AttributeError(
                f"Simulation missing required attribute '{attr}'. "
                f"SimulationTimeSeries.record_tick() requires: {', '.join(required_attrs)}"
            )
    
    self.times.append(simulation.time)
    # ... rest of code
```

**Benefit:** Clear error messages if simulation object is malformed, instead of cryptic AttributeErrors.

---

#### 1.2 Pending Requests Calculation with Error Handling
**File:** `metrics_helpers.py`, lines 76-82

**Before:**
```python
pending_count = len([r for r in simulation.requests 
                    if r.status in ('WAITING', 'ASSIGNED', 'PICKED')])
self.pending.append(pending_count)
```

**After:**
```python
# Count pending requests (active: not yet complete)
# Includes WAITING (unassigned), ASSIGNED (assigned, unpicked), PICKED (in transit)
try:
    pending_count = len([r for r in simulation.requests 
                        if r.status in ('WAITING', 'ASSIGNED', 'PICKED')])
except (AttributeError, TypeError) as e:
    raise RuntimeError(
        f"Error counting pending requests: {e}. "
        f"Ensure all requests have a 'status' attribute with valid values."
    )
self.pending.append(pending_count)
```

**Benefits:**
- Clear error messages if requests missing `status` attribute
- Added documentation explaining pending statuses

---

#### 1.3 Driver Utilization with Proper Guards
**File:** `metrics_helpers.py`, lines 84-99

**Before:**
```python
busy_drivers = sum(1 for d in simulation.drivers if d.status != 'IDLE')
utilization = (busy_drivers / len(simulation.drivers) * 100.0) if simulation.drivers else 0.0
```

**After:**
```python
# Driver utilization (% of drivers actively busy/moving)
if not simulation.drivers:
    utilization = 0.0
else:
    try:
        busy_drivers = sum(1 for d in simulation.drivers if d.status != 'IDLE')
        utilization = (busy_drivers / len(simulation.drivers) * 100.0)
    except (AttributeError, TypeError) as e:
        raise RuntimeError(
            f"Error calculating driver utilization: {e}. "
            f"Ensure all drivers have a 'status' attribute."
        )
self.utilization.append(utilization)
```

**Benefits:**
- Explicit guard for empty driver list (clearer intent)
- Graceful error handling for missing `status` attribute
- Better error messages for debugging

---

#### 1.4 Behaviour Tracking with Validation
**File:** `metrics_helpers.py`, lines 101-115

**Before:**
```python
def _track_behaviour_changes(self, simulation):
    """Track driver behaviour mutations and stagnation."""
    current_behaviours = {
        driver.id: type(driver.behaviour).__name__ if driver.behaviour else "None"
        for driver in simulation.drivers
    }
```

**After:**
```python
def _track_behaviour_changes(self, simulation):
    """Track driver behaviour mutations and stagnation.
    
    Raises:
        RuntimeError: If drivers missing expected attributes.
    """
    try:
        current_behaviours = {
            driver.id: type(driver.behaviour).__name__ if driver.behaviour else "None"
            for driver in simulation.drivers
        }
    except (AttributeError, TypeError) as e:
        raise RuntimeError(
            f"Error tracking behaviour changes: {e}. "
            f"Ensure all drivers have 'id' and 'behaviour' attributes."
        )
```

**Benefits:**
- Catches missing `id` or `behaviour` attributes early
- Helpful error messages guide debugging

---

### 2. VISUALIZATION IMPROVEMENTS ✅

#### 2.1 Smart Screen Resolution Detection
**File:** `report_window.py`, lines 63-86

**Before:**
```python
# Standard laptop resolution
screen_width = 1920
screen_height = 1080
```

**After:**
```python
# Try to detect actual screen resolution
screen_width = 1920
screen_height = 1080
try:
    import tkinter
    root = tkinter.Tk()
    root.withdraw()  # Hide the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
except Exception:
    # Fall back to standard laptop resolution if detection fails
    pass
```

**Benefits:**
- ✅ Works on displays with different resolutions (2K, 4K, ultrawide, etc.)
- ✅ Gracefully falls back if detection fails
- ✅ No more hardcoded 1920×1080 assumption

---

#### 2.2 Colour Palette Consistency Fix
**File:** `report_window.py`, line 309

**Before:**
```python
# Hardcoded duplicate colours
colours = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700', '#FF99FF', '#99FFFF']
ax.stackplot(..., colors=colours[:len(all_behaviours)], ...)
```

**After:**
```python
# Use PLOT_COLOURS from metrics_helpers (single source of truth)
ax.stackplot(..., colors=PLOT_COLOURS[:len(all_behaviours)], ...)
```

**Benefits:**
- ✅ Single source of truth for colours
- ✅ Easier to change palette globally
- ✅ Eliminates code duplication

---

#### 2.3 Smart Legend Overflow Handling
**File:** `report_window.py`, lines 318-324

**Before:**
```python
ax.legend(loc='upper left', fontsize=9)
```

**After:**
```python
# Handle legend overflow for many behaviours
if len(all_behaviours) > 6:
    ax.legend(loc='upper left', fontsize=8, ncol=2, framealpha=0.9)
else:
    ax.legend(loc='upper left', fontsize=9)
```

**Benefits:**
- ✅ Prevents legend overflow when > 6 behaviours
- ✅ Automatically uses 2-column layout for many items
- ✅ Reduces font size only when needed

---

#### 2.4 Figure Export Functionality
**File:** `report_window.py`, lines 67-79 (function signature) + lines 153-163 (export logic)

**Before:**
```python
def generate_report(simulation, time_series: Optional[SimulationTimeSeries] = None) -> None:
    # ... only displays plots in windows
    plt.show()
```

**After:**
```python
def generate_report(simulation, time_series: Optional[SimulationTimeSeries] = None,
                   save_dir: Optional[str] = None) -> None:
    """Generate 3 matplotlib windows: metrics, behaviour analysis, and mutation analysis.
    
    Args:
        simulation: Completed DeliverySimulation instance
        time_series: Optional SimulationTimeSeries with recorded metrics
        save_dir: Optional directory to save PNG figures (created if missing)
    
    Raises:
        RuntimeError: If matplotlib not installed or save_dir not writable
    """
    # ... validation logic ...
    
    # At end of function:
    if save_dir:
        import os
        try:
            fig1.savefig(os.path.join(save_dir, 'metrics_report.png'), dpi=150, bbox_inches='tight')
            fig2.savefig(os.path.join(save_dir, 'behaviour_analysis.png'), dpi=150, bbox_inches='tight')
            fig3.savefig(os.path.join(save_dir, 'mutation_analysis.png'), dpi=150, bbox_inches='tight')
            print(f"📁 Figures saved to {save_dir}/")
        except (OSError, IOError) as e:
            print(f"⚠️ Warning: Could not save figures: {e}")
    
    plt.show()
```

**Usage Example:**
```python
# Display only (existing behavior)
generate_report(simulation, series)

# Display AND save to PNG files
generate_report(simulation, series, save_dir='./reports/run_2025_12_14')
```

**Benefits:**
- ✅ Optional PNG export of all 3 figures
- ✅ Auto-creates output directory if missing
- ✅ High DPI (150) for publication quality
- ✅ Graceful error handling with warnings
- ✅ User feedback ("Figures saved to...")

---

### 3. VALIDATION & ROBUSTNESS ✅

#### 3.1 save_dir Permission Checking
**File:** `report_window.py`, lines 82-86

```python
# Validate save_dir if provided
if save_dir is not None:
    import os
    try:
        os.makedirs(save_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Cannot create save directory '{save_dir}': {e}")
```

**Benefits:**
- ✅ Early error detection (fail at `generate_report()` call, not at save time)
- ✅ Helpful error messages

---

## Test Results

### ✅ All Tests Passing

```
Metrics Tests (test_metrics.py):
  Ran 28 tests in 0.001s - OK

Report Window Tests (test_report_window.py):
  Ran 29 tests in 0.310s - OK

Total: 57/57 tests passing ✅
```

---

## Summary of Improvements

| Improvement | Type | Impact | Status |
|-------------|------|--------|--------|
| Attribute validation | Error Handling | High - Prevents cryptic crashes | ✅ |
| Pending count error handling | Error Handling | Medium - Better error messages | ✅ |
| Utilization guard checks | Error Handling | Medium - Consistent null handling | ✅ |
| Behaviour tracking validation | Error Handling | Medium - Early error detection | ✅ |
| Smart resolution detection | Visualization | High - Works on any display | ✅ |
| Colour palette consistency | Visualization | Low - Code quality, DRY | ✅ |
| Legend overflow handling | Visualization | Medium - Prevents cut-off text | ✅ |
| Figure export (PNG) | Visualization | High - New functionality | ✅ |
| save_dir validation | Robustness | Medium - Early failure detection | ✅ |

---

## Backwards Compatibility

✅ **All changes are backwards compatible:**
- `record_tick()` signature unchanged - just more robust
- `generate_report()` has optional `save_dir` parameter (defaults to None = old behavior)
- All existing code continues to work unchanged

---

## Next Steps (Optional Enhancements)

1. **Add PDF export option** (currently PNG only)
   ```python
   def generate_report(..., save_format: str = 'png')  # 'png', 'pdf', or 'both'
   ```

2. **Add compression level control** for PNG export
   ```python
   fig1.savefig(..., dpi=dpi, compression_level=9)
   ```

3. **Add running sum optimization** for large simulations
   - Track cumulative stagnation to avoid O(n) recalculation in `get_final_summary()`

4. **Add edge-case tests** for zero drivers/requests (currently assumed > 0)

---

