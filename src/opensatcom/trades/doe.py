"""Design of Experiments sampling for trade studies."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd


class DesignOfExperiments:
    """Generate parameter combinations for trade study evaluation.

    Supports Latin Hypercube Sampling (LHS), full factorial, and random sampling.

    Parameters
    ----------
    parameter_space : dict[str, tuple[float, float]]
        Parameter names mapped to (min, max) ranges.
    """

    def __init__(self, parameter_space: dict[str, tuple[float, float]]) -> None:
        self.parameter_space = parameter_space
        self._names = list(parameter_space.keys())
        self._bounds = [parameter_space[n] for n in self._names]

    def generate(self, n_samples: int, method: str = "lhs", seed: int = 42) -> pd.DataFrame:
        """Generate parameter combinations.

        Parameters
        ----------
        n_samples : int
            Number of design points.
        method : str
            Sampling method: "lhs", "random", or "full_factorial".
        seed : int
            Random seed for reproducibility.
        """
        if method == "lhs":
            return self.lhs(n_samples, seed=seed)
        elif method == "random":
            return self.random(n_samples, seed=seed)
        elif method == "full_factorial":
            return self.full_factorial(n_samples)
        else:
            raise ValueError(f"Unknown sampling method: {method}")

    def lhs(self, n_samples: int, seed: int = 42) -> pd.DataFrame:
        """Latin Hypercube Sampling using scipy."""
        from scipy.stats.qmc import LatinHypercube

        d = len(self._names)
        sampler = LatinHypercube(d=d, seed=seed)
        unit_samples = sampler.random(n=n_samples)

        # Scale to parameter bounds
        data = np.zeros_like(unit_samples)
        for j, (lo, hi) in enumerate(self._bounds):
            data[:, j] = lo + unit_samples[:, j] * (hi - lo)

        return pd.DataFrame(data, columns=self._names)

    def random(self, n_samples: int, seed: int = 42) -> pd.DataFrame:
        """Uniform random sampling."""
        rng = np.random.default_rng(seed)
        d = len(self._names)
        unit_samples = rng.random((n_samples, d))

        data = np.zeros_like(unit_samples)
        for j, (lo, hi) in enumerate(self._bounds):
            data[:, j] = lo + unit_samples[:, j] * (hi - lo)

        return pd.DataFrame(data, columns=self._names)

    def full_factorial(self, levels_per_param: int) -> pd.DataFrame:
        """Full factorial design with equal levels per parameter."""
        grids = []
        for lo, hi in self._bounds:
            grids.append(np.linspace(lo, hi, levels_per_param))

        combos = list(itertools.product(*grids))
        return pd.DataFrame(combos, columns=self._names)
