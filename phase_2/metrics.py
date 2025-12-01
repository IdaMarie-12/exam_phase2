from __future__ import annotations
from typing import List, Dict, Any
import matplotlib.pyplot as plt

#-----------------------------------
# Plot Metrics at end of simulation
#-----------------------------------

def plot_metrics(metrics_history: List[Dict[str, Any]]) -> None:
    """ Plot metrics history """
    if not mertics_history:
        return

    time = [m["time"] for m in metrics_history]

    # Served per tick
    # Expired per tick
    # Average wait to pickup
    # Surge factor
    # Total earnings

    plt.show()