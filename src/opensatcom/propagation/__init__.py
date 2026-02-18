"""Propagation models for OpenSatCom."""

from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation
from opensatcom.propagation.gas import GaseousAbsorptionP676
from opensatcom.propagation.rain import RainAttenuationP618
from opensatcom.propagation.scintillation import ScintillationLoss

__all__ = [
    "CompositePropagation",
    "FreeSpacePropagation",
    "GaseousAbsorptionP676",
    "RainAttenuationP618",
    "ScintillationLoss",
]
