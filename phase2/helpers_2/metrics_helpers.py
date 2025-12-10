class Metrics:
    """
    Global metrics collector for behaviours, used to count how many offers each behaviour
    accepted or rejected.
    """

    stats = {}

    @classmethod
    def record_decision(cls, behaviour, accepted: bool):
        name = behaviour.__class__.__name__
        if name not in cls.stats:
            cls.stats[name] = {"accepted": 0, "rejected": 0}

        if accepted:
            cls.stats[name]["accepted"] += 1
        else:
            cls.stats[name]["rejected"] += 1

    @classmethod
    def reset(cls):
        cls.stats = {}

    @classmethod
    def get_stats(cls):
        return cls.stats

#---------------------------------
    #simulation metrics
class SimulationMetrics:
    """
    Collects all simulation performance metrics:
    wait times, completion count, expiration, earnings,
    and behaviour comparisons.
    """
    def __init__(self):
        self.served = 0
        self.expired = 0
        self.wait_times = []
        self.earnings = {}

    def record_expired(self):
        self.expired += 1

    def record_completed_trip(self, driver):
        last = driver.history[-1]
        wait = last["time"] - last["start_time"]
        self.wait_times.append(wait)
        self.served += 1

        beh = type(driver.behaviour).__name__
        self.earnings.setdefault(beh, 0)
        self.earnings[beh] += last.get("fare", 0.0)

    def snapshot_for_gui(self, sim):
        """Data formatted for GUI plotting."""
        return {
            "time": sim.time,
            "served": self.served,
            "expired": self.expired,
            "avg_wait": sum(self.wait_times)/len(self.wait_times) if self.wait_times else 0,
            "earnings": self.earnings,
        }


# ====================================================================
# TIME-SERIES METRICS TRACKING FOR POST-SIMULATION ANALYSIS
# ====================================================================

class SimulationTimeSeries:
    """
    Records simulation metrics at each timestep for post-simulation analysis.
    
    Tracks evolution of key performance indicators over time:
    - Served requests (cumulative)
    - Expired requests (cumulative)
    - Average wait time (rolling)
    - Pending requests (snapshot)
    - Driver utilization (snapshot)
    
    Call record_tick() after each simulation.tick() to capture state.
    
    Example:
        >>> series = SimulationTimeSeries()
        >>> for _ in range(1000):
        ...     sim.tick()
        ...     series.record_tick(sim)
        >>> series.plot_metrics()  # Generate plots
    """
    
    def __init__(self):
        """Initialize time-series tracker."""
        self.times = []
        self.served = []
        self.expired = []
        self.avg_wait = []
        self.pending = []
        self.utilization = []
    
    def record_tick(self, simulation):
        """
        Record metrics at current simulation timestep.
        
        Args:
            simulation: DeliverySimulation instance with current state
        """
        self.times.append(simulation.time)
        self.served.append(simulation.served_count)
        self.expired.append(simulation.expired_count)
        self.avg_wait.append(simulation.avg_wait)
        
        # Count pending requests
        pending_count = len([r for r in simulation.requests 
                            if r.status.name in ('WAITING', 'ASSIGNED', 'PICKED')])
        self.pending.append(pending_count)
        
        # Driver utilization
        busy_drivers = sum(1 for d in simulation.drivers if d.status != 'IDLE')
        utilization = (busy_drivers / len(simulation.drivers) * 100.0) if simulation.drivers else 0.0
        self.utilization.append(utilization)
    
    def get_data(self):
        """
        Get all recorded time-series data.
        
        Returns:
            Dict with keys: times, served, expired, avg_wait, pending, utilization
            Each value is a list of measurements over time.
        """
        return {
            'times': self.times,
            'served': self.served,
            'expired': self.expired,
            'avg_wait': self.avg_wait,
            'pending': self.pending,
            'utilization': self.utilization,
        }
    
    def get_final_summary(self):
        """
        Get final summary statistics from recorded time-series.
        
        Returns:
            Dict with summary metrics at end of simulation
        """
        if not self.times:
            return {}
        
        return {
            'total_time': self.times[-1],
            'final_served': self.served[-1],
            'final_expired': self.expired[-1],
            'final_avg_wait': self.avg_wait[-1],
            'total_requests': self.served[-1] + self.expired[-1],
            'service_level': (self.served[-1] / (self.served[-1] + self.expired[-1]) * 100.0) 
                           if (self.served[-1] + self.expired[-1]) > 0 else 0.0,
        }
