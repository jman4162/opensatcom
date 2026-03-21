"""Tests for Doppler shift computation."""

import pytest

from opensatcom.core.constants import SPEED_OF_LIGHT_MPS
from opensatcom.geometry.doppler import doppler_shift_hz


class TestDopplerShift:
    """Tests for doppler_shift_hz."""

    def test_zero_velocity(self) -> None:
        assert doppler_shift_hz(12e9, 0.0) == 0.0

    def test_approaching_positive_shift(self) -> None:
        # Satellite approaching → negative v_radial → positive Doppler shift
        f_hz = 12e9
        v_radial = -7000.0  # approaching at 7 km/s
        shift = doppler_shift_hz(f_hz, v_radial)
        assert shift > 0
        expected = f_hz * 7000.0 / SPEED_OF_LIGHT_MPS
        assert shift == pytest.approx(expected)

    def test_receding_negative_shift(self) -> None:
        # Satellite receding → positive v_radial → negative Doppler shift
        f_hz = 12e9
        v_radial = 7000.0
        shift = doppler_shift_hz(f_hz, v_radial)
        assert shift < 0

    def test_ku_band_leo_magnitude(self) -> None:
        # At Ku-band (20 GHz) with LEO radial velocity ~7 km/s
        # Expected: ~467 kHz
        f_hz = 20e9
        v_radial = -7000.0
        shift = doppler_shift_hz(f_hz, v_radial)
        assert abs(shift) == pytest.approx(467e3, rel=0.01)

    def test_symmetry(self) -> None:
        f = 10e9
        v = 5000.0
        assert doppler_shift_hz(f, v) == pytest.approx(-doppler_shift_hz(f, -v))

    def test_linearity_in_frequency(self) -> None:
        v = 1000.0
        shift_1 = doppler_shift_hz(10e9, v)
        shift_2 = doppler_shift_hz(20e9, v)
        assert shift_2 == pytest.approx(2 * shift_1)
