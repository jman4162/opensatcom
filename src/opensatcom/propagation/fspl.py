"""Free-space path loss propagation model."""

from __future__ import annotations

import math

from opensatcom.core.constants import SPEED_OF_LIGHT_MPS
from opensatcom.core.models import PropagationConditions


class FreeSpacePropagation:
    """Free-space path loss: FSPL(dB) = 20*log10(4*pi*d*f/c)."""

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        return 20.0 * math.log10(4.0 * math.pi * range_m * f_hz / SPEED_OF_LIGHT_MPS)
