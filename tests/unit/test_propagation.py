"""Tests for propagation models."""

import math

import pytest

from opensatcom.core.constants import SPEED_OF_LIGHT_MPS
from opensatcom.core.models import PropagationConditions
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation


class TestFreeSpacePropagation:
    def test_fspl_at_19_7ghz_1200km(self) -> None:
        """FSPL at 19.7 GHz / 1200 km — hand calculation."""
        f_hz = 19.7e9
        range_m = 1200e3
        expected = 20.0 * math.log10(4.0 * math.pi * range_m * f_hz / SPEED_OF_LIGHT_MPS)
        fspl = FreeSpacePropagation()
        cond = PropagationConditions()
        result = fspl.total_path_loss_db(f_hz, 30.0, range_m, cond)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_fspl_positive(self) -> None:
        fspl = FreeSpacePropagation()
        cond = PropagationConditions()
        loss = fspl.total_path_loss_db(12e9, 45.0, 550e3, cond)
        assert loss > 0.0

    def test_fspl_increases_with_range(self) -> None:
        fspl = FreeSpacePropagation()
        cond = PropagationConditions()
        loss_near = fspl.total_path_loss_db(12e9, 90.0, 500e3, cond)
        loss_far = fspl.total_path_loss_db(12e9, 10.0, 2000e3, cond)
        assert loss_far > loss_near


class TestCompositePropagation:
    def test_single_component_equals_fspl(self) -> None:
        fspl = FreeSpacePropagation()
        comp = CompositePropagation([fspl])
        cond = PropagationConditions()
        f_hz, elev, rng = 19.7e9, 30.0, 1200e3
        assert comp.total_path_loss_db(f_hz, elev, rng, cond) == pytest.approx(
            fspl.total_path_loss_db(f_hz, elev, rng, cond), rel=1e-10
        )

    def test_empty_composite_is_zero(self) -> None:
        comp = CompositePropagation([])
        cond = PropagationConditions()
        assert comp.total_path_loss_db(19.7e9, 30.0, 1200e3, cond) == pytest.approx(0.0)
