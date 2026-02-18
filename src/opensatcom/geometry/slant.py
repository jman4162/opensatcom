"""Slant range and elevation geometry computations."""

from __future__ import annotations

import math

from opensatcom.core.constants import EARTH_RADIUS_M


def slant_range_m(terminal_alt_m: float, sat_alt_m: float, elev_deg: float) -> float:
    """Compute slant range using law of cosines.

    Parameters
    ----------
    terminal_alt_m : float
        Terminal altitude above sea level (m).
    sat_alt_m : float
        Satellite altitude above sea level (m).
    elev_deg : float
        Elevation angle from terminal to satellite (degrees).

    Returns
    -------
    float
        Slant range in metres.
    """
    r_t = EARTH_RADIUS_M + terminal_alt_m
    r_s = EARTH_RADIUS_M + sat_alt_m
    elev_rad = math.radians(elev_deg)

    # Law of cosines: d^2 = r_t^2 + r_s^2 - 2*r_t*r_s*cos(gamma)
    # where gamma = pi/2 + elev - arcsin(r_t/r_s * cos(elev))
    # Simpler form using Earth-centric angle:
    # d = -r_t*sin(elev) + sqrt((r_t*sin(elev))^2 + r_s^2 - r_t^2)
    sin_e = math.sin(elev_rad)
    d = -r_t * sin_e + math.sqrt((r_t * sin_e) ** 2 + r_s**2 - r_t**2)
    return d


def elevation_deg(terminal_alt_m: float, sat_alt_m: float, range_m: float) -> float:
    """Compute elevation angle given slant range (inverse of slant_range_m).

    Parameters
    ----------
    terminal_alt_m : float
        Terminal altitude above sea level in metres.
    sat_alt_m : float
        Satellite altitude above sea level in metres.
    range_m : float
        Slant range in metres.

    Returns
    -------
    float
        Elevation angle in degrees.
    """
    r_t = EARTH_RADIUS_M + terminal_alt_m
    r_s = EARTH_RADIUS_M + sat_alt_m

    # From law of cosines: r_s^2 = r_t^2 + d^2 + 2*r_t*d*sin(elev)
    # sin(elev) = (r_s^2 - r_t^2 - d^2) / (2*r_t*d)
    sin_e = (r_s**2 - r_t**2 - range_m**2) / (2.0 * r_t * range_m)
    return math.degrees(math.asin(sin_e))
