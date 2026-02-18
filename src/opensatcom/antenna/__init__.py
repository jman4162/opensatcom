"""Antenna models for OpenSatCom."""

from opensatcom.antenna.cosine import CosineRolloffAntenna
from opensatcom.antenna.pam import PamArrayAntenna
from opensatcom.antenna.parametric import ParametricAntenna

__all__ = ["CosineRolloffAntenna", "PamArrayAntenna", "ParametricAntenna"]
