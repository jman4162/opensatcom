"""Unit conversion utilities for dB and power domains."""

from __future__ import annotations

import math


def lin_to_db10(x: float) -> float:
    """Convert linear power ratio to dB (10*log10)."""
    return 10.0 * math.log10(x)


def db10_to_lin(x_db: float) -> float:
    """Convert dB to linear power ratio (10^(x/10))."""
    return float(10.0 ** (x_db / 10.0))


def lin_to_db20(x: float) -> float:
    """Convert linear amplitude ratio to dB (20*log10)."""
    return 20.0 * math.log10(x)


def db20_to_lin(x_db: float) -> float:
    """Convert dB to linear amplitude ratio (10^(x/20))."""
    return float(10.0 ** (x_db / 20.0))


def w_to_dbw(w: float) -> float:
    """Convert watts to dBW."""
    return 10.0 * math.log10(w)


def dbw_to_w(dbw: float) -> float:
    """Convert dBW to watts."""
    return float(10.0 ** (dbw / 10.0))
