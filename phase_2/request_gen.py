from __future__ import annotations

from dataclasses import dataclass
from typing import List
import random

from phase2.model import Request, Point

#-----------------------------------
# Request Generator
#-----------------------------------
@dataclass
class RequestGenerator:
    """ Generate new requests over time at a given expected rate. """

    rate: float
    width: int
    height: int
    rng: random.Random
    next_id: int = 0

    def maybe_generate(self, time: int) -> List[Request]:
        """ Return a list of newly generated requests for this tick."""
        new_requests: List[Request] = []

        return new_requests