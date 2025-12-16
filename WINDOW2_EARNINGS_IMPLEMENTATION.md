# Window 2 Earnings Metrics Implementation

## Overview
Added comprehensive earnings/fare metrics to Window 2 (Behaviour Dynamics) to provide economic insight into driver behaviour performance.

## Changes Made

### 1. Window 2 Layout Expansion
**File**: `phase2/report_window.py` (_show_behaviour_window)
- **Previous Layout**: 2 rows (Behaviour Evolution + Pie/Stats)
- **New Layout**: 3 rows
  - Row 0 (full width): Behaviour Distribution Evolution (stacked area chart)
  - Row 1: Pie Chart (left) + Behaviour/Mutation Stats (right)
  - Row 2: Earnings by Behaviour Bar Chart (left) + Earnings Distribution Box Plot (right)
- **Figure Height**: Increased from ~11 to 16 to accommodate 3 rows

### 2. New Plotting Functions

#### `_plot_earnings_by_behaviour(ax, simulation)`
**Location**: `phase2/report_window.py` (lines ~299-337)
- **Purpose**: Bar chart showing average earnings per behaviour type
- **Data Source**: `simulation.earnings_by_behaviour` dictionary
- **Visualization**: 
  - X-axis: Behaviour types (GreedyDistanceBehaviour, etc.)
  - Y-axis: Average earnings ($)
  - Color-coded bars using PLOT_COLOURS
  - Rotated labels if more than 3 behaviours
- **Error Handling**: Displays "No earnings data by behaviour" if missing data

#### `_plot_earnings_distribution(ax, simulation)`
**Location**: `phase2/report_window.py` (lines ~340-366)
- **Purpose**: Box plot showing earnings distribution across all drivers
- **Data Source**: Individual `driver.earnings` from all drivers
- **Visualization**:
  - Single box plot showing min/max/median/quartiles
  - Light cyan color with 70% transparency
  - Y-axis: Individual Driver Earnings ($)
  - X-axis Label: "Drivers"
- **Error Handling**: Displays appropriate messages if no driver or earnings data

### 3. New Formatting Function

#### `format_earnings_statistics(simulation)` 
**Location**: `phase2/helpers_2/metrics_helpers.py` (lines ~624-652)
- **Purpose**: Generate formatted text summary of earnings metrics
- **Metrics Displayed**:
  - Total Fleet Earnings: Sum of all driver earnings
  - Number of Drivers: Count with positive earnings
  - Average per Driver: Mean earnings across fleet
  - Min Earnings: Minimum individual driver earnings
  - Max Earnings: Maximum individual driver earnings
  - Range: Max - Min difference
  - By Behaviour: Average earnings for each behaviour type (if data available)
- **Formatting**: Monospace text in yellow background box

### 4. Import Updates
**File**: `phase2/report_window.py` (lines 5-17)
- Added `format_earnings_statistics` to imports from metrics_helpers

### 5. Test Coverage

#### test_report_window.py
- **test_plot_earnings_by_behaviour**: Verifies bar chart creation without error
- **test_plot_earnings_distribution**: Verifies box plot creation without error
- **MockSimulation Update**: Added:
  - Individual driver earnings initialization (100-300 range)
  - earnings_by_behaviour dictionary with sample data

#### test_metrics.py
- **test_format_earnings_statistics_with_drivers**: Tests text generation with driver data
- **test_format_earnings_statistics_no_drivers**: Tests graceful handling of missing data

## Data Integration Points

### Driver Earnings
- Source: Each driver has an `earnings` attribute (decimal value)
- Updated during request delivery
- Accessed in `_plot_earnings_distribution()` and `format_earnings_statistics()`

### Earnings by Behaviour
- Source: `simulation.earnings_by_behaviour` dictionary
- Keys: Behaviour class names (e.g., 'GreedyDistanceBehaviour')
- Values: Lists of earnings values from drivers with that behaviour
- Used in `_plot_earnings_by_behaviour()` and `format_earnings_statistics()`

## Visual Hierarchy

```
Window 2: Behaviour Dynamics & Earnings
├── Row 0 (full width): Behaviour Distribution Evolution
│   └── Stacked area chart showing driver count per behaviour over time
│
├── Row 1: Behaviour Analysis
│   ├── Left: Final Behaviour Distribution (pie chart)
│   └── Right: Behaviour & Mutation Statistics (text)
│
└── Row 2: Earnings Analysis
    ├── Left: Average Earnings by Behaviour (bar chart)
    └── Right: Earnings Distribution (box plot)
```

## Key Features

✅ **Comprehensive Economic View**: Shows both aggregate fleet earnings and individual driver distribution
✅ **Behaviour Comparison**: Average earnings by behaviour type enables comparative analysis
✅ **Statistical Summary**: Min/Max/Range/Mean provides quick economic health assessment
✅ **Graceful Degradation**: Handles missing data without crashing
✅ **Consistent Styling**: Uses PLOT_COLOURS and matches existing aesthetic
✅ **Full Test Coverage**: All new functions tested with success/no-data scenarios

## Test Results
- **34 total tests**: All passing ✅
- **3 new tests**: Added for earnings functions
- **No regressions**: All existing tests still pass
- **Full suite**: 433 tests pass across entire workspace

## Interpretation Guidelines

### Earnings by Behaviour Bar Chart
- **Higher bar = More profitable behaviour**: Compare heights to identify economically superior strategies
- **Behaviour variation**: Shows whether certain behaviour types generate more revenue

### Earnings Distribution Box Plot
- **Box height = IQR (Inter-Quartile Range)**: Shows spread of middle 50% of drivers
- **Whiskers = Extreme values**: Outliers in earning performance
- **Median line = Central tendency**: Typical driver earnings level
- **Wide box = High variance**: Inconsistent earnings across fleet
- **Narrow box = Consistent earnings**: More uniform economic performance

### Text Summary
- **Total Fleet Earnings**: Absolute economic value generated
- **Avg per Driver**: Normalized per-driver performance
- **Range**: Economic inequality/variance in earnings
- **By Behaviour**: Which behaviour types are most lucrative

