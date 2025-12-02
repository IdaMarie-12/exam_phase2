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
"""The arrival of new requests should follow a fixed average rate (as in Part I), but now modelled as a
separate object.
Attributes (suggested):
– rate: float (expected number of new requests per tick),
– a random number generator,
– next_id: int (for request identifiers)
– map boundaries (width and height)."""
    def maybe_generate(self, time: int) -> list[Request]:
        """Called once per tick. Draws, according to a user's defined rule, and returns N new Request
        objects whose creation_time is 'time' and whose pickup/dropoff points
        are valid positions in the map.
        """


    def __init__(self, rate: float, width: int, height: int, seed: int | None = None) -> None:
        """ Initialize the request generator. """
        self.rate = rate
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.next_id = 0
