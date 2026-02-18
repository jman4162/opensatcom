"""Tests for CosineRolloffAntenna."""

import numpy as np
import pytest

from opensatcom.antenna.cosine import CosineRolloffAntenna


class TestCosineRolloffAntenna:
    def test_peak_gain_at_boresight(self) -> None:
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        theta = np.array([0.0])
        phi = np.array([0.0])
        gain = ant.gain_dbi(theta, phi, 19.7e9)
        assert gain[0] == pytest.approx(35.0)

    def test_3db_point(self) -> None:
        """At theta_3db off-axis, gain should be 3 dB below peak (parabolic formula)."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        # Off-axis by exactly theta_3db in azimuth
        theta = np.array([2.0])
        phi = np.array([0.0])
        gain = ant.gain_dbi(theta, phi, 19.7e9)
        # gain = 35 - 12*(2/2)^2 = 35 - 12 = 23
        assert gain[0] == pytest.approx(23.0)

    def test_half_power_beamwidth(self) -> None:
        """At half the 3dB beamwidth, gain drops by 3 dB."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        # Off-axis angle where gain = peak - 3 dB:
        # 35 - 12*(theta/2)^2 = 32  =>  theta = 2*sqrt(3/12) = 1.0
        theta = np.array([1.0])
        phi = np.array([0.0])
        gain = ant.gain_dbi(theta, phi, 19.7e9)
        assert gain[0] == pytest.approx(32.0)

    def test_sidelobe_floor(self) -> None:
        """Beyond 2.6 * theta_3db, gain clamps to sidelobe floor."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            sidelobe_floor_dbi=-20.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        # Way off-axis
        theta = np.array([10.0])
        phi = np.array([0.0])
        gain = ant.gain_dbi(theta, phi, 19.7e9)
        assert gain[0] == pytest.approx(-20.0)

    def test_sidelobe_clamp(self) -> None:
        """Gain never drops below sidelobe floor, even in main lobe tail."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            sidelobe_floor_dbi=-20.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        # Close to boresight: above floor
        theta = np.array([2.5])
        phi = np.array([0.0])
        gains = ant.gain_dbi(theta, phi, 19.7e9)
        assert gains[0] > -20.0
        assert gains[0] < 35.0
        # Far off-axis: clamped to floor
        theta = np.array([10.0])
        gains = ant.gain_dbi(theta, phi, 19.7e9)
        assert gains[0] == pytest.approx(-20.0)

    def test_nonzero_boresight(self) -> None:
        """Antenna with boresight pointing at (5, 3): peak gain at that direction."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=5.0, boresight_el_deg=3.0,
        )
        theta = np.array([5.0])
        phi = np.array([3.0])
        gain = ant.gain_dbi(theta, phi, 19.7e9)
        assert gain[0] == pytest.approx(35.0)

    def test_gain_toward_dbi_scalar(self) -> None:
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
        )
        assert ant.gain_toward_dbi(0.0, 0.0, 19.7e9) == pytest.approx(35.0)

    def test_eirp_dbw(self) -> None:
        from opensatcom.core.units import w_to_dbw

        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
        )
        eirp = ant.eirp_dbw(0.0, 0.0, 19.7e9, 100.0)
        assert eirp == pytest.approx(w_to_dbw(100.0) + 35.0)

    def test_vectorized(self) -> None:
        """gain_dbi accepts arrays and returns correct shapes."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
        )
        theta = np.array([0.0, 1.0, 3.0, 10.0])
        phi = np.zeros(4)
        gains = ant.gain_dbi(theta, phi, 19.7e9)
        assert gains.shape == (4,)
        # Peak at boresight, decreasing off-axis
        assert gains[0] > gains[1] > gains[2]
