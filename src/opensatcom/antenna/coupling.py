"""Coupling-aware antenna model using EdgeFEM artifacts."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from opensatcom.antenna.edgefem_loader import CouplingData, load_npz_artifact
from opensatcom.core.units import lin_to_db10, w_to_dbw


class CouplingAwareAntenna:
    """Antenna model using EdgeFEM coupling data for direction-dependent gain.

    Computes array gain using embedded element patterns corrected for
    mutual coupling. The gain at each direction accounts for:
    1. Active element patterns (from EdgeFEM simulation)
    2. Coupling correction via S-parameter matrix
    3. Array factor with element positions and steering weights

    Parameters
    ----------
    coupling_data : CouplingData
        Coupling data loaded from an EdgeFEM artifact.
    steering_az_deg : float
        Beam steering azimuth in degrees (default 0.0).
    steering_el_deg : float
        Beam steering elevation in degrees (default 0.0).
    """

    def __init__(
        self,
        coupling_data: CouplingData,
        steering_az_deg: float = 0.0,
        steering_el_deg: float = 0.0,
    ) -> None:
        self._data = coupling_data
        self._steering_az = steering_az_deg
        self._steering_el = steering_el_deg

        # Precompute coupling correction matrix: (I + S)^-1
        n = coupling_data.n_elements
        identity = np.eye(n, dtype=complex)
        self._coupling_correction = np.linalg.inv(
            identity + coupling_data.coupling_matrix
        )

        # Precompute steering weights
        self._weights = self._compute_steering_weights()

    def _compute_steering_weights(self) -> np.ndarray:
        """Compute uniform steering weights toward (steering_az, steering_el)."""
        positions = self._data.array_positions_m
        n_elem = self._data.n_elements

        # Compute wavenumber from frequency
        if isinstance(self._data.freq_hz, np.ndarray):
            freq = float(self._data.freq_hz[0])
        else:
            freq = float(self._data.freq_hz)

        from opensatcom.core.constants import SPEED_OF_LIGHT_MPS

        wavelength = SPEED_OF_LIGHT_MPS / freq
        k = 2.0 * np.pi / wavelength

        # Direction cosines for steering direction
        az_rad = np.radians(self._steering_az)
        el_rad = np.radians(self._steering_el)
        u0 = np.cos(el_rad) * np.sin(az_rad)
        v0 = np.sin(el_rad)

        # Phase weights for uniform steering
        if positions.shape[1] >= 2:
            phase = k * (positions[:, 0] * u0 + positions[:, 1] * v0)
        else:
            phase = k * positions[:, 0] * u0

        weights: np.ndarray = np.exp(-1j * phase) / np.sqrt(n_elem)
        return weights

    def _evaluate_array_gain(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray
    ) -> np.ndarray:
        """Compute array gain (linear) for given directions.

        Parameters
        ----------
        theta_deg : numpy.ndarray
            Azimuth angles in degrees, shape ``(N,)``.
        phi_deg : numpy.ndarray
            Elevation angles in degrees, shape ``(N,)``.

        Returns
        -------
        numpy.ndarray
            Linear gain values, shape ``(N,)``.
        """
        data = self._data
        n_dir = len(theta_deg)
        n_elem = data.n_elements

        # Interpolate element patterns to requested directions
        # element_patterns shape: (N_elem, N_theta, N_phi)
        from scipy.interpolate import RegularGridInterpolator

        gains = np.zeros(n_dir)

        for d in range(n_dir):
            # Evaluate each element's pattern at this direction
            elem_response = np.zeros(n_elem, dtype=complex)
            for e in range(n_elem):
                pattern = data.element_patterns[e]
                # Use nearest-neighbor interpolation for robustness
                interp = RegularGridInterpolator(
                    (data.theta_grid_deg, data.phi_grid_deg),
                    pattern,
                    method="nearest",
                    bounds_error=False,
                    fill_value=0.0,
                )
                elem_response[e] = interp(
                    np.array([[float(theta_deg[d]), float(phi_deg[d])]])
                )[0]

            # Apply coupling correction
            corrected = self._coupling_correction @ elem_response

            # Array factor with steering weights
            if isinstance(data.freq_hz, np.ndarray):
                freq = float(data.freq_hz[0])
            else:
                freq = float(data.freq_hz)

            from opensatcom.core.constants import SPEED_OF_LIGHT_MPS

            wavelength = SPEED_OF_LIGHT_MPS / freq
            k = 2.0 * np.pi / wavelength
            positions = data.array_positions_m

            az_rad = np.radians(float(theta_deg[d]))
            el_rad = np.radians(float(phi_deg[d]))
            u = np.cos(el_rad) * np.sin(az_rad)
            v = np.sin(el_rad)

            if positions.shape[1] >= 2:
                phase = k * (positions[:, 0] * u + positions[:, 1] * v)
            else:
                phase = k * positions[:, 0] * u

            array_factor = np.exp(1j * phase)

            # Total response: sum of weighted, corrected element contributions
            total = np.sum(self._weights * corrected * array_factor)
            gains[d] = np.abs(total) ** 2

        return gains

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray:
        """Return gain in dBi accounting for coupling effects.

        Parameters
        ----------
        theta_deg : numpy.ndarray
            Azimuth angles in degrees.
        phi_deg : numpy.ndarray
            Elevation angles in degrees.
        f_hz : float
            Carrier frequency in Hz (for reference; pattern data at nearest freq).

        Returns
        -------
        numpy.ndarray
            Gain values in dBi, same shape as *theta_deg*.
        """
        gain_lin = self._evaluate_array_gain(theta_deg, phi_deg)
        # Normalize to directivity: 4*pi * gain / (sum over sphere)
        # For simplicity, use the raw array gain with element patterns
        # that are already calibrated in dBi-equivalent units
        safe_gain = np.maximum(gain_lin, 1e-20)
        return np.array([lin_to_db10(g) for g in safe_gain])

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """Compute EIRP in a given direction.

        Parameters
        ----------
        theta_deg : float
            Azimuth angle in degrees.
        phi_deg : float
            Elevation angle in degrees.
        f_hz : float
            Carrier frequency in Hz.
        tx_power_w : float
            Transmit power in watts.

        Returns
        -------
        float
            EIRP in dBW.
        """
        g = self.gain_dbi(np.array([theta_deg]), np.array([phi_deg]), f_hz)
        return w_to_dbw(tx_power_w) + float(g[0])

    @classmethod
    def from_npz(
        cls,
        artifact_path: str | Path,
        steering_az_deg: float = 0.0,
        steering_el_deg: float = 0.0,
    ) -> CouplingAwareAntenna:
        """Load coupling data from .npz and construct antenna.

        Parameters
        ----------
        artifact_path : str or Path
            Path to the ``.npz`` file containing EdgeFEM coupling data.
        steering_az_deg : float
            Beam steering azimuth in degrees (default 0.0).
        steering_el_deg : float
            Beam steering elevation in degrees (default 0.0).

        Returns
        -------
        CouplingAwareAntenna
            Constructed antenna with loaded coupling data.
        """
        data = load_npz_artifact(artifact_path)
        return cls(data, steering_az_deg, steering_el_deg)
