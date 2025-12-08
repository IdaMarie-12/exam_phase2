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
