"""Tests for CouplingAwareAntenna."""

from pathlib import Path

import numpy as np
import pytest

from opensatcom.antenna.coupling import CouplingAwareAntenna
from opensatcom.antenna.edgefem_loader import CouplingData, load_npz_artifact

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "synthetic_coupling.npz"


def _make_coupling_data() -> CouplingData:
    """Load the synthetic 4-element fixture."""
    return load_npz_artifact(FIXTURE_PATH)


class TestCouplingAwareAntenna:
    def test_construction(self) -> None:
        data = _make_coupling_data()
        ant = CouplingAwareAntenna(data)
        assert ant is not None

    def test_from_npz(self) -> None:
        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        assert ant is not None

    def test_gain_at_boresight_positive(self) -> None:
        """Gain at boresight should be positive (elements in phase)."""
        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        theta = np.array([0.0])
        phi = np.array([0.0])
        gain = ant.gain_dbi(theta, phi, 10e9)
        assert gain[0] > 0.0

    def test_gain_varies_with_direction(self) -> None:
        """Gain should vary with direction (not constant)."""
        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        theta = np.array([0.0, 30.0, 60.0])
        phi = np.array([0.0, 0.0, 0.0])
        gains = ant.gain_dbi(theta, phi, 10e9)
        # Not all values should be identical
        assert not np.allclose(gains[0], gains[2], atol=0.1)

    def test_peak_gain_near_boresight(self) -> None:
        """Peak gain should be near boresight for broadside steering."""
        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        # Check a few angles
        theta_vals = np.array([0.0, 10.0, 20.0, 40.0, 60.0])
        phi = np.zeros_like(theta_vals)
        gains = ant.gain_dbi(theta_vals, phi, 10e9)
        # Boresight gain should be among the highest
        assert gains[0] >= gains[-1]

    def test_coupling_reduces_gain(self) -> None:
        """Coupling correction should change gain vs uncoupled baseline."""
        data = _make_coupling_data()

        # With coupling
        ant_coupled = CouplingAwareAntenna(data)
        theta = np.array([0.0])
        phi = np.array([0.0])
        g_coupled = ant_coupled.gain_dbi(theta, phi, 10e9)[0]

        # Without coupling (identity coupling matrix = no coupling)
        data_no_coupling = CouplingData(
            coupling_matrix=np.zeros((4, 4), dtype=complex),
            element_patterns=data.element_patterns,
            theta_grid_deg=data.theta_grid_deg,
            phi_grid_deg=data.phi_grid_deg,
            freq_hz=data.freq_hz,
            array_positions_m=data.array_positions_m,
        )
        ant_uncoupled = CouplingAwareAntenna(data_no_coupling)
        g_uncoupled = ant_uncoupled.gain_dbi(theta, phi, 10e9)[0]

        # Gains should differ due to coupling correction
        assert g_coupled != pytest.approx(g_uncoupled, abs=0.01)

    def test_eirp_dbw(self) -> None:
        from opensatcom.core.units import w_to_dbw

        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        g = ant.gain_dbi(np.array([0.0]), np.array([0.0]), 10e9)[0]
        eirp = ant.eirp_dbw(0.0, 0.0, 10e9, 100.0)
        assert eirp == pytest.approx(w_to_dbw(100.0) + g, abs=0.01)

    def test_vectorized_output_shape(self) -> None:
        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        theta = np.array([0.0, 10.0, 20.0])
        phi = np.array([0.0, 5.0, 10.0])
        gains = ant.gain_dbi(theta, phi, 10e9)
        assert gains.shape == (3,)

    def test_steered_antenna(self) -> None:
        """Steering should shift the peak gain direction."""
        ant_broadside = CouplingAwareAntenna.from_npz(
            FIXTURE_PATH, steering_az_deg=0.0, steering_el_deg=0.0
        )
        ant_steered = CouplingAwareAntenna.from_npz(
            FIXTURE_PATH, steering_az_deg=20.0, steering_el_deg=0.0
        )

        # At 20 deg, steered antenna should have higher gain
        theta = np.array([20.0])
        phi = np.array([0.0])
        g_broadside = ant_broadside.gain_dbi(theta, phi, 10e9)[0]
        g_steered = ant_steered.gain_dbi(theta, phi, 10e9)[0]
        assert g_steered > g_broadside
