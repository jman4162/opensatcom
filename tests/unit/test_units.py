"""Tests for core unit conversion utilities."""

import math

import pytest

from opensatcom.core.units import (
    db10_to_lin,
    db20_to_lin,
    dbw_to_w,
    lin_to_db10,
    lin_to_db20,
    w_to_dbw,
)


class TestDb10:
    def test_roundtrip(self) -> None:
        for val in [0.001, 0.5, 1.0, 2.0, 100.0, 1e6]:
            assert db10_to_lin(lin_to_db10(val)) == pytest.approx(val, rel=1e-12)

    def test_known_values(self) -> None:
        assert lin_to_db10(1.0) == pytest.approx(0.0)
        assert lin_to_db10(10.0) == pytest.approx(10.0)
        assert lin_to_db10(100.0) == pytest.approx(20.0)
        assert lin_to_db10(0.5) == pytest.approx(-3.0103, rel=1e-3)

    def test_inverse(self) -> None:
        assert db10_to_lin(0.0) == pytest.approx(1.0)
        assert db10_to_lin(10.0) == pytest.approx(10.0)
        assert db10_to_lin(20.0) == pytest.approx(100.0)
        assert db10_to_lin(-3.0) == pytest.approx(0.5012, rel=1e-3)


class TestDb20:
    def test_roundtrip(self) -> None:
        for val in [0.001, 0.5, 1.0, 2.0, 100.0]:
            assert db20_to_lin(lin_to_db20(val)) == pytest.approx(val, rel=1e-12)

    def test_known_values(self) -> None:
        assert lin_to_db20(1.0) == pytest.approx(0.0)
        assert lin_to_db20(10.0) == pytest.approx(20.0)
        assert lin_to_db20(0.5) == pytest.approx(-6.0206, rel=1e-3)

    def test_inverse(self) -> None:
        assert db20_to_lin(0.0) == pytest.approx(1.0)
        assert db20_to_lin(20.0) == pytest.approx(10.0)


class TestDbw:
    def test_roundtrip(self) -> None:
        for val in [0.001, 1.0, 10.0, 200.0, 1000.0]:
            assert dbw_to_w(w_to_dbw(val)) == pytest.approx(val, rel=1e-12)

    def test_known_values(self) -> None:
        assert w_to_dbw(1.0) == pytest.approx(0.0)
        assert w_to_dbw(1000.0) == pytest.approx(30.0)
        assert w_to_dbw(200.0) == pytest.approx(10.0 * math.log10(200.0))

    def test_inverse(self) -> None:
        assert dbw_to_w(0.0) == pytest.approx(1.0)
        assert dbw_to_w(30.0) == pytest.approx(1000.0)
