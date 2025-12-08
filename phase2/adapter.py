from __future__ import annotations
from typing import Any, Dict
from code.phase2.simulation import DeliverySimulation


class SimulationAdapter:
    """
    Thin procedural façade used by the GUI.
    The GUI calls simple functions (init, step, get data)
    while this adapter internally drives the simulation engine.
    """

    def __init__(self):
        self.sim: DeliverySimulation | None = None

    # ----------------------------------------------------------
    # PUBLIC API (called by dispatch_ui.py / GUI)

    def init_simulation(self, config: Dict[str, Any]) -> None:
        """
        Create an OOP DeliverySimulation using GUI-provided config.
        The adapter translates raw GUI dictionaries/lists into
        objects expected by the simulation engine.
        """
        self.sim = DeliverySimulation(
            drivers=config["drivers"],
            dispatch_policy=config["dispatch_policy"],
            request_generator=config["generator"],
            mutation_rule=config["mutation_rule"],
            timeout=config.get("timeout", 20),
        )

    def step_simulation(self) -> None:
        """
        Run a single simulation tick.
        Called repeatedly by the teacher GUI.
        """
        if self.sim is None:
            raise RuntimeError("Simulation not initialized.")
        self.sim.tick()

    def get_plot_data(self) -> Dict[str, Any]:
        """
        Returns GUI-friendly metrics and state needed for plotting.
        Uses the simulation's snapshot(), ensuring the GUI does not
        depend on internal objects or class structures.
        """
        if self.sim is None:
            raise RuntimeError("Simulation not initialized.")

        snap = self.sim.get_snapshot()   # from simulation.py

        return {
            "time": snap["time"],
            "drivers": snap["drivers"],
            "pickups": snap["pickups"],
            "dropoffs": snap["dropoffs"],
            "metrics": snap["metrics"],   # full matrix for visualisation
        }

    # ----------------------------------------------------------
    # INTERNAL helpers

    def _extract_driver_states(self) -> Dict[int, Dict[str, Any]]:
        """
        Extracts essential, serializable driver info.
        Not used by GUI directly—helper for future extensions.
        """
        if self.sim is None:
            raise RuntimeError("Simulation not initialized.")

        result = {}
        for d in self.sim.drivers:
            result[d.id] = {
                "x": d.position.x,
                "y": d.position.y,
                "status": d.status,
                "behavior": type(d.behaviour).__name__ if d.behaviour else None,
            }
        return result
