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
        self.behaviour_stagnation = []     # List tracking drivers stable in same behaviour (no change)
        self.earnings_stagnation_events = []  # List tracking drivers with earnings stagnation (70% within ±5%)
        
        # Policy & Offer tracking
        self.offers_generated = []         # Number of offers created per tick
        self.offers_accepted = []          # Number of offers accepted per tick
        self.offer_acceptance_rate = []    # Percentage of offers accepted per tick
        self.policy_names = set()          # Set of all unique policy names used
        self.policy_offers_by_type = []    # List of dicts tracking offers per policy type per tick
        self.policy_success_rates = []     # List of dicts tracking success % per policy per tick
        self.avg_offer_quality = []        # Average reward/time ratio per tick
        
        # Internal state tracking
        self._previous_behaviours = {}  # Map of driver_id -> behaviour_type
        self._total_mutations = 0       # Cumulative mutation counter
        self._mutation_reason_counts = {
            'performance_low_earnings': 0,
            'performance_high_earnings': 0,
            'exit_greedy': 0,
            'exit_earnings': 0,
            'stagnation_exploration': 0
        }  # Breakdown of mutations by reason
        self._offer_history = []        # Store all offers for analysis
        self._policy_request_tracking = {}  # Track request completion by policy
    
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
        self._track_offers_and_policies(simulation)
    
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
        
        # Count mutations (behaviour changes) and stability (no change)
        mutations_this_tick = 0
        stable_count = 0
        
        for driver_id, current_behaviour in current_behaviours.items():
            if driver_id in self._previous_behaviours:
                previous_behaviour = self._previous_behaviours[driver_id]
                if current_behaviour != previous_behaviour:
                    mutations_this_tick += 1
                    self._total_mutations += 1
                else:
                    stable_count += 1
        
        # Count behaviour distribution
        behaviour_counts = defaultdict(int)
        for behaviour_type in current_behaviours.values():
            behaviour_counts[behaviour_type] += 1
        
        # Track earnings stagnation events from mutation rule
        earnings_stagnation_count = self._count_earnings_stagnation_events(simulation)
        
        # Track mutation reasons from mutation rule
        self._track_mutation_reasons(simulation)
        
        # Record metrics
        self.behaviour_distribution.append(dict(behaviour_counts))
        self.behaviour_mutations.append(self._total_mutations)
        self.behaviour_stagnation.append(stable_count)
        self.earnings_stagnation_events.append(earnings_stagnation_count)
        
        # Update previous state for next tick
        self._previous_behaviours = current_behaviours.copy()
    
    def _count_earnings_stagnation_events(self, simulation) -> int:
        """Count drivers with earnings stagnation detected this tick.
        
        Returns drivers that have stagnation_exploration in mutation history at current time.
        """
        if not hasattr(simulation, 'mutation_rule') or simulation.mutation_rule is None:
            return 0
        
        rule = simulation.mutation_rule
        if not hasattr(rule, 'mutation_history'):
            return 0
        
        # Count unique drivers that had stagnation_exploration mutations at current time
        stagnation_drivers = set()
        for entry in rule.mutation_history:
            if entry['time'] == simulation.time and entry['reason'] == 'stagnation_exploration':
                stagnation_drivers.add(entry['driver_id'])
        
        return len(stagnation_drivers)
    
    def _track_mutation_reasons(self, simulation) -> None:
        """Update mutation reason breakdown from mutation rule history."""
        if not hasattr(simulation, 'mutation_rule') or simulation.mutation_rule is None:
            return
        
        rule = simulation.mutation_rule
        if not hasattr(rule, 'mutation_history'):
            return
        
        # Count reasons from entire history
        reason_counts = {
            'performance_low_earnings': 0,
            'performance_high_earnings': 0,
            'exit_greedy': 0,
            'exit_earnings': 0,
            'stagnation_exploration': 0
        }
        
        for entry in rule.mutation_history:
            reason = entry.get('reason')
            if reason in reason_counts:
                reason_counts[reason] += 1
        
        self._mutation_reason_counts = reason_counts
    
    def _track_offers_and_policies(self, simulation) -> None:
        """Track offer generation and policy performance metrics."""
        # Check if simulation has offer history attribute
        if not hasattr(simulation, 'offer_history'):
            # Initialize default tracking if not present
            self.offers_generated.append(0)
            self.offers_accepted.append(0)
            self.offer_acceptance_rate.append(0.0)
            self.policy_offers_by_type.append({})
            self.policy_success_rates.append({})
            self.avg_offer_quality.append(0.0)
            return
        
        # Get offers from this tick (offers in offer_history with time == simulation.time)
        current_tick_offers = [
            o for o in simulation.offer_history 
            if hasattr(o, 'created_at') and o.created_at == simulation.time
        ]
        
        # Track offers generated
        self.offers_generated.append(len(current_tick_offers))
        
        # Group offers by policy
        policy_counts = {}
        total_quality = 0.0
        
        for offer in current_tick_offers:
            policy_name = getattr(offer, 'policy_name', 'Unknown')
            self.policy_names.add(policy_name)
            
            # Count offers by policy
            policy_counts[policy_name] = policy_counts.get(policy_name, 0) + 1
            
            # Track offer quality (reward/time ratio)
            reward = getattr(offer, 'estimated_reward', 0)
            time = getattr(offer, 'estimated_travel_time', 1)
            if time > 0:
                total_quality += (reward / time)
        
        # Calculate average quality
        if current_tick_offers:
            avg_quality = total_quality / len(current_tick_offers)
        else:
            avg_quality = 0.0
        
        self.avg_offer_quality.append(avg_quality)
        self.policy_offers_by_type.append(policy_counts)
        
        # Count accepted offers by checking which requests were assigned
        # An offer is "accepted" if the request moved from WAITING to ASSIGNED/PICKED
        accepted_count = 0
        for offer in current_tick_offers:
            request = offer.request
            # If request is no longer WAITING, it was accepted
            if request.status != 'WAITING':
                accepted_count += 1
        
        self.offers_accepted.append(accepted_count)
        
        # Calculate acceptance rate
        if current_tick_offers:
            acceptance_rate = (accepted_count / len(current_tick_offers)) * 100.0
        else:
            acceptance_rate = 0.0
        
        self.offer_acceptance_rate.append(acceptance_rate)
        
        # Track policy success rates (requests completed by policy)
        policy_success = {}
        if hasattr(simulation, 'requests'):
            served_by_policy = {}
            total_by_policy = {}
            
            for request in simulation.requests:
                if hasattr(request, 'policy_used') and request.policy_used:
                    policy = request.policy_used
                    total_by_policy[policy] = total_by_policy.get(policy, 0) + 1
                    
                    if request.status == 'DELIVERED':
                        served_by_policy[policy] = served_by_policy.get(policy, 0) + 1
            
            for policy, total in total_by_policy.items():
                if total > 0:
                    policy_success[policy] = (served_by_policy.get(policy, 0) / total) * 100.0
                else:
                    policy_success[policy] = 0.0
        
        self.policy_success_rates.append(policy_success)
    
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
            'earnings_stagnation_events': self.earnings_stagnation_events,
            'offers_generated': self.offers_generated,
            'offers_accepted': self.offers_accepted,
            'offer_acceptance_rate': self.offer_acceptance_rate,
            'policy_offers_by_type': self.policy_offers_by_type,
            'avg_offer_quality': self.avg_offer_quality,
        }
    
    def get_final_summary(self):
        """Return final summary statistics."""
        if not self.times:
            return {}
        
        total_requests = self.served[-1] + self.expired[-1]
        total_mutations = self.behaviour_mutations[-1] if self.behaviour_mutations else 0
        avg_stability = sum(self.behaviour_stagnation) / len(self.behaviour_stagnation) if self.behaviour_stagnation else 0
        avg_earnings_stagnation = sum(self.earnings_stagnation_events) / len(self.earnings_stagnation_events) if self.earnings_stagnation_events else 0
        
        # Calculate offer metrics
        total_offers_generated = sum(self.offers_generated) if self.offers_generated else 0
        total_offers_accepted = sum(self.offers_accepted) if self.offers_accepted else 0
        avg_offer_quality = sum(self.avg_offer_quality) / len(self.avg_offer_quality) if self.avg_offer_quality else 0.0
        avg_acceptance_rate = sum(self.offer_acceptance_rate) / len(self.offer_acceptance_rate) if self.offer_acceptance_rate else 0.0
        
        return {
            'total_time': self.times[-1],
            'final_served': self.served[-1],
            'final_expired': self.expired[-1],
            'final_avg_wait': self.avg_wait[-1],
            'total_requests': total_requests,
            'service_level': (self.served[-1] / total_requests * 100.0) if total_requests > 0 else 0.0,
            'total_behaviour_mutations': total_mutations,
            'avg_stagnant_drivers': avg_stability,
            'avg_earnings_stagnation_events': avg_earnings_stagnation,
            'mutation_reason_breakdown': self._mutation_reason_counts.copy(),
            'final_behaviour_distribution': self.behaviour_distribution[-1] if self.behaviour_distribution else {},
            'total_offers_generated': total_offers_generated,
            'total_offers_accepted': total_offers_accepted,
            'avg_offer_quality': avg_offer_quality,
            'avg_acceptance_rate': avg_acceptance_rate,
            'policies_used': list(self.policy_names),
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
  • Avg Stable:         {summary.get('avg_stable_drivers', 0):.1f}
  • Avg Earnings Stag:  {summary.get('avg_earnings_stagnation_events', 0):.1f}

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
    
    # Add time-series mutation and stability stats if available
    if time_series and time_series.get_final_summary():
        summary = time_series.get_final_summary()
        stats_text += f"\nBehaviour Evolution Metrics:\n"
        stats_text += f"  • Total Mutations:        {summary.get('total_behaviour_mutations', 0)}\n"
        stats_text += f"  • Avg Stable Drivers:     {summary.get('avg_stable_drivers', 0):.1f}\n"
        stats_text += f"  • Avg Earnings Stagnation: {summary.get('avg_earnings_stagnation_events', 0):.1f}\n"
    
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
        if hasattr(rule, 'low_threshold'):
            rule_text += f"Low Earnings Threshold:      {rule.low_threshold:.2f}\n"
        if hasattr(rule, 'high_threshold'):
            rule_text += f"High Earnings Threshold:     {rule.high_threshold:.2f}\n"
        if hasattr(rule, 'cooldown_ticks'):
            rule_text += f"Mutation Cooldown:           {rule.cooldown_ticks} ticks\n"
        if hasattr(rule, 'exploration_prob'):
            rule_text += f"Exploration Probability:     {rule.exploration_prob:.1%}\n"
        if hasattr(rule, 'greedy_exit_threshold'):
            rule_text += f"Greedy Exit Threshold:       {rule.greedy_exit_threshold:.2f}\n"
        if hasattr(rule, 'earnings_max_exit_threshold'):
            rule_text += f"EarningsMax Exit Threshold:  {rule.earnings_max_exit_threshold:.2f}\n"
        
        rule_text += "\nTrigger Conditions:\n"
        rule_text += "  • Performance (Low):  avg < 3.0  → Switch to Greedy\n"
        rule_text += "  • Performance (High): avg > 10.0 → Switch to EarningsMax\n"
        rule_text += "  • Stagnation:         70% within ±5% of avg → Explore\n"
        rule_text += "    - Lazy driver:    100% explore\n"
        rule_text += "    - Active driver:  30% explore\n"
        
        # Add mutation transitions data
        if hasattr(rule, 'mutation_transitions') and rule.mutation_transitions:
            rule_text += "\nBehaviour Transitions:\n"
            total_mutations = sum(rule.mutation_transitions.values())
            for (from_behaviour, to_behaviour), count in sorted(rule.mutation_transitions.items()):
                pct = (count / total_mutations * 100) if total_mutations > 0 else 0
                rule_text += f"  {from_behaviour} → {to_behaviour}: {count}\n"
        
        # Add mutation reason breakdown
        if hasattr(rule, 'mutation_history') and rule.mutation_history:
            rule_text += "\nMutation Reason Breakdown:\n"
            reason_names = {
                'performance_low_earnings': 'Low Earnings (< 3.0)',
                'performance_high_earnings': 'High Earnings (> 10.0)',
                'exit_greedy': 'Exit Greedy (>= 5.0)',
                'exit_earnings': 'Exit EarningsMax (< 7.5)',
                'stagnation_exploration': 'Stagnation Exploration'
            }
            
            # Count mutations by reason
            reason_counts = {
                'performance_low_earnings': 0,
                'performance_high_earnings': 0,
                'exit_greedy': 0,
                'exit_earnings': 0,
                'stagnation_exploration': 0
            }
            for entry in rule.mutation_history:
                reason = entry.get('reason')
                if reason in reason_counts:
                    reason_counts[reason] += 1
            
            total_mutations = sum(reason_counts.values())
            for reason, count in sorted(reason_counts.items()):
                pct = (count / total_mutations * 100) if total_mutations > 0 else 0
                rule_text += f"  • {reason_names.get(reason, reason):30s}: {count:3d} ({pct:5.1f}%)\n"
        
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
