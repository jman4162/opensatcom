"""Free-space path loss propagation model."""

from __future__ import annotations

import math

from opensatcom.core.constants import SPEED_OF_LIGHT_MPS
from opensatcom.core.models import PropagationConditions


class FreeSpacePropagation:
    """Free-space path loss model.

    Computes ``FSPL(dB) = 20 * log10(4 * pi * d * f / c)`` where *d* is the
    slant range and *f* is the carrier frequency.

    Examples
    --------
    >>> prop = FreeSpacePropagation()
    >>> prop.total_path_loss_db(12e9, 30.0, 37e6, PropagationConditions())
    205.3  # approximate
    """

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        """Compute free-space path loss.

        Parameters
        ----------
        f_hz : float
            Carrier frequency in Hz.
        elev_deg : float
            Elevation angle in degrees (unused for FSPL).
        range_m : float
            Slant range in metres.
        cond : PropagationConditions
            Environmental conditions (unused for FSPL).

        Returns
        -------
        float
            Free-space path loss in dB (positive value).
        """
        return 20.0 * math.log10(4.0 * math.pi * range_m * f_hz / SPEED_OF_LIGHT_MPS)
