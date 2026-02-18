"""ITU-R P.676 gaseous absorption propagation model."""

from __future__ import annotations

import math

from opensatcom.core.models import PropagationConditions


def _specific_dry_attenuation(f_ghz: float) -> float:
    """Approximate specific attenuation for dry air (dB/km).

    Simplified ITU-R P.676 model capturing O2 resonance near 60 GHz
    and general frequency dependence.
    """
    # O2 resonance line complex near 60 GHz
    # Simplified: base + resonance peak
    gamma_base = 7.2e-3 + 6.0e-3 * (f_ghz / 57.0) ** 2
    # O2 resonance peak around 60 GHz
    gamma_o2 = 0.0
    if 50.0 < f_ghz < 70.0:
        x = (f_ghz - 60.0) / 5.0
        gamma_o2 = 15.0 * math.exp(-0.5 * x * x)
    elif 118.0 < f_ghz < 120.0:
        x = (f_ghz - 118.75) / 1.0
        gamma_o2 = 3.0 * math.exp(-0.5 * x * x)
    return gamma_base + gamma_o2


def _specific_wet_attenuation(f_ghz: float, rho_g_m3: float) -> float:
    """Approximate specific attenuation for water vapor (dB/km).

    Simplified ITU-R P.676 model capturing H2O resonance near 22.2 GHz
    and 183.3 GHz.
    """
    # Water vapor resonance at 22.2 GHz
    x_22 = (f_ghz - 22.235) / 4.0
    gamma_22 = 0.067 * rho_g_m3 / 7.5 * math.exp(-0.5 * x_22 * x_22)

    # General frequency-dependent term
    gamma_base = 0.050 * (f_ghz / 100.0) ** 1.5 * (rho_g_m3 / 7.5)

    # Water vapor resonance at 183.3 GHz
    gamma_183 = 0.0
    if 175.0 < f_ghz < 195.0:
        x_183 = (f_ghz - 183.31) / 3.0
        gamma_183 = 4.0 * rho_g_m3 / 7.5 * math.exp(-0.5 * x_183 * x_183)

    return gamma_base + gamma_22 + gamma_183


class GaseousAbsorptionP676:
    """ITU-R P.676 gaseous absorption model.

    Computes combined dry-air (O2) and water-vapor (H2O) absorption loss.
    Simplified model with frequency-dependent specific attenuation
    multiplied by slant path length through the atmosphere.

    Parameters
    ----------
    water_vapor_density_g_m3 : float
        Surface water vapor density in g/m^3. Default 7.5 g/m^3
        (standard mid-latitude).
    """

    def __init__(self, water_vapor_density_g_m3: float = 7.5) -> None:
        self.rho = water_vapor_density_g_m3

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        """Compute gaseous absorption loss in dB.

        Parameters
        ----------
        f_hz : float
            Carrier frequency in Hz.
        elev_deg : float
            Elevation angle in degrees.
        range_m : float
            Slant range in metres (unused; path derived from elevation).
        cond : PropagationConditions
            Environmental conditions (unused; water vapor set at construction).

        Returns
        -------
        float
            Combined dry-air and water-vapor absorption in dB
            (0.0 if frequency < 1 GHz).
        """
        f_ghz = f_hz / 1e9
        if f_ghz < 1.0:
            return 0.0

        gamma_dry = _specific_dry_attenuation(f_ghz)
        gamma_wet = _specific_wet_attenuation(f_ghz, self.rho)

        # Equivalent atmosphere height (simplified)
        # Dry: ~6 km effective height, Wet: ~2.1 km effective height
        h_dry_km = 6.0
        h_wet_km = 2.1

        elev_rad = math.radians(max(elev_deg, 5.0))
        sin_elev = math.sin(elev_rad)

        # Slant path attenuation
        a_dry = gamma_dry * h_dry_km / sin_elev
        a_wet = gamma_wet * h_wet_km / sin_elev

        return a_dry + a_wet
