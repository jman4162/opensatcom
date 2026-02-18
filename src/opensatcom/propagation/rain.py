"""ITU-R P.618 rain attenuation propagation model."""

from __future__ import annotations

import math

from opensatcom.core.models import PropagationConditions

# ITU-R P.838 regression coefficients (k, alpha) for horizontal polarization
# Selected frequency breakpoints (GHz) -> (k_h, alpha_h)
_P838_COEFFS: list[tuple[float, float, float]] = [
    (1.0, 0.0000387, 0.912),
    (2.0, 0.000154, 0.963),
    (4.0, 0.000650, 1.121),
    (6.0, 0.00175, 1.308),
    (7.0, 0.00301, 1.332),
    (8.0, 0.00454, 1.327),
    (10.0, 0.0101, 1.276),
    (12.0, 0.0188, 1.217),
    (15.0, 0.0367, 1.154),
    (20.0, 0.0751, 1.099),
    (25.0, 0.124, 1.061),
    (30.0, 0.187, 1.021),
    (35.0, 0.263, 0.979),
    (40.0, 0.350, 0.939),
    (45.0, 0.442, 0.903),
    (50.0, 0.536, 0.873),
]


def _interpolate_p838(f_ghz: float) -> tuple[float, float]:
    """Interpolate ITU-R P.838 k and alpha for given frequency."""
    if f_ghz <= _P838_COEFFS[0][0]:
        return _P838_COEFFS[0][1], _P838_COEFFS[0][2]
    if f_ghz >= _P838_COEFFS[-1][0]:
        return _P838_COEFFS[-1][1], _P838_COEFFS[-1][2]

    for i in range(len(_P838_COEFFS) - 1):
        f0, k0, a0 = _P838_COEFFS[i]
        f1, k1, a1 = _P838_COEFFS[i + 1]
        if f0 <= f_ghz <= f1:
            # Log-linear interpolation for k, linear for alpha
            t = (math.log10(f_ghz) - math.log10(f0)) / (math.log10(f1) - math.log10(f0))
            k = 10.0 ** (math.log10(k0) + t * (math.log10(k1) - math.log10(k0)))
            alpha = a0 + t * (a1 - a0)
            return k, alpha

    return _P838_COEFFS[-1][1], _P838_COEFFS[-1][2]


class RainAttenuationP618:
    """ITU-R P.618 rain attenuation model.

    Computes rain-induced path loss using specific attenuation from ITU-R P.838
    coefficients and effective path length derived from elevation angle.

    Parameters
    ----------
    availability_target : float
        Target link availability (e.g. 0.99 for 99%).
    rain_rate_mm_per_hr : float | None
        Rain rate. If None, uses value from PropagationConditions.
    climate_region : str | None
        ITU rain climate region (for future region-based rain rate lookup).
    """

    def __init__(
        self,
        availability_target: float = 0.99,
        rain_rate_mm_per_hr: float | None = None,
        climate_region: str | None = None,
    ) -> None:
        self.availability_target = availability_target
        self._rain_rate = rain_rate_mm_per_hr
        self._climate_region = climate_region

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        """Compute rain attenuation in dB (additional loss beyond FSPL).

        Parameters
        ----------
        f_hz : float
            Carrier frequency in Hz.
        elev_deg : float
            Elevation angle in degrees.
        range_m : float
            Slant range in metres (unused; path length derived from elevation).
        cond : PropagationConditions
            Environmental conditions; ``rain_rate_mm_per_hr`` is used as
            fallback when not set at construction time.

        Returns
        -------
        float
            Rain attenuation in dB (0.0 if rain rate is zero or frequency < 1 GHz).
        """
        rain_rate = self._rain_rate
        if rain_rate is None and cond.rain_rate_mm_per_hr is not None:
            rain_rate = cond.rain_rate_mm_per_hr
        if rain_rate is None or rain_rate <= 0.0:
            return 0.0

        f_ghz = f_hz / 1e9
        if f_ghz < 1.0:
            return 0.0

        k, alpha = _interpolate_p838(f_ghz)

        # Specific attenuation (dB/km)
        gamma_r = k * (rain_rate ** alpha)

        # Effective path length through rain (simplified P.618)
        # Rain height ~= 3.0 km for mid-latitudes (simplified)
        h_rain_km = 3.0
        h_station_km = 0.0  # Approximate ground level

        elev_rad = math.radians(max(elev_deg, 5.0))  # Clamp to avoid division issues
        sin_elev = math.sin(elev_rad)

        # Slant path length through rain
        l_s_km = (h_rain_km - h_station_km) / sin_elev

        # Horizontal reduction factor (simplified)
        l_g_km = l_s_km * math.cos(elev_rad)
        denom = (
            1.0
            + 0.78 * math.sqrt(l_g_km * gamma_r / f_ghz)
            - 0.38 * (1.0 - math.exp(-2.0 * l_g_km))
        )
        r_001 = 1.0 / denom

        # Effective path length
        l_eff_km = l_s_km * r_001

        # Rain attenuation exceeded for 0.01% of time
        a_001 = gamma_r * l_eff_km

        # Scale to desired availability using power-law approximation
        p_target = (1.0 - self.availability_target) * 100.0  # percentage exceedance
        if p_target <= 0.0:
            p_target = 0.01  # minimum

        if p_target >= 1.0:
            # For p >= 1%, attenuation is much less
            a_p = a_001 * 0.12 * (p_target ** 0.546)
        else:
            # Scaling from 0.01% to target percentage
            ratio = p_target / 0.01
            if ratio >= 1.0:
                beta = -0.655 + 0.033 * math.log(ratio) - 0.045 * math.log(a_001)
                beta = max(beta, -0.7)
                exp = -(
                    0.655
                    + 0.033 * math.log(ratio)
                    - 0.045 * math.log(max(a_001, 0.01))
                )
                a_p = a_001 * (ratio ** exp)
            else:
                a_p = a_001

        return max(a_p, 0.0)
