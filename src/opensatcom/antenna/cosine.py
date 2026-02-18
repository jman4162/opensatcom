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

    Parameters
    ----------
    peak_gain_dbi : float
        Peak (boresight) antenna gain in dBi.
    theta_3db_deg : float
        Half-power (3 dB) beamwidth in degrees.
    sidelobe_floor_dbi : float, optional
        Minimum gain floor representing the sidelobe level, in dBi.
        Default is -20.0.
    boresight_az_deg : float, optional
        Azimuth angle of the boresight direction in degrees.
        Default is 0.0.
    boresight_el_deg : float, optional
        Elevation angle of the boresight direction in degrees.
        Default is 0.0.

    Examples
    --------
    >>> ant = CosineRolloffAntenna(peak_gain_dbi=36.0, theta_3db_deg=1.5)
    >>> ant.gain_toward_dbi(az_deg=0.0, el_deg=0.0, f_hz=12e9)
    36.0
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
        """Peak (boresight) antenna gain.

        Returns
        -------
        float
            Peak gain in dBi.
        """
        return self._peak_gain_dbi

    @property
    def theta_3db_deg(self) -> float:
        """Half-power (3 dB) beamwidth.

        Returns
        -------
        float
            Beamwidth in degrees.
        """
        return self._theta_3db_deg

    @property
    def sidelobe_floor_dbi(self) -> float:
        """Minimum gain floor representing the sidelobe level.

        Returns
        -------
        float
            Sidelobe floor in dBi.
        """
        return self._sidelobe_floor_dbi

    @property
    def boresight_az_deg(self) -> float:
        """Azimuth angle of the boresight direction.

        Returns
        -------
        float
            Boresight azimuth in degrees.
        """
        return self._boresight_az_deg

    @property
    def boresight_el_deg(self) -> float:
        """Elevation angle of the boresight direction.

        Returns
        -------
        float
            Boresight elevation in degrees.
        """
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
        theta_deg : numpy.ndarray
            Azimuth angles in degrees.
        phi_deg : numpy.ndarray
            Elevation angles in degrees.
        f_hz : float
            Frequency in Hz. Unused in this analytic model but accepted
            for interface compatibility with ``AntennaModel``.

        Returns
        -------
        numpy.ndarray
            Gain values in dBi, clamped to the sidelobe floor.
        """
        off_axis = self._off_axis_angle_deg(theta_deg, phi_deg)
        # Main lobe: parabolic rolloff  gain = peak - 12*(theta/theta_3db)^2
        gain = self._peak_gain_dbi - 12.0 * (off_axis / self._theta_3db_deg) ** 2
        # Clamp to sidelobe floor (applies both in main lobe tail and beyond)
        gain = np.maximum(gain, self._sidelobe_floor_dbi)
        return gain

    def gain_toward_dbi(self, az_deg: float, el_deg: float, f_hz: float) -> float:
        """Scalar convenience: gain in a specific direction.

        Parameters
        ----------
        az_deg : float
            Azimuth angle in degrees toward which to evaluate the gain.
        el_deg : float
            Elevation angle in degrees toward which to evaluate the gain.
        f_hz : float
            Frequency in Hz. Unused in this analytic model but accepted
            for interface compatibility with ``AntennaModel``.

        Returns
        -------
        float
            Antenna gain in the specified direction, in dBi.
        """
        return float(
            self.gain_dbi(np.array([az_deg]), np.array([el_deg]), f_hz)[0]
        )

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """Compute EIRP in a given direction.

        EIRP is calculated as ``Ptx(dBW) + G(dBi)`` where the gain is
        evaluated at the specified azimuth/elevation angles.

        Parameters
        ----------
        theta_deg : float
            Azimuth angle in degrees toward which to evaluate the EIRP.
        phi_deg : float
            Elevation angle in degrees toward which to evaluate the EIRP.
        f_hz : float
            Frequency in Hz. Passed through to :meth:`gain_toward_dbi`.
        tx_power_w : float
            Transmit power in Watts.

        Returns
        -------
        float
            Effective isotropic radiated power in dBW.
        """
        g = self.gain_toward_dbi(theta_deg, phi_deg, f_hz)
        return w_to_dbw(tx_power_w) + g
