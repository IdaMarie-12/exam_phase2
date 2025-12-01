"""
Phase 2: Object-oriented delivery simulation backend.

This package contains:
- Core domain models (Point, Request, Driver)
- Behaviors (DriverBehavior and concrete subclasses)
- Dispatch policies (DispatchPolicy and concrete subclasses)
- Mutation rules
- Request generator
- DeliverySimulation engine
- A thin adapter (backend.py) that exposes a procedural API
  compatible with the teacher's Dispatch UI.
"""