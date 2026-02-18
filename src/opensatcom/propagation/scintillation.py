"""Tropospheric scintillation fade margin model."""

from __future__ import annotations

import math

from opensatcom.core.models import PropagationConditions


def _inverse_gaussian_quantile(p: float) -> float:
    """Approximate inverse Gaussian CDF for availability-to-fade conversion.

    Uses Abramowitz & Stegun rational approximation.
    p is the probability (e.g. 0.99 for 99% availability).
    Returns the quantile G(p) such that P(X <= G) = p.
    """
    if p <= 0.5:
        return 0.0
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    # Rational approximation constants
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)


class ScintillationLoss:
    """Tropospheric scintillation fade margin model.

    Computes the scintillation fade margin based on frequency, elevation angle,
    and target availability. Uses a simplified model:

        sigma = C_f * f_GHz^(7/12) * (1/sin(elev))^1.2
        fade_margin = sigma * G(p)

    where G(p) is the inverse Gaussian quantile for the availability target.

    Parameters
    ----------
    availability_target : float
        Target link availability (e.g. 0.99 for 99%).
    """

    # Empirical constant (dB) for reference conditions
    _C_F: float = 0.036

    def __init__(self, availability_target: float = 0.99) -> None:
        self.availability_target = availability_target

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        """Compute scintillation fade margin in dB."""
        f_ghz = f_hz / 1e9
        if f_ghz < 1.0:
            return 0.0

        # Use availability from conditions if available, else constructor value
        avail = self.availability_target
        if cond.availability_target is not None:
            avail = cond.availability_target

        elev_rad = math.radians(max(elev_deg, 5.0))
        sin_elev = math.sin(elev_rad)

        # Scintillation standard deviation
        sigma = self._C_F * (f_ghz ** (7.0 / 12.0)) * ((1.0 / sin_elev) ** 1.2)

        # Fade margin for given availability
        g_p = _inverse_gaussian_quantile(avail)
        fade_db = sigma * g_p

        return max(fade_db, 0.0)
