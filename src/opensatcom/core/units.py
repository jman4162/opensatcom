"""Unit conversion utilities for dB and power domains.

Provides symmetric conversion pairs for power ratios (10 log10),
amplitude ratios (20 log10), and absolute power (watts / dBW).
"""

from __future__ import annotations

import math


def lin_to_db10(x: float) -> float:
    """Convert a linear power ratio to decibels.

    Parameters
    ----------
    x : float
        Linear power ratio (must be > 0).

    Returns
    -------
    float
        Value in dB: ``10 * log10(x)``.

    Examples
    --------
    >>> lin_to_db10(100.0)
    20.0
    """
    return 10.0 * math.log10(x)


def db10_to_lin(x_db: float) -> float:
    """Convert decibels to a linear power ratio.

    Parameters
    ----------
    x_db : float
        Value in dB.

    Returns
    -------
    float
        Linear power ratio: ``10^(x_db / 10)``.

    Examples
    --------
    >>> db10_to_lin(20.0)
    100.0
    """
    return float(10.0 ** (x_db / 10.0))


def lin_to_db20(x: float) -> float:
    """Convert a linear amplitude ratio to decibels.

    Parameters
    ----------
    x : float
        Linear amplitude ratio (must be > 0).

    Returns
    -------
    float
        Value in dB: ``20 * log10(x)``.

    Examples
    --------
    >>> lin_to_db20(10.0)
    20.0
    """
    return 20.0 * math.log10(x)


def db20_to_lin(x_db: float) -> float:
    """Convert decibels to a linear amplitude ratio.

    Parameters
    ----------
    x_db : float
        Value in dB.

    Returns
    -------
    float
        Linear amplitude ratio: ``10^(x_db / 20)``.

    Examples
    --------
    >>> db20_to_lin(20.0)
    10.0
    """
    return float(10.0 ** (x_db / 20.0))


def w_to_dbw(w: float) -> float:
    """Convert watts to dBW.

    Parameters
    ----------
    w : float
        Power in watts (must be > 0).

    Returns
    -------
    float
        Power in dBW: ``10 * log10(w)``.

    Examples
    --------
    >>> w_to_dbw(100.0)
    20.0
    """
    return 10.0 * math.log10(w)


def dbw_to_w(dbw: float) -> float:
    """Convert dBW to watts.

    Parameters
    ----------
    dbw : float
        Power in dBW.

    Returns
    -------
    float
        Power in watts: ``10^(dbw / 10)``.

    Examples
    --------
    >>> dbw_to_w(20.0)
    100.0
    """
    return float(10.0 ** (dbw / 10.0))
