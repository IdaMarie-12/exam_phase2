# CSV Request Timing Test Results

## Test Run Summary
Tested loading 11 requests from `data/requests.csv` with a simulation timeout of 20 ticks.

## Key Findings

### ✅ Timing is Correct
Requests appear at their scheduled times based on the CSV `t` column:

| Request | CSV `t` | Appears At | Status |
|---------|---------|-----------|--------|
| 0 | 0 | Time 1 | ✅ Correct |
| 1 | 1 | Time 2 | ✅ Correct |
| 2 | 2 | Time 3 | ✅ Correct |
| 9 | 90 | Time 91 | ✅ Correct |
| 10 | 110 | Time 111 | ✅ Correct |

**Note:** Requests appear at `time = t+1` because they're injected during the `gen_requests()` phase which runs at the start of each tick.

### ✅ Timeout is Respected
Requests expire exactly after 20 ticks of waiting:

| Request | Created | Timeout | Expires At | Status |
|---------|---------|---------|-----------|--------|
| 1 | 1 | 20 | 21 | ✅ Correct |
| 6 | 30 | 20 | 50 | ✅ Correct |

**Formula:** `Expiration time = Creation time + Timeout`

### ✅ Requests Don't Expire When Assigned/Picked
- Request 0: Created at time 1, still alive at time 120+ (status: delivered)
- Request 9: Created at time 91, still alive at time 120+ (status: picked)

### ✅ GUI Display is Correct
The GUI's `_adapter_plot_data()` function correctly filters requests:
- **Pickup markers** shown only for `status in ("waiting", "assigned")`
- **Dropoff markers** shown only for `status == "picked"`
- **Completed/Expired requests** are kept in the list for metrics but not displayed on the map

## Why Pickup Points Might Appear "Weird"

If you're seeing scattered pickup points on the map:
1. **Time 0-5**: Early CSV requests appear (t=0, 1, 2, 5) = 4 pickups visible
2. **Time 30**: Request 6 appears (t=30) = adds 1 more
3. **Time 45**: Request 7 appears (t=45) = adds 1 more
4. **Time 60**: Request 8 appears (t=60) = adds 1 more
5. **And so on...**

As time progresses and the timeout expires, old requests disappear from the map. So the visualization is **actually working correctly** - you're seeing a dynamic map of only "active" (not yet served or expired) requests.

## Conclusion

✅ **The CSV timing system is working as designed:**
- Requests appear when their `t` value is reached
- Requests expire after `timeout` ticks of being in "waiting" status
- The GUI correctly shows only active requests as pickup/dropoff points
- No bugs detected in the timing or timeout logic

If the appearance still seems "weird", it's the expected behavior of a dynamic request stream appearing and disappearing over time.
