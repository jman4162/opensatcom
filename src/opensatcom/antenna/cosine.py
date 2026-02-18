"""Cosine-rolloff antenna model for multi-beam payload analysis."""

from __future__ import annotations

import numpy as np

from opensatcom.core.units import w_to_dbw


class CosineRolloffAntenna:
    """Simple analytic antenna model with cosine-squared rolloff.

    Gain pattern:
        gain(theta_off) = peak_gain_dbi - 12*(theta_off / theta_3db)^2
        for theta_off < theta_3db * 2.6, otherwise sidelobe_floor_dbi.

    This produces a realistic off-axis pattern suitable for multi-beam
    interference analysis without requiring the full PAM library.
    """

    def __init__(
        self,
        peak_gain_dbi: float,
        theta_3db_deg: float,
        sidelobe_floor_dbi: float = -20.0,
        boresight_az_deg: float = 0.0,
        boresight_el_deg: float = 0.0,
    ) -> None:
        self._peak_gain_dbi = peak_gain_dbi
        self._theta_3db_deg = theta_3db_deg
        self._sidelobe_floor_dbi = sidelobe_floor_dbi
        self._boresight_az_deg = boresight_az_deg
        self._boresight_el_deg = boresight_el_deg

    @property
    def peak_gain_dbi(self) -> float:
        return self._peak_gain_dbi

    @property
    def theta_3db_deg(self) -> float:
        return self._theta_3db_deg

    @property
    def sidelobe_floor_dbi(self) -> float:
        return self._sidelobe_floor_dbi

    @property
    def boresight_az_deg(self) -> float:
        return self._boresight_az_deg

    @property
    def boresight_el_deg(self) -> float:
        return self._boresight_el_deg

    def _off_axis_angle_deg(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray
    ) -> np.ndarray:
        """Compute off-axis angle from boresight direction."""
        d_az = theta_deg - self._boresight_az_deg
        d_el = phi_deg - self._boresight_el_deg
        return np.sqrt(d_az**2 + d_el**2)

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray:
        """Return gain accounting for off-axis rolloff.

        Parameters
        ----------
        theta_deg : array — azimuth angles
        phi_deg : array — elevation angles
        f_hz : frequency (unused in analytic model)
        """
        off_axis = self._off_axis_angle_deg(theta_deg, phi_deg)
        # Main lobe: parabolic rolloff  gain = peak - 12*(theta/theta_3db)^2
        gain = self._peak_gain_dbi - 12.0 * (off_axis / self._theta_3db_deg) ** 2
        # Clamp to sidelobe floor (applies both in main lobe tail and beyond)
        gain = np.maximum(gain, self._sidelobe_floor_dbi)
        return gain

    def gain_toward_dbi(self, az_deg: float, el_deg: float, f_hz: float) -> float:
        """Scalar convenience: gain in a specific direction."""
        return float(
            self.gain_dbi(np.array([az_deg]), np.array([el_deg]), f_hz)[0]
        )

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """EIRP = Ptx(dBW) + G(dBi) in the given direction."""
        g = self.gain_toward_dbi(theta_deg, phi_deg, f_hz)
        return w_to_dbw(tx_power_w) + g
