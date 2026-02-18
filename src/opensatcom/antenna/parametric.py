"""Parametric antenna with fixed gain."""

from __future__ import annotations

import numpy as np

from opensatcom.core.units import w_to_dbw


class ParametricAntenna:
    """Fixed-gain antenna model (e.g., parabolic dish or specified gain).

    Returns the same gain in all directions — useful for quick link budgets
    where the antenna pattern is not the focus.

    Parameters
    ----------
    gain_dbi : float
        Isotropic antenna gain in dBi (default 0.0).
    scan_loss_model : str
        Scan-loss model name (default ``"none"``).

    Examples
    --------
    >>> ant = ParametricAntenna(gain_dbi=36.0)
    >>> float(ant.gain_dbi(np.array([30.0]), np.array([0.0]), 12e9)[0])
    36.0
    """

    def __init__(self, gain_dbi: float = 0.0, scan_loss_model: str = "none") -> None:
        self._gain_dbi = gain_dbi
        self._scan_loss_model = scan_loss_model

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray:
        """Return fixed gain for all directions.

        Parameters
        ----------
        theta_deg : numpy.ndarray
            Elevation angles in degrees.
        phi_deg : numpy.ndarray
            Azimuth angles in degrees.
        f_hz : float
            Carrier frequency in Hz (unused).

        Returns
        -------
        numpy.ndarray
            Constant gain array in dBi, same shape as *theta_deg*.
        """
        return np.full_like(theta_deg, self._gain_dbi, dtype=float)

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """Compute EIRP in a given direction.

        Parameters
        ----------
        theta_deg : float
            Elevation angle in degrees.
        phi_deg : float
            Azimuth angle in degrees.
        f_hz : float
            Carrier frequency in Hz (unused).
        tx_power_w : float
            Transmit power in watts.

        Returns
        -------
        float
            EIRP in dBW (``Ptx_dBW + G_dBi``).
        """
        return w_to_dbw(tx_power_w) + self._gain_dbi
