from collections import defaultdict, Counter


# Colour palette for consistent visualizations
PLOT_COLOURS = ['#FF9999', '#66B2FF', '#99FF99', '#FFD700', '#FF99FF', '#99FFFF']


def get_behaviour_distribution(simulation) -> dict:
    """Get current behaviour distribution across all drivers."""
    counts = Counter()
    for driver in simulation.drivers:
        behaviour_type = driver.behaviour.__class__.__name__
        counts[behaviour_type] += 1
    return dict(counts)


def get_simulation_summary(simulation) -> dict:
    """Get static summary statistics from simulation state."""
    total = simulation.served_count + simulation.expired_count
    return {
        'total_time': simulation.time,
        'final_served': simulation.served_count,
        'final_expired': simulation.expired_count,
        'total_requests': total,
        'service_level': (simulation.served_count / total * 100.0) if total > 0 else 0.0,
        'final_avg_wait': simulation.avg_wait,
    }


class SimulationTimeSeries:
    """Records simulation metrics at each timestep. Call record_tick after each tick."""
    
    def __init__(self):
        self.times = []
        self.served = []
        self.expired = []
        self.avg_wait = []
        self.pending = []
        self.utilization = []
        
        # Behaviour tracking
        self.behaviour_distribution = []  # List of dicts tracking behaviour counts
        self.behaviour_mutations = []      # List tracking cumulative mutations per tick
        self.behaviour_stagnation = []     # List tracking drivers stable in same behaviour
        
        # Internal state tracking
        self._previous_behaviours = {}  # Map of driver_id -> behaviour_type
        self._total_mutations = 0       # Cumulative mutation counter
    
    def record_tick(self, simulation):
        """Capture current simulation state including behaviour changes."""
        # Validate simulation has all required attributes
        required_attrs = ['time', 'served_count', 'expired_count', 'avg_wait', 'requests', 'drivers']
        for attr in required_attrs:
            if not hasattr(simulation, attr):
                raise AttributeError(
                    f"Simulation missing required attribute '{attr}'. "
                    f"SimulationTimeSeries.record_tick() requires: {', '.join(required_attrs)}"
                )
        
        self.times.append(simulation.time)
        self.served.append(simulation.served_count)
        self.expired.append(simulation.expired_count)
        self.avg_wait.append(simulation.avg_wait)
        
        try:
            pending_count = len([r for r in simulation.requests 
                                if r.status in ('WAITING', 'ASSIGNED', 'PICKED')])
        except (AttributeError, TypeError) as e:
            raise RuntimeError(
                f"Error counting pending requests: {e}. "
                f"Ensure all requests have a 'status' attribute with valid values."
            )
        self.pending.append(pending_count)
        
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
        
        self._track_behaviour_changes(simulation)
    
    def _track_behaviour_changes(self, simulation):
        """Track driver behaviour mutations and stagnation."""
        # Get current behaviour snapshot
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
        
        # Count mutations (behaviour changes) and stagnation (no change)
        mutations_this_tick = 0
        stagnant_count = 0
        
        for driver_id, current_behaviour in current_behaviours.items():
            if driver_id in self._previous_behaviours:
                previous_behaviour = self._previous_behaviours[driver_id]
                if current_behaviour != previous_behaviour:
                    mutations_this_tick += 1
                    self._total_mutations += 1
                else:
                    stagnant_count += 1
        
        # Count behaviour distribution
        behaviour_counts = defaultdict(int)
        for behaviour_type in current_behaviours.values():
            behaviour_counts[behaviour_type] += 1
        
        # Record metrics
        self.behaviour_distribution.append(dict(behaviour_counts))
        self.behaviour_mutations.append(self._total_mutations)
        self.behaviour_stagnation.append(stagnant_count)
        
        # Update previous state for next tick
        self._previous_behaviours = current_behaviours.copy()
    
    def get_data(self):
        """Return all time-series data as dict."""
        return {
            'times': self.times,
            'served': self.served,
            'expired': self.expired,
            'avg_wait': self.avg_wait,
            'pending': self.pending,
            'utilization': self.utilization,
            'behaviour_distribution': self.behaviour_distribution,
            'behaviour_mutations': self.behaviour_mutations,
            'behaviour_stagnation': self.behaviour_stagnation,
        }
    
    def get_final_summary(self):
        """Return final summary statistics."""
        if not self.times:
            return {}
        
        total_requests = self.served[-1] + self.expired[-1]
        total_mutations = self.behaviour_mutations[-1] if self.behaviour_mutations else 0
        avg_stagnation = sum(self.behaviour_stagnation) / len(self.behaviour_stagnation) if self.behaviour_stagnation else 0
        
        return {
            'total_time': self.times[-1],
            'final_served': self.served[-1],
            'final_expired': self.expired[-1],
            'final_avg_wait': self.avg_wait[-1],
            'total_requests': total_requests,
            'service_level': (self.served[-1] / total_requests * 100.0) if total_requests > 0 else 0.0,
            'total_behaviour_mutations': total_mutations,
            'avg_stagnant_drivers': avg_stagnation,
            'final_behaviour_distribution': self.behaviour_distribution[-1] if self.behaviour_distribution else {},
        }


# ====================================================================
# TEXT FORMATTING FUNCTIONS FOR VISUALIZATION
# ====================================================================

