"""Tests for antenna models."""

import numpy as np
import pytest

from opensatcom.antenna.pam import PamArrayAntenna
from opensatcom.antenna.parametric import ParametricAntenna


class TestParametricAntenna:
    def test_fixed_gain(self) -> None:
        ant = ParametricAntenna(gain_dbi=35.0)
        theta = np.array([0.0, 30.0, 60.0])
        phi = np.array([0.0, 0.0, 0.0])
        gains = ant.gain_dbi(theta, phi, 19.7e9)
        np.testing.assert_allclose(gains, 35.0)

    def test_eirp(self) -> None:
        ant = ParametricAntenna(gain_dbi=35.0)
        from opensatcom.core.units import w_to_dbw

        eirp = ant.eirp_dbw(0.0, 0.0, 19.7e9, 200.0)
        assert eirp == pytest.approx(w_to_dbw(200.0) + 35.0)

    def test_default_gain_is_zero(self) -> None:
        ant = ParametricAntenna()
        theta = np.array([0.0])
        phi = np.array([0.0])
        gains = ant.gain_dbi(theta, phi, 1e9)
        assert gains[0] == pytest.approx(0.0)


class TestPamArrayAntenna:
    def test_positive_gain(self) -> None:
        ant = PamArrayAntenna(nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5)
        theta = np.array([0.0])
        phi = np.array([0.0])
        gains = ant.gain_dbi(theta, phi, 19.7e9)
        assert gains[0] > 0.0

    def test_gain_scales_with_aperture(self) -> None:
        small = PamArrayAntenna(nx=4, ny=4, dx_lambda=0.5, dy_lambda=0.5)
        large = PamArrayAntenna(nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5)
        theta = np.array([0.0])
        phi = np.array([0.0])
        g_small = small.gain_dbi(theta, phi, 19.7e9)[0]
        g_large = large.gain_dbi(theta, phi, 19.7e9)[0]
        # 16x16 vs 4x4 → 16x more area → ~12 dB more gain
        assert g_large - g_small == pytest.approx(12.04, rel=1e-2)

    def test_16x16_known_gain(self) -> None:
        # D = 4*pi*16*0.5*16*0.5 = 4*pi*64 ≈ 804.2 → ~29.05 dBi
        import math

        ant = PamArrayAntenna(nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5)
        expected_dbi = 10.0 * math.log10(4.0 * math.pi * 64.0)
        theta = np.array([0.0])
        phi = np.array([0.0])
        assert ant.gain_dbi(theta, phi, 19.7e9)[0] == pytest.approx(expected_dbi, rel=1e-6)
