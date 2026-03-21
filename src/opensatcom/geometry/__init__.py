"""Geometry computations for OpenSatCom."""

from opensatcom.geometry.doppler import doppler_shift_hz
from opensatcom.geometry.slant import elevation_deg, slant_range_m

__all__ = ["doppler_shift_hz", "elevation_deg", "slant_range_m"]
