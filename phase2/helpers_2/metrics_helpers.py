"""Time-series metrics tracking for post-simulation analysis."""


class SimulationTimeSeries:
    """Records simulation metrics at each timestep. Call record_tick() after each tick."""
    
    def __init__(self):
        self.times = []
        self.served = []
        self.expired = []
        self.avg_wait = []
        self.pending = []
        self.utilization = []
    
    def record_tick(self, simulation):
        """Capture current simulation state."""
        self.times.append(simulation.time)
        self.served.append(simulation.served_count)
        self.expired.append(simulation.expired_count)
        self.avg_wait.append(simulation.avg_wait)
        
        # Count pending requests
        pending_count = len([r for r in simulation.requests 
                            if r.status in ('WAITING', 'ASSIGNED', 'PICKED')])
        self.pending.append(pending_count)
        
        # Driver utilization
        busy_drivers = sum(1 for d in simulation.drivers if d.status != 'IDLE')
        utilization = (busy_drivers / len(simulation.drivers) * 100.0) if simulation.drivers else 0.0
        self.utilization.append(utilization)
    
    def get_data(self):
        """Return all time-series data as dict."""
        return {
            'times': self.times,
            'served': self.served,
            'expired': self.expired,
            'avg_wait': self.avg_wait,
            'pending': self.pending,
            'utilization': self.utilization,
        }
    
    def get_final_summary(self):
        """Return final summary statistics."""
        if not self.times:
            return {}
        
        total = self.served[-1] + self.expired[-1]
        return {
            'total_time': self.times[-1],
            'final_served': self.served[-1],
            'final_expired': self.expired[-1],
            'final_avg_wait': self.avg_wait[-1],
            'total_requests': total,
            'service_level': (self.served[-1] / total * 100.0) if total > 0 else 0.0,
        }
