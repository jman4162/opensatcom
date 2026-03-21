"""Tests for Sobol sensitivity analysis."""

import numpy as np
import pytest

from opensatcom.trades.sensitivity import (
    SobolResult,
    compute_sobol_indices,
    generate_saltelli_samples,
)


def _salib_available() -> bool:
    try:
        import SALib  # noqa: F401
        return True
    except ImportError:
        return False


class TestSobolResult:
    """Tests for the SobolResult dataclass."""

    def test_creation(self) -> None:
        result = SobolResult(
            param_names=["a", "b"],
            S1=np.array([0.5, 0.3]),
            ST=np.array([0.6, 0.4]),
            S1_conf=np.array([0.05, 0.04]),
            ST_conf=np.array([0.06, 0.05]),
        )
        assert result.param_names == ["a", "b"]
        assert len(result.S1) == 2


@pytest.mark.skipif(
    not _salib_available(),
    reason="SALib not installed",
)
class TestSaltelliSampling:
    """Tests for Saltelli sample generation."""

    def test_sample_shape(self) -> None:
        space = {"x": (0.0, 1.0), "y": (0.0, 10.0)}
        df = generate_saltelli_samples(space, n=64)
        # Saltelli with calc_second_order=False: N * (D + 2) = 64 * (2 + 2) = 256
        assert len(df) == 64 * (2 + 2)
        assert list(df.columns) == ["x", "y"]

    def test_bounds_respected(self) -> None:
        space = {"a": (5.0, 10.0), "b": (-1.0, 1.0)}
        df = generate_saltelli_samples(space, n=32)
        assert df["a"].min() >= 5.0
        assert df["a"].max() <= 10.0
        assert df["b"].min() >= -1.0
        assert df["b"].max() <= 1.0


@pytest.mark.skipif(
    not _salib_available(),
    reason="SALib not installed",
)
class TestSobolAnalysis:
    """Tests for Sobol index computation."""

    def test_linear_model_sensitivity(self) -> None:
        # y = 3*x1 + x2 → x1 should dominate
        space = {"x1": (0.0, 1.0), "x2": (0.0, 1.0)}
        n = 512
        df = generate_saltelli_samples(space, n=n)
        y = 3.0 * df["x1"].values + df["x2"].values

        result = compute_sobol_indices(space, y, n=n)

        assert result.param_names == ["x1", "x2"]
        # x1 should have higher S1 than x2
        assert result.S1[0] > result.S1[1]
        # Total should be >= first-order (with tolerance for numerical noise)
        assert np.all(result.ST >= result.S1 - 0.1)
