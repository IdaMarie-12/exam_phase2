from __future__ import annotations

from typing import List, Dict, Tuple
import random

#-----------------------------------
# Import Phase 2 files
#-----------------------------------
from phase2.model import Driver, Request, Point
from phase2.behavior import GreedyDistanceBehavior
from phase2.policies import GlobalGreedyPolicy
from phase2.mutation import PerformanceMutationRule
from phase2.request_gen import RequestGenerator
from phase2.simulation import DeliverySimulation

#-----------------------------------
# Procedural API functions for the Dispatch UI
#-----------------------------------

def load_drivers:
    return NotImplementedError

def load_requests:
    return NotImplementedError

def generate_drivers:
    return NotImplementedError

def generate_requests:
    return NotImplementedError

def init_state():
    return NotImplementedError

def simulate_step():
    return NotImplementedError

#-----------------------------------
# Backend dict that the UI launcher expects
#-----------------------------------
backend: Dict[str, object] = {
    "load_drivers": load_drivers,
    "load_requests": load_requests,
    "generate_drivers": generate_drivers,
    "generate_requests": generate_requests,
    "init_state": init_state,
    "simulate_step": simulate_step,
}