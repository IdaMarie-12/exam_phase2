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
        self.service_level = []        # Percentage served / (served + expired) per tick
        self.utilization = []
        
        # Behaviour tracking
        self.behaviour_distribution = []  # List of dicts tracking behaviour counts
        self.mutation_rate = []            # Mutations per 10 ticks (stability indicator)
        self.behaviour_transitions = []    # List of dicts: transitions from->to per tick
        self.stable_ratio = []             # Ratio of stable drivers (no recent change)
        
        # Mutation root cause tracking
        self.mutation_reasons = []         # List of dicts tracking mutation reason breakdown
        self.driver_mutation_freq = {}     # Map of driver_id -> count of mutations
        
        # Policy & Offer tracking
        self.offers_generated = []         # Number of offers created per tick
        self.offer_acceptance_rate = []    # Percentage of offers accepted per tick
        self.policy_names = set()          # Set of all unique policy names used
        self.policy_distribution = []      # List of dicts tracking drivers per policy per tick
        self.avg_offer_quality = []        # Average reward/time ratio per tick
        self.offer_quality_distribution = []  # List of quality values for distribution analysis
        
        # Internal state tracking
        self._previous_behaviours = {}     # Map of driver_id -> behaviour_type
        self._total_mutations = 0          # Cumulative mutation counter
        self._mutation_reason_counts = {
            'performance_low_earnings': 0,
            'performance_high_earnings': 0,
            'exit_greedy': 0,
            'exit_earnings': 0,
            'stagnation_exploration': 0
        }  # Breakdown of mutations by reason
        self._mutations_last_10_ticks = 0  # Track mutations in last 10 ticks for rate
        self._recent_driver_mutations = {}  # Track which drivers mutated recently (last 5 ticks)
    
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
        
        # Calculate service level (percentage served)
        total_requests = simulation.served_count + simulation.expired_count
        service_level = (simulation.served_count / total_requests * 100.0) if total_requests > 0 else 0.0
        self.service_level.append(service_level)
        
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
        """Track driver behaviour mutations, transitions, and stability."""
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
        
        # Count mutations and build transition map
        mutations_this_tick = 0
        stable_count = 0
        transitions = defaultdict(int)  # from_behaviour -> to_behaviour counts
        
        for driver_id, current_behaviour in current_behaviours.items():
            if driver_id in self._previous_behaviours:
                previous_behaviour = self._previous_behaviours[driver_id]
                if current_behaviour != previous_behaviour:
                    mutations_this_tick += 1
                    self._total_mutations += 1
                    transitions[f"{previous_behaviour}→{current_behaviour}"] += 1
                    
                    # Track driver mutation frequency
                    if driver_id not in self.driver_mutation_freq:
                        self.driver_mutation_freq[driver_id] = 0
                    self.driver_mutation_freq[driver_id] += 1
                    
                    # Mark driver as recently mutated
                    self._recent_driver_mutations[driver_id] = simulation.time
                else:
                    stable_count += 1
        
        # Clean old recent mutations (older than 5 ticks)
        cutoff_time = simulation.time - 5
        self._recent_driver_mutations = {
            driver_id: time for driver_id, time in self._recent_driver_mutations.items()
            if time >= cutoff_time
        }
        
        # Count behaviour distribution
        behaviour_counts = defaultdict(int)
        for behaviour_type in current_behaviours.values():
            behaviour_counts[behaviour_type] += 1
        
        # Calculate stable ratio (drivers that haven't mutated in last 5 ticks)
        stable_drivers = len(current_behaviours) - len(self._recent_driver_mutations)
        stable_ratio = (stable_drivers / len(current_behaviours) * 100.0) if current_behaviours else 0.0
        
        # Calculate mutation rate (mutations per 10 ticks)
        # Store last 10 tick mutations and calculate rate
        self._mutations_last_10_ticks += mutations_this_tick
        if len(self.mutation_rate) >= 10:
            # Remove oldest mutation count
            oldest_idx = len(self.mutation_rate) - 10
            if oldest_idx >= 0 and oldest_idx < len(self.mutation_rate):
                self._mutations_last_10_ticks = sum(self.mutation_rate[-10:])
        
        mutation_rate = self._mutations_last_10_ticks / 10.0  # Average per tick over last 10
        
        # Track mutation reasons from mutation rule
        self._track_mutation_reasons(simulation)
        
        # Record metrics
        self.behaviour_distribution.append(dict(behaviour_counts))
        self.mutation_rate.append(mutation_rate)
        self.behaviour_transitions.append(dict(transitions))
        self.stable_ratio.append(stable_ratio)
        self.mutation_reasons.append(self._mutation_reason_counts.copy())
        
        # Update previous state for next tick
        self._previous_behaviours = current_behaviours.copy()
    
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
        """Track offer generation, acceptance, and policy distribution."""
        # Check if simulation has offer history attribute
        if not hasattr(simulation, 'offer_history'):
            # Initialize default tracking if not present
            self.offers_generated.append(0)
            self.offer_acceptance_rate.append(0.0)
            self.policy_distribution.append({})
            self.avg_offer_quality.append(0.0)
            self.offer_quality_distribution.append([])
            return
        
        # Get offers from the current tick
        # Since record_tick is called AFTER sim.tick(), we need to look for offers
        # created at time (simulation.time - 1) since time was already incremented
        target_time = simulation.time - 1 if simulation.time > 0 else 0
        current_tick_offers = [
            o for o in simulation.offer_history 
            if hasattr(o, 'created_at') and o.created_at == target_time
        ]
        
        # Track offers generated
        self.offers_generated.append(len(current_tick_offers))
        
        # Track offer quality distribution and calculate average
        quality_list = []
        total_quality = 0.0
        policy_driver_counts = defaultdict(int)  # Track drivers per policy
        
        for offer in current_tick_offers:
            policy_name = getattr(offer, 'policy_name', 'Unknown')
            self.policy_names.add(policy_name)
            policy_driver_counts[policy_name] += 1
            
            # Track offer quality (reward/time ratio)
            reward = getattr(offer, 'estimated_reward', 0)
            time = getattr(offer, 'estimated_travel_time', 1)
            if time > 0:
                quality = reward / time
                quality_list.append(quality)
                total_quality += quality
        
        # Calculate average quality
        if current_tick_offers:
            avg_quality = total_quality / len(current_tick_offers)
            acceptance_rate = (len([o for o in current_tick_offers if getattr(o.request, 'status', None) != 'WAITING']) / len(current_tick_offers)) * 100.0
        else:
            avg_quality = 0.0
            acceptance_rate = 0.0
        
        self.avg_offer_quality.append(avg_quality)
        self.offer_quality_distribution.append(quality_list)
        self.offer_acceptance_rate.append(acceptance_rate)
        self.policy_distribution.append(dict(policy_driver_counts))
    
    def get_data(self):
        """Return all time-series data as dict."""
        return {
            'times': self.times,
            'served': self.served,
            'expired': self.expired,
            'avg_wait': self.avg_wait,
            'service_level': self.service_level,
            'utilization': self.utilization,
            'behaviour_distribution': self.behaviour_distribution,
            'mutation_rate': self.mutation_rate,
            'behaviour_transitions': self.behaviour_transitions,
            'stable_ratio': self.stable_ratio,
            'mutation_reasons': self.mutation_reasons,
            'offers_generated': self.offers_generated,
            'offer_acceptance_rate': self.offer_acceptance_rate,
            'policy_distribution': self.policy_distribution,
            'avg_offer_quality': self.avg_offer_quality,
        }
    
    def get_final_summary(self):
        """Return final summary statistics."""
        if not self.times:
            return {}
        
        total_requests = self.served[-1] + self.expired[-1]
        total_mutations = self._total_mutations
        avg_mutation_rate = sum(self.mutation_rate) / len(self.mutation_rate) if self.mutation_rate else 0.0
        final_stable_ratio = self.stable_ratio[-1] if self.stable_ratio else 0.0
        
        # Calculate offer metrics
        total_offers_generated = sum(self.offers_generated) if self.offers_generated else 0
        avg_offer_quality = sum(self.avg_offer_quality) / len(self.avg_offer_quality) if self.avg_offer_quality else 0.0
        avg_acceptance_rate = sum(self.offer_acceptance_rate) / len(self.offer_acceptance_rate) if self.offer_acceptance_rate else 0.0
        
        # Count driver mutation frequency distribution
        mutation_freq_dist = Counter(self.driver_mutation_freq.values())
        
        return {
            'total_time': self.times[-1],
            'final_served': self.served[-1],
            'final_expired': self.expired[-1],
            'final_avg_wait': self.avg_wait[-1],
            'final_service_level': self.service_level[-1] if self.service_level else 0.0,
            'total_requests': total_requests,
            'total_behaviour_mutations': total_mutations,
            'avg_mutation_rate': avg_mutation_rate,
            'final_stable_ratio': final_stable_ratio,
            'mutation_reason_breakdown': self._mutation_reason_counts.copy(),
            'driver_mutation_frequency': dict(mutation_freq_dist),
            'final_behaviour_distribution': self.behaviour_distribution[-1] if self.behaviour_distribution else {},
            'total_offers_generated': total_offers_generated,
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
    
    # Format text for Window 1
    stats_text = f"""
SYSTEM EFFICIENCY SUMMARY
{'=' * 50}

Simulation Duration:   {summary.get('total_time', 0)} ticks
Total Requests:        {summary.get('total_requests', 0)}
  • Served:            {summary.get('final_served', 0)}
  • Expired:           {summary.get('final_expired', 0)}

Service Level:         {summary.get('final_service_level', 0):.1f}%
Average Wait Time:     {summary.get('final_avg_wait', 0):.2f} ticks
System Stability:      Utilization variance tracking

Drivers Deployed:      {len(simulation.drivers)}
"""
    return stats_text


def format_behaviour_statistics(simulation, time_series) -> str:
    """Format behaviour distribution statistics as text block."""
    behaviour_counts = get_behaviour_distribution(simulation)
    total_drivers = len(simulation.drivers)
    
    stats_text = "BEHAVIOUR DISTRIBUTION SUMMARY\n" + "=" * 50 + "\n\n"
    stats_text += f"Total Drivers: {total_drivers}\n\n"
    
    for behaviour_type, count in sorted(behaviour_counts.items()):
        percentage = (count / total_drivers * 100) if total_drivers > 0 else 0
        stats_text += f"  {behaviour_type:20s}: {count:3d} ({percentage:5.1f}%)\n"
    
    # Add mutation stats if available
    if time_series and time_series.get_final_summary():
        summary = time_series.get_final_summary()
        stats_text += f"\nMutation Summary:\n"
        stats_text += f"  Total Mutations:       {summary.get('total_behaviour_mutations', 0)}\n"
        stats_text += f"  Avg Mutation Rate:     {summary.get('avg_mutation_rate', 0):.2f} per tick\n"
        stats_text += f"  Final Stability:       {summary.get('final_stable_ratio', 0):.1f}% stable\n"
    
    return stats_text


def format_impact_metrics(simulation) -> str:
    """Format performance impact metrics as text block."""
    total_requests = simulation.served_count + simulation.expired_count
    service_level = (simulation.served_count / total_requests * 100) if total_requests > 0 else 0
    
    impact_text = "PERFORMANCE IMPACT\n" + "=" * 50 + "\n\n"
    impact_text += f"Service Level:        {service_level:.1f}%\n"
    impact_text += f"  • Served:           {simulation.served_count}\n"
    impact_text += f"  • Expired:          {simulation.expired_count}\n"
    impact_text += f"  • Total Requests:   {total_requests}\n\n"
    impact_text += f"Average Wait Time:    {simulation.avg_wait:.2f} ticks\n"
    impact_text += f"Simulation Duration:  {simulation.time} ticks\n"
    impact_text += f"Total Drivers:        {len(simulation.drivers)}\n"
    
    return impact_text


def format_mutation_rule_info(simulation) -> str:
    """Format mutation rule configuration as text block."""
    if not hasattr(simulation, 'mutation_rule') or simulation.mutation_rule is None:
        return "No mutation rule configured"
    
    rule = simulation.mutation_rule
    rule_type = rule.__class__.__name__
    
    rule_text = f"MUTATION RULE: {rule_type}\n" + "=" * 50 + "\n\n"
    
    if rule_type == "HybridMutation":
        rule_text += "Trigger Conditions & Thresholds:\n"
        if hasattr(rule, 'low_threshold'):
            rule_text += f"  • Low Earnings:    {rule.low_threshold:.2f}\n"
        if hasattr(rule, 'high_threshold'):
            rule_text += f"  • High Earnings:   {rule.high_threshold:.2f}\n"
        if hasattr(rule, 'cooldown_ticks'):
            rule_text += f"  • Mutation Cooldown: {rule.cooldown_ticks} ticks\n"
        if hasattr(rule, 'exploration_prob'):
            rule_text += f"  • Exploration Prob: {rule.exploration_prob:.0%}\n"
        if hasattr(rule, 'greedy_exit_threshold'):
            rule_text += f"  • Greedy Exit:   {rule.greedy_exit_threshold:.2f}\n"
        if hasattr(rule, 'earnings_max_exit_threshold'):
            rule_text += f"  • EarningsMax Exit: {rule.earnings_max_exit_threshold:.2f}\n"
    else:
        rule_text += f"Configuration:\n  • Type: {rule_type}\n"
    
    return rule_text
    return rule_text
