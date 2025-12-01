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

    def __init__(self, rate: float, width: int, height: int, seed: int | None = None) -> None:
        """ Initialize the request generator. """
        self.rate = rate
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.next_id = 0

    def maybe_generate(self, time: int) -> List[Request]:
        """ Generate new requests over time. """
        raise NotImplementedError
