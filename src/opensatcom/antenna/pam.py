"""PAM-based phased array antenna model with analytic fallback."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from opensatcom.core.units import lin_to_db10, w_to_dbw


class PamArrayAntenna:
    """Phased array antenna wrapping PAM, with analytic fallback."""

    def __init__(
        self,
        nx: int = 1,
        ny: int = 1,
        dx_lambda: float = 0.5,
        dy_lambda: float = 0.5,
        taper: tuple[str, float] | str | None = None,
        steering: Any | None = None,
        impairments: Any | None = None,
    ) -> None:
        self.nx = nx
        self.ny = ny
        self.dx_lambda = dx_lambda
        self.dy_lambda = dy_lambda
        self.taper = taper
        self.steering = steering
        self.impairments = impairments

        self._pam_available = False
        try:
            import pam  # noqa: F401

            self._pam_available = True
        except ImportError:
            pass

        # Compute analytic peak gain: D = 4*pi*Nx*dx*Ny*dy (in wavelengths^2)
        aperture_lambda_sq = nx * dx_lambda * ny * dy_lambda
        self._peak_gain_lin = 4.0 * math.pi * aperture_lambda_sq
        self._peak_gain_dbi = lin_to_db10(self._peak_gain_lin)

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray:
        """Return peak gain (analytic fallback)."""
        return np.full_like(theta_deg, self._peak_gain_dbi, dtype=float)

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """EIRP = Ptx(dBW) + G(dBi)."""
        return w_to_dbw(tx_power_w) + self._peak_gain_dbi
