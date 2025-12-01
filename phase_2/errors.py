from __future__ import annotations

#-----------------------------------
# Simulation Error
#-----------------------------------

class SimulationError(Exception):
    """ Base class for simulation-related errors. """
    pass

#-----------------------------------
# Invalid Request State Error
#-----------------------------------

class InvalidRequestStateError(SimulationError):
    """ Raised when an invalid request state is encountered. """
    pass

#-----------------------------------
# Invalid Driver Operation Error
#-----------------------------------

class InvalidDriverOperationError(SimulationError):
    """ Raised when an invalid driver operation occurs. """
    pass

