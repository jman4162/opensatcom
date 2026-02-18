"""Propagation models for OpenSatCom."""

from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation

__all__ = ["CompositePropagation", "FreeSpacePropagation"]
