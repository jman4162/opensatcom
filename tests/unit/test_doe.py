"""Tests for Design of Experiments module."""

import pytest

from opensatcom.trades.doe import DesignOfExperiments
from opensatcom.trades.requirements import RequirementsTemplate


class TestDesignOfExperiments:
    def setup_method(self) -> None:
        self.space = {
            "freq_hz": (10e9, 30e9),
            "tx_power_w": (10.0, 200.0),
        }
        self.doe = DesignOfExperiments(self.space)

    def test_lhs_shape(self) -> None:
        df = self.doe.lhs(50, seed=42)
        assert df.shape == (50, 2)
        assert list(df.columns) == ["freq_hz", "tx_power_w"]

    def test_lhs_within_bounds(self) -> None:
        df = self.doe.lhs(100, seed=42)
        assert df["freq_hz"].min() >= 10e9
        assert df["freq_hz"].max() <= 30e9
        assert df["tx_power_w"].min() >= 10.0
        assert df["tx_power_w"].max() <= 200.0

    def test_random_shape(self) -> None:
        df = self.doe.random(30, seed=42)
        assert df.shape == (30, 2)

    def test_full_factorial(self) -> None:
        df = self.doe.full_factorial(5)
        assert len(df) == 25  # 5^2

    def test_generate_dispatch(self) -> None:
        df = self.doe.generate(50, method="lhs", seed=42)
        assert len(df) == 50

    def test_generate_unknown_method(self) -> None:
        with pytest.raises(ValueError, match="Unknown"):
            self.doe.generate(10, method="bogus")


class TestRequirementsTemplate:
    def test_add_and_space(self) -> None:
        rt = RequirementsTemplate()
        rt.add("freq_hz", 10e9, 30e9)
        rt.add("tx_power_w", 10.0, 200.0)
        space = rt.to_parameter_space()
        assert len(space) == 2
        assert space["freq_hz"] == (10e9, 30e9)

    def test_invalid_range(self) -> None:
        rt = RequirementsTemplate()
        with pytest.raises(ValueError, match="lo"):
            rt.add("x", 100.0, 10.0)

    def test_names(self) -> None:
        rt = RequirementsTemplate()
        rt.add("a", 0.0, 1.0)
        rt.add("b", 0.0, 1.0)
        assert rt.names == ["a", "b"]
        assert rt.n_params == 2
