"""Doppler shift computation for satellite links."""

from __future__ import annotations

from opensatcom.core.constants import SPEED_OF_LIGHT_MPS


def doppler_shift_hz(f_hz: float, v_radial_mps: float) -> float:
    """Compute Doppler frequency shift from radial velocity.

    Parameters
    ----------
    f_hz : float
        Carrier frequency in Hz.
    v_radial_mps : float
        Radial velocity of the satellite relative to the ground station
        in m/s. Positive means the satellite is moving away (red shift),
        negative means approaching (blue shift).

    Returns
    -------
    float
        Doppler shift in Hz. Negative when satellite approaches
        (frequency increases), positive when satellite recedes.
    """
    return -f_hz * v_radial_mps / SPEED_OF_LIGHT_MPS
