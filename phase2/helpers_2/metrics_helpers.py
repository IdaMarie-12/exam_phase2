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
    """Records simulation metrics at each timestep."""
    
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
        self.mutations_per_tick = []       # Actual mutations this tick (not smoothed)
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
        self.actual_policy_used = []       # Track which actual policy was used per tick (for Adaptive breakdown)
        
        # Request queue dynamics
        self.pending_requests = []         # Number of waiting requests per tick
        self.rejection_rate = []           # % of offers drivers reject per tick
        self.max_request_age = []          # Maximum age of any waiting request per tick
        self.avg_request_age = []          # Average age of all waiting requests per tick
        
        # Dispatch efficiency
        self.offers_vs_assignments = []    # (offers_generated, offers_accepted) per tick for efficiency
        self.conflict_count = []           # Number of offers competing for same request per tick
        self.matching_efficiency = []      # % of offers that became assignments per tick
        
        # Driver state distribution
        self.driver_status_distribution = []  # Dict of {status: count} per tick
        
        # Request completion quality
        self.completion_time_samples = []     # List of (pickup_time, delivery_time) tuples
        self.avg_total_trip_distance = []     # Average distance drivers travel per request per tick
        
        # Behaviour-specific insights
        self.earnings_by_behaviour = defaultdict(list)  # Track avg earnings per behaviour per tick
        self.acceptance_rate_by_behaviour = defaultdict(list)  # Track acceptance rate by behaviour type
        self.behaviour_performance_ratio = []  # Service level by behaviour type per tick
        
        # System load indicators
        self.request_generation_rate = []  # Actual requests generated per tick
        self.expiration_rate = []          # % of requests expired per tick
        self.served_to_expired_ratio = []  # KPI: served / (served + expired) per tick
        
        # Internal state tracking
        self._total_mutations = 0          # Cumulative mutation counter
        self._mutation_reason_counts = {
            'performance_low_earnings': 0,
            'performance_high_earnings': 0,
            'exit_greedy': 0,
            'exit_earnings': 0,
            'exit_lazy': 0,
            'stagnation_exploration': 0
        }  # Breakdown of mutations by reason (6 types total)
        self._mutations_last_10_ticks = 0  # Track mutations in last 10 ticks for rate
        self._recent_driver_mutations = {}  # Track which drivers mutated recently (last 5 ticks)
        self._previous_requests_count = 0  # Track request generation per tick
        self._previous_behaviour_snapshots = {}  # Map of driver_id -> (last_tick, behaviour_type) for single-pass tracking
        self._previous_expired_count = 0   # Track expiration per tick
    
    def record_tick(self, simulation):
        """Record all metrics for current tick."""
        required_attrs = ['time', 'served_count', 'expired_count', 'avg_wait', 'requests', 'drivers']
        for attr in required_attrs:
            if not hasattr(simulation, attr):
                raise AttributeError(
                    f"Simulation missing required attribute '{attr}'. "
                    f"SimulationTimeSeries.record_tick() requires: {', '.join(required_attrs)}"
                )
        
        # Append time-1 to match the tick number where events actually occurred
        # (record_tick is called after time increment, so simulation.time is already T+1)
        self.times.append(simulation.time - 1)
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
        self._track_request_queue_dynamics(simulation)
        self._track_driver_state_distribution(simulation)
        self._track_system_load_indicators(simulation)
    
    def _track_behaviour_changes(self, simulation):
        """Track behaviour mutations, distribution, and stability."""
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
        
        # Count mutations using mutation_history as single source of truth
        mutations_this_tick = 0
        transitions = defaultdict(int)  # from_behaviour -> to_behaviour counts
        
        # Get mutations that occurred this tick from mutation_history
        # Note: mutations are recorded during phase 8 with current time, then time is incremented in phase 9
        # So when record_tick is called (after tick), simulation.time has already been incremented
        # We need to check for mutations at (time - 1) to match mutations from the tick that just completed
        if hasattr(simulation, 'mutation_rule') and hasattr(simulation.mutation_rule, 'mutation_history'):
            mutations_this_tick = self._count_mutations_this_tick(
                simulation.mutation_rule.mutation_history,
                simulation.time - 1  # Check for mutations from the previous tick (which just completed)
            )
            
            # Update recent mutations tracking
            # Get mutations from the tick that just completed (time - 1)
            current_tick_mutations = [
                entry for entry in simulation.mutation_rule.mutation_history
                if entry.get('time') == simulation.time - 1
            ]
            
            for entry in current_tick_mutations:
                driver_id = entry.get('driver_id')
                if driver_id:
                    if driver_id not in self.driver_mutation_freq:
                        self.driver_mutation_freq[driver_id] = 0
                    self.driver_mutation_freq[driver_id] += 1
                    self._recent_driver_mutations[driver_id] = simulation.time
                    
                    # Build transitions for diagnostics
                    old_behaviour = entry.get('from_behaviour', 'Unknown')
                    new_behaviour = entry.get('to_behaviour', 'Unknown')
                    transitions[f"{old_behaviour}→{new_behaviour}"] += 1
        
        # Update total mutations counter
        self._total_mutations += mutations_this_tick
        
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
            # Remove oldest mutation count from the rolling window
            oldest_idx = len(self.mutation_rate) - 10
            if oldest_idx >= 0 and oldest_idx < len(self.mutation_rate):
                # Rebuild from actual last 10 values
                self._mutations_last_10_ticks = sum(self.mutation_rate[-10:])
        
        # Calculate effective mutation rate: 
        # mutations_this_tick / 10 gives rate per tick, then *10 for 10-tick window
        # This shows the sustainable mutation rate accounting for cooldowns
        mutation_rate = self._mutations_last_10_ticks / 10.0  # Average per tick over last 10
        
        # Track mutation reasons from mutation rule
        self._track_mutation_reasons(simulation)
        
        # Record metrics
        self.behaviour_distribution.append(dict(behaviour_counts))
        self.mutation_rate.append(mutation_rate)
        self.mutations_per_tick.append(mutations_this_tick)  # Track actual mutations this tick
        self.stable_ratio.append(stable_ratio)
        self.mutation_reasons.append(self._mutation_reason_counts.copy())
        
        # Update snapshot for next tick's change detection
        self._previous_behaviour_snapshots = current_behaviours.copy()
    
    def _count_mutations_this_tick(self, mutation_history, current_tick):
        """Count mutations recorded at given tick."""
        if not mutation_history:
            return 0
        
        # Count entries with 'time' == current_tick (mutation_history uses 'time' field)
        return sum(1 for entry in mutation_history if entry.get('time') == current_tick)
    
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
            'exit_lazy': 0,
            'stagnation_exploration': 0
        }
        
        for entry in rule.mutation_history:
            reason = entry.get('reason', '')
            
            # Normalize reason strings to standard keys
            # Handle both short and long format reason names
            if 'performance_low_earnings' in reason:
                reason_counts['performance_low_earnings'] += 1
            elif 'performance_high_earnings' in reason:
                reason_counts['performance_high_earnings'] += 1
            elif 'stagnation_exploration' in reason:
                reason_counts['stagnation_exploration'] += 1
            elif 'exit_greedy' in reason or 'exit_greedydistancebehaviour' in reason:
                reason_counts['exit_greedy'] += 1
            elif 'exit_earnings' in reason or 'exit_earningsmaxbehaviour' in reason:
                reason_counts['exit_earnings'] += 1
            elif 'exit_lazy' in reason or 'exit_lazybehaviour' in reason:
                reason_counts['exit_lazy'] += 1
        
        self._mutation_reason_counts = reason_counts
    
    def _track_offers_and_policies(self, simulation) -> None:
        """
        Track offer generation, acceptance, quality, and policy distribution.
        Handles offers at (time-1) matching phase timing.
        """
        # Check if simulation has offer history attribute
        if not hasattr(simulation, 'offer_history'):
            # Initialize default tracking if not present
            self.offers_generated.append(0)
            self.offer_acceptance_rate.append(0.0)
            self.policy_distribution.append({})
            self.avg_offer_quality.append(0.0)
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
        
        # Detect actual policy used (for AdaptiveHybridPolicy breakdown)
        actual_policy = self._detect_actual_policy(simulation, current_tick_offers)
        self.actual_policy_used.append(actual_policy)
        
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
        self.offer_acceptance_rate.append(acceptance_rate)
        self.policy_distribution.append(dict(policy_driver_counts))
        
        # Calculate offers vs assignments efficiency
        offers_accepted = len([o for o in current_tick_offers if getattr(o.request, 'status', None) != 'WAITING'])
        self.offers_vs_assignments.append((len(current_tick_offers), offers_accepted))
        
        # Calculate matching efficiency
        matching_eff = (offers_accepted / len(current_tick_offers) * 100.0) if current_tick_offers else 0.0
        self.matching_efficiency.append(matching_eff)
        
        # Calculate rejection rate (offers that were rejected)
        offers_rejected = len([o for o in current_tick_offers if getattr(o.request, 'status', None) == 'WAITING'])
        rejection_rate = (offers_rejected / len(current_tick_offers) * 100.0) if current_tick_offers else 0.0
        self.rejection_rate.append(rejection_rate)
        
        # Count conflicts (offers competing for same request)
        request_offer_counts = defaultdict(int)
        for offer in current_tick_offers:
            request_id = getattr(offer.request, 'id', None)
            if request_id is not None:
                request_offer_counts[request_id] += 1
        
        conflict_count = len([count for count in request_offer_counts.values() if count > 1])
        self.conflict_count.append(conflict_count)
        
        # Track behaviour-specific acceptance rates
        behaviour_offers = defaultdict(lambda: {'total': 0, 'accepted': 0})
        for offer in current_tick_offers:
            behaviour = getattr(offer.driver, 'behaviour', None)
            if behaviour:
                behaviour_name = type(behaviour).__name__
                behaviour_offers[behaviour_name]['total'] += 1
                if getattr(offer.request, 'status', None) != 'WAITING':
                    behaviour_offers[behaviour_name]['accepted'] += 1
        
        for behaviour_name, counts in behaviour_offers.items():
            acceptance_rate_beh = (counts['accepted'] / counts['total'] * 100.0) if counts['total'] > 0 else 0.0
            self.acceptance_rate_by_behaviour[behaviour_name].append(acceptance_rate_beh)
    
    def _track_request_queue_dynamics(self, simulation) -> None:
        """Track pending requests, age pressure, and queue metrics."""
        # Count pending (WAITING) requests
        pending_count = len([r for r in simulation.requests if getattr(r, 'status', None) == 'WAITING'])
        self.pending_requests.append(pending_count)
        
        # Track request ages
        if pending_count > 0:
            ages = [simulation.time - getattr(r, 'creation_time', simulation.time) 
                    for r in simulation.requests if getattr(r, 'status', None) == 'WAITING']
            self.max_request_age.append(max(ages) if ages else 0)
            self.avg_request_age.append(sum(ages) / len(ages) if ages else 0)
        else:
            self.max_request_age.append(0)
            self.avg_request_age.append(0)
    
    def _track_driver_state_distribution(self, simulation) -> None:
        """Track driver status distribution and earnings by behaviour."""
        status_counts = defaultdict(int)
        for driver in simulation.drivers:
            status = getattr(driver, 'status', 'UNKNOWN')
            status_counts[status] += 1
        
        self.driver_status_distribution.append(dict(status_counts))
        
        # Track earnings by behaviour type
        if hasattr(simulation, 'earnings_by_behaviour'):
            for behaviour_type, earnings_list in simulation.earnings_by_behaviour.items():
                avg_earnings = sum(earnings_list) / len(earnings_list) if earnings_list else 0.0
                self.earnings_by_behaviour[behaviour_type].append(avg_earnings)
    
    def _track_system_load_indicators(self, simulation) -> None:
        """Track request generation, expiration, and efficiency ratios."""
        # Calculate request generation rate
        current_total_requests = len(simulation.requests)
        generated_this_tick = max(0, current_total_requests - self._previous_requests_count)
        self.request_generation_rate.append(generated_this_tick)
        self._previous_requests_count = current_total_requests
        
        # Calculate expiration rate
        expired_this_tick = max(0, simulation.expired_count - self._previous_expired_count)
        total_in_system = simulation.served_count + simulation.expired_count
        expiration_rate = (expired_this_tick / max(1, total_in_system)) * 100.0
        self.expiration_rate.append(expiration_rate)
        self._previous_expired_count = simulation.expired_count
        
        # Calculate served-to-expired ratio
        total = simulation.served_count + simulation.expired_count
        ratio = (simulation.served_count / total * 100.0) if total > 0 else 0.0
        self.served_to_expired_ratio.append(ratio)
    
    def _detect_actual_policy(self, simulation, offers) -> str:
        """Detect policy used (distinguishes Adaptive sub-policy).
        For AdaptiveHybridPolicy, returns whether it used NearestNeighbor
        or GlobalGreedy based on request/driver ratio.
        """
        if not hasattr(simulation, 'dispatch_policy'):
            return 'Unknown'
        
        policy_name = type(simulation.dispatch_policy).__name__
        
        # If not Adaptive, return the policy name as-is
        if policy_name != 'AdaptiveHybridPolicy':
            return policy_name
        
        # For Adaptive, detect which sub-policy was used based on driver/request ratio
        idle_drivers = sum(1 for d in simulation.drivers if getattr(d, 'status', None) == 'IDLE')
        waiting_requests = len([r for r in simulation.requests if getattr(r, 'status', None) == 'WAITING'])
        
        # AdaptiveHybridPolicy uses: 
        # - GlobalGreedyPolicy if requests > drivers
        # - NearestNeighborPolicy if drivers >= requests
        if waiting_requests > idle_drivers:
            return 'GlobalGreedyPolicy'
        else:
            return 'NearestNeighborPolicy'
    
    def get_data(self) -> dict:
        """Get all time-series metric data."""
        return {
            'times': self.times,
            'served': self.served,
            'expired': self.expired,
            'avg_wait': self.avg_wait,
            'service_level': self.service_level,
            'utilization': self.utilization,
            'behaviour_distribution': self.behaviour_distribution,
            'mutation_rate': self.mutation_rate,
            'mutations_per_tick': self.mutations_per_tick,
            'stable_ratio': self.stable_ratio,
            'mutation_reasons': self.mutation_reasons,
            'offers_generated': self.offers_generated,
            'offer_acceptance_rate': self.offer_acceptance_rate,
            'policy_distribution': self.policy_distribution,
            'avg_offer_quality': self.avg_offer_quality,
            'actual_policy_used': self.actual_policy_used,
            'pending_requests': self.pending_requests,
            'rejection_rate': self.rejection_rate,
            'max_request_age': self.max_request_age,
            'avg_request_age': self.avg_request_age,
            'offers_vs_assignments': self.offers_vs_assignments,
            'conflict_count': self.conflict_count,
            'matching_efficiency': self.matching_efficiency,
            'driver_status_distribution': self.driver_status_distribution,
            'request_generation_rate': self.request_generation_rate,
            'expiration_rate': self.expiration_rate,
            'served_to_expired_ratio': self.served_to_expired_ratio,
        }
    
    def get_final_summary(self) -> dict:
        """Get aggregated final simulation summary."""
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
        
        # Calculate queue and dispatch metrics
        avg_pending_requests = sum(self.pending_requests) / len(self.pending_requests) if self.pending_requests else 0
        avg_rejection_rate = sum(self.rejection_rate) / len(self.rejection_rate) if self.rejection_rate else 0.0
        max_request_age_final = max(self.max_request_age) if self.max_request_age else 0
        avg_matching_efficiency = sum(self.matching_efficiency) / len(self.matching_efficiency) if self.matching_efficiency else 0.0
        total_conflicts = sum(self.conflict_count) if self.conflict_count else 0
        
        # Calculate request generation and expiration metrics
        total_generated = sum(self.request_generation_rate) if self.request_generation_rate else 0
        avg_expiration_rate = sum(self.expiration_rate) / len(self.expiration_rate) if self.expiration_rate else 0.0
        
        # Calculate actual policy usage (for Adaptive breakdown)
        policy_usage = Counter(self.actual_policy_used)
        
        # Calculate utilization variance (measures system load consistency)
        import statistics
        utilization_variance = statistics.variance(self.utilization) if len(self.utilization) > 1 else 0.0
        avg_utilization = sum(self.utilization) / len(self.utilization) if self.utilization else 0.0
        
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
            'actual_policy_usage': dict(policy_usage),  # Shows NN vs GG breakdown if Adaptive
            'avg_pending_requests': avg_pending_requests,
            'avg_rejection_rate': avg_rejection_rate,
            'max_request_age': max_request_age_final,
            'avg_matching_efficiency': avg_matching_efficiency,
            'total_offer_conflicts': total_conflicts,
            'total_requests_generated': total_generated,
            'avg_expiration_rate': avg_expiration_rate,
            'final_served_to_expired_ratio': self.served_to_expired_ratio[-1] if self.served_to_expired_ratio else 0.0,
            'avg_utilization': avg_utilization,
            'utilization_variance': utilization_variance,
        }


# ====================================================================
# TEXT FORMATTING FUNCTIONS FOR VISUALIZATION
# ====================================================================

def format_summary_statistics(simulation, time_series) -> str:
    """Format final simulation summary as text.
    
    Args:
        simulation: DeliverySimulation instance.
        time_series: SimulationTimeSeries with metrics.
        
    Returns:
        Formatted text block.
    """
    # Get final summary
    if time_series:
        summary = time_series.get_final_summary()
    else:
        summary = get_simulation_summary(simulation)
    
    # Calculate utilization display
    avg_util = summary.get('avg_utilization', 0)
    util_var = summary.get('utilization_variance', 0)
    util_display = f"{avg_util:.1%} (var: {util_var:.2f})" if util_var is not None else f"{avg_util:.1%}"
    
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
System Stability:      Utilization {util_display}

Drivers Deployed:      {len(simulation.drivers)}
"""
    return stats_text


def format_behaviour_statistics(simulation, time_series) -> str:
    """Format behaviour distribution statistics as text."""
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
    """Format performance impact metrics as text."""
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
    """Format mutation rule configuration as text."""
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