def format_summary_statistics(simulation, time_series) -> str:
    """Format final simulation summary statistics as text block."""
    # Get final summary
    if time_series:
        summary = time_series.get_final_summary()
    else:
        summary = get_simulation_summary(simulation)
    
    # Format text with behaviour metrics if available
    stats_text = f"""
FINAL SIMULATION SUMMARY
{'=' * 40}

Total Time:            {summary.get('total_time', 0)} ticks
Total Requests:        {summary.get('total_requests', 0)}
  • Served:            {summary.get('final_served', 0)}
  • Expired:           {summary.get('final_expired', 0)}

Service Level:         {summary.get('service_level', 0):.1f}%
Average Wait Time:     {summary.get('final_avg_wait', 0):.2f} ticks

Behaviour Analysis:
  • Total Mutations:    {summary.get('total_behaviour_mutations', 0)}
  • Avg Stagnant:       {summary.get('avg_stagnant_drivers', 0):.1f}

Total Drivers:         {len(simulation.drivers)}
Total Requests:        {len(simulation.requests)}
"""
    return stats_text


def format_behaviour_statistics(simulation, time_series) -> str:
    """Format behaviour distribution statistics as text block."""
    behaviour_counts = get_behaviour_distribution(simulation)
    total_drivers = len(simulation.drivers)
    
    stats_text = "BEHAVIOUR STATISTICS\n" + "=" * 60 + "\n\n"
    stats_text += f"Total Drivers: {total_drivers}\n\n"
    stats_text += "Final Behaviour Distribution:\n"
    
    for behaviour_type, count in sorted(behaviour_counts.items()):
        percentage = (count / total_drivers * 100) if total_drivers > 0 else 0
        stats_text += f"  • {behaviour_type:25s}: {count:3d} drivers ({percentage:5.1f}%)\n"
    
    # Add time-series mutation and stagnation stats if available
    if time_series and time_series.get_final_summary():
        summary = time_series.get_final_summary()
        stats_text += f"\nBehaviour Evolution Metrics:\n"
        stats_text += f"  • Total Mutations:        {summary.get('total_behaviour_mutations', 0)}\n"
        stats_text += f"  • Avg Stagnant Drivers:   {summary.get('avg_stagnant_drivers', 0):.1f}\n"
    
    return stats_text


def format_impact_metrics(simulation) -> str:
    """Format performance impact metrics as text block."""
    total_requests = simulation.served_count + simulation.expired_count
    service_level = (simulation.served_count / total_requests * 100) if total_requests > 0 else 0
    
    # Count drivers that have mutated
    mutated_drivers = sum(1 for d in simulation.drivers 
                         if hasattr(d, '_last_mutation_time') and d._last_mutation_time > -float("inf"))
    
    impact_text = "PERFORMANCE IMPACT\n" + "=" * 45 + "\n\n"
    impact_text += f"Final Service Level:  {service_level:.1f}%\n"
    impact_text += f"  • Served:           {simulation.served_count}\n"
    impact_text += f"  • Expired:          {simulation.expired_count}\n"
    impact_text += f"  • Total Requests:   {total_requests}\n\n"
    impact_text += f"Average Wait Time:    {simulation.avg_wait:.2f} ticks\n"
    impact_text += f"Simulation Duration:  {simulation.time} ticks\n"
    impact_text += f"Total Drivers:        {len(simulation.drivers)}\n"
    impact_text += f"Mutated Drivers:      {mutated_drivers} ({mutated_drivers/len(simulation.drivers)*100:.1f}%)\n"
    
    return impact_text


def format_mutation_rule_info(simulation) -> str:
    """Format mutation rule configuration and history as text block."""
    if not hasattr(simulation, 'mutation_rule') or simulation.mutation_rule is None:
        return "No mutation rule configured"
    
    rule = simulation.mutation_rule
    rule_type = rule.__class__.__name__
    
    rule_text = f"MUTATION RULE CONFIGURATION\n" + "=" * 45 + "\n\n"
    rule_text += f"Active Rule: {rule_type}\n\n"
    
    if rule_type == "HybridMutation":
        if hasattr(rule, 'window'):
            rule_text += f"Performance Window:  {rule.window} ticks\n"
        if hasattr(rule, 'low_threshold'):
            rule_text += f"Low Earnings Threshold:  {rule.low_threshold:.2f}\n"
        if hasattr(rule, 'high_threshold'):
            rule_text += f"High Earnings Threshold:  {rule.high_threshold:.2f}\n"
        if hasattr(rule, 'cooldown_ticks'):
            rule_text += f"Mutation Cooldown:  {rule.cooldown_ticks} ticks\n"
        if hasattr(rule, 'stagnation_window'):
            rule_text += f"Stagnation Window:  {rule.stagnation_window} ticks\n"
        rule_text += "\nTrigger Conditions:\n"
        rule_text += "  Low earnings → Switch to Greedy\n"
        rule_text += "  High earnings → Switch to EarningsMax\n"
        rule_text += "  Stagnating → Explore random behaviour\n"
        
        # Add mutation transitions data
        if hasattr(rule, 'mutation_transitions') and rule.mutation_transitions:
            rule_text += "\nBehaviour Transitions:\n"
            total_mutations = sum(rule.mutation_transitions.values())
            for (from_behaviour, to_behaviour), count in sorted(rule.mutation_transitions.items()):
                pct = (count / total_mutations * 100) if total_mutations > 0 else 0
                rule_text += f"  {from_behaviour} → {to_behaviour}: {count}\n"
        
        # Add detailed mutation history (last 10 mutations shown)
        if hasattr(rule, 'mutation_history') and rule.mutation_history:
            rule_text += "\nMutation History (latest 10):\n"
            for entry in rule.mutation_history[-10:]:
                reason = entry['reason'].replace('_', ' ').title()
                rule_text += f"  t{entry['time']:4d}: D{entry['driver_id']:2d} " +\
                            f"{entry['from_behaviour'][:4]}→{entry['to_behaviour'][:4]} " +\
                            f"({reason}, fare:{entry['avg_fare']:.1f})\n"
    else:
        rule_text += f"Custom Rule: {rule_type}\n"
    
    return rule_text
