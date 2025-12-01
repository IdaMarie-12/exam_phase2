from __future__ import annotations

"""
Phase 2: Object-Oriented Ride-Hailing / Food Delivery Simulation.

This package contains:

- Core domain model (Point, Request, Driver, constants).
- Driver behaviors and mutation rules.
- Dispatch policies and Offer type.
- Request generator.
- DeliverySimulation engine.
- Backend adapter to the teacher's GUI.
- Metrics plotting utilities.
"""

__all__ = [
    "model",
    "behavior",
    "policies",
    "mutation",
    "request_gen",
    "simulation",
    "backend",
    "metrics",
    "errors",
]
