"""Golden tests for EdgeFEM coupling-aware antenna — frozen reference values."""

from pathlib import Path

import numpy as np
import pytest

from opensatcom.antenna.coupling import CouplingAwareAntenna

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "synthetic_coupling.npz"


class TestCouplingGolden:
    def test_boresight_gain_frozen(self) -> None:
        """Frozen boresight gain for 4-element synthetic array at 10 GHz."""
        ant = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        gain = ant.gain_dbi(np.array([0.0]), np.array([0.0]), 10e9)
        # 4-element array with coupling should produce ~6 dBi boresight gain
        assert gain[0] == pytest.approx(6.0, abs=2.0)

    def test_steered_gain_shift(self) -> None:
        """Steered array gain at steer direction should exceed broadside at same angle."""
        ant_broadside = CouplingAwareAntenna.from_npz(FIXTURE_PATH)
        ant_steered = CouplingAwareAntenna.from_npz(
            FIXTURE_PATH, steering_az_deg=20.0, steering_el_deg=0.0
        )
        theta = np.array([20.0])
        phi = np.array([0.0])
        g_broad = ant_broadside.gain_dbi(theta, phi, 10e9)[0]
        g_steer = ant_steered.gain_dbi(theta, phi, 10e9)[0]
        assert g_steer > g_broad
