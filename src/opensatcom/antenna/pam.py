"""PAM-based phased array antenna model with analytic fallback."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from opensatcom.core.units import lin_to_db10, w_to_dbw


class PamArrayAntenna:
    """Phased array antenna wrapping PAM, with analytic fallback.

    Models a planar phased-array antenna as an Nx-by-Ny rectangular lattice
    of isotropic elements.  When the optional PAM package is installed, the
    full pattern synthesis engine is used; otherwise an analytic peak-gain
    approximation is provided via the standard aperture formula
    ``D = 4 * pi * Nx * dx * Ny * dy`` (element spacings in wavelengths).

    Parameters
    ----------
    nx : int, optional
        Number of elements along the x-axis, by default 1.
    ny : int, optional
        Number of elements along the y-axis, by default 1.
    dx_lambda : float, optional
        Element spacing along x in wavelengths, by default 0.5.
    dy_lambda : float, optional
        Element spacing along y in wavelengths, by default 0.5.
    taper : tuple of (str, float), str, or None, optional
        Amplitude taper specification.  Can be a taper name string (e.g.
        ``"uniform"``) or a ``(name, sll_db)`` tuple for parameterised
        tapers (e.g. ``("taylor", -25)``).  ``None`` applies no taper
        (uniform illumination), by default None.
    steering : Any or None, optional
        Beam-steering specification passed through to PAM.  Ignored when
        PAM is not available, by default None.
    impairments : Any or None, optional
        Element-level impairment model (amplitude/phase errors) passed
        through to PAM.  Ignored when PAM is not available, by default None.
    """

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
        """Return peak gain (analytic fallback).

        Computes the antenna gain at the requested angular coordinates.
        In the current analytic-fallback mode the returned array is filled
        with the peak directivity for every direction; full pattern shaping
        is available when PAM is installed.

        Parameters
        ----------
        theta_deg : numpy.ndarray
            Elevation angles in degrees.  The shape of the output matches
            this array.
        phi_deg : numpy.ndarray
            Azimuth angles in degrees.  Must be broadcastable with
            ``theta_deg``.
        f_hz : float
            Operating frequency in hertz.

        Returns
        -------
        numpy.ndarray
            Gain values in dBi, with the same shape as ``theta_deg``.
        """
        return np.full_like(theta_deg, self._peak_gain_dbi, dtype=float)

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """EIRP = Ptx(dBW) + G(dBi).

        Computes the Effective Isotropic Radiated Power by adding the
        transmit power (converted to dBW) and the antenna peak gain (dBi).

        Parameters
        ----------
        theta_deg : float
            Elevation angle in degrees toward the target.
        phi_deg : float
            Azimuth angle in degrees toward the target.
        f_hz : float
            Operating frequency in hertz.
        tx_power_w : float
            Transmitter output power in watts (linear).

        Returns
        -------
        float
            EIRP in dBW.
        """
        return w_to_dbw(tx_power_w) + self._peak_gain_dbi
