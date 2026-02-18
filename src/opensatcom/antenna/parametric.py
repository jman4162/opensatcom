"""Parametric antenna with fixed gain."""

from __future__ import annotations

import numpy as np

from opensatcom.core.units import w_to_dbw


class ParametricAntenna:
    """Fixed-gain antenna model (e.g., parabolic dish or specified gain)."""

    def __init__(self, gain_dbi: float = 0.0, scan_loss_model: str = "none") -> None:
        self._gain_dbi = gain_dbi
        self._scan_loss_model = scan_loss_model

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray:
        """Return fixed gain for all directions."""
        return np.full_like(theta_deg, self._gain_dbi, dtype=float)

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """EIRP = Ptx(dBW) + G(dBi)."""
        return w_to_dbw(tx_power_w) + self._gain_dbi
