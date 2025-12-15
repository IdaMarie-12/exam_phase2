# Mutation Strategy Description

The mutation system allows drivers to dynamically adapt their behavior during simulation based on performance metrics. We use a HybridMutation strategy, that combines performance-based switching while considering stagnation and exit strategies.  

For each tick in the simulation, it is considered whether a driver should mutate, based on the flow in appendix XX. The HybridMutation works in 5 steps: 

1. Assess driver cooldown period
2. Calculate average fare from the last 10 trips
3. Check exit conditions
4. Mutation performance
   a. Primary mutation
   b. Secondary mutation (stagnation mutation)

All drivers can only mutate once every 10 ticks. If they haven't mutated in the last 10 ticks, we then calculate the average fare from the last 10 trips, to conclude if they should mutate or not. Based on the average a driver can fall into one of 5 zones: 

| Zone | Average fare | Action |
|------|--------------|--------|
| Struggling | < 3.0 | Switch to GreedyDistanceBehaviour |
| Recovery | 3.0 – 5.0 | Greedy driver; at 5.0 threshold, exit to Lazy and reset cooldown |
| Normal | 5.0 – 7.5 | Evaluate stability |
| Good | 7.5 – 10.0 | Stable performance, approaching selectivity |
| Thriving | > 10.0 | Switch to EarningsMaxBehaviour |

When we have calculated the average fare, we then check the existing behaviours exit conditions. Here we have following conditions: 

- Greedy exit: average ≥ 5.0
- EarningsMax exit: average < 7.5
- Lazy exit: None

The LazyBehaviour is considered the natural state, it therefore has no exit point. If a driver meets the exit conditions, it is automatically assigned the LazyBehaviour. When 10 ticks have passed after this, they can be considered to mutate again.

**Note on Recovery zone:** The Recovery zone (3.0 – 5.0) represents a transition/holding zone rather than an action zone. If a driver is already in Greedy and their earnings improve to ≥5.0, they exit Greedy and reset to Lazy. If a Greedy driver's earnings drop back below 5.0, they stay in Greedy. This hysteresis prevents constant switching and gives strategies time to work.

A driver is considered stagnated in their behaviour if 70% of their earnings of the latest 10 trips are within ±5% of the average (while also being over cooldown period and in an average earnings). If it is less than 70% it is considered a healthy variation. If a driver is deemed stagnated, we trigger exploration. 

If a driver is considered stagnated and has the LazyBehaviour they will 100% of the time trigger exploration and randomly be assigned either GreedyDistanceBehaviour or EarningsMaxBehaviour with equal 50% probability. If a driver has GreedyDistanceBehaviour or EarningsMaxBehaviour, they have 30% chance of mutating to another behaviour different from their existing one with equal probability. 

When a driver mutates their new behaviour, it is only in effect the next tick, since the offer for new requests happens before evaluating mutation. In the next tick, the driver will be in their cooldown period, and therefore not further considered for mutation before 10 ticks have gone by.
