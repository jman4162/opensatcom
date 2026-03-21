"""Sobol sensitivity analysis for trade studies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class SobolResult:
    """Results of a Sobol sensitivity analysis.

    Parameters
    ----------
    param_names : list of str
        Names of the input parameters.
    S1 : numpy.ndarray
        First-order Sobol indices (direct effect of each parameter).
    ST : numpy.ndarray
        Total-order Sobol indices (direct + interaction effects).
    S1_conf : numpy.ndarray
        Confidence intervals for first-order indices.
    ST_conf : numpy.ndarray
        Confidence intervals for total-order indices.
    """

    param_names: list[str]
    S1: np.ndarray
    ST: np.ndarray
    S1_conf: np.ndarray
    ST_conf: np.ndarray


def generate_saltelli_samples(
    param_space: dict[str, tuple[float, float]],
    n: int = 1024,
) -> pd.DataFrame:
    """Generate Saltelli samples for Sobol analysis.

    Uses SALib's Saltelli sampling scheme, which generates
    ``N * (2D + 2)`` samples for ``D`` parameters.

    Parameters
    ----------
    param_space : dict of str to (float, float)
        Mapping from parameter name to ``(min, max)`` bounds.
    n : int
        Base sample size (default 1024). Total samples will be
        ``n * (2 * n_params + 2)``.

    Returns
    -------
    pd.DataFrame
        DataFrame with one column per parameter, containing the
        Saltelli sample points.

    Raises
    ------
    ImportError
        If SALib is not installed.
    """
    try:
        from SALib.sample import saltelli
    except ImportError:
        raise ImportError(
            "SALib package required for sensitivity analysis. "
            "Install with: pip install 'opensatcom[sensitivity]'"
        )

    names = list(param_space.keys())
    bounds = [list(param_space[k]) for k in names]

    problem: dict[str, Any] = {
        "num_vars": len(names),
        "names": names,
        "bounds": bounds,
    }

    samples = saltelli.sample(problem, n, calc_second_order=False)
    return pd.DataFrame(samples, columns=names)


def compute_sobol_indices(
    param_space: dict[str, tuple[float, float]],
    results: np.ndarray,
    n: int = 1024,
) -> SobolResult:
    """Compute Sobol sensitivity indices from evaluation results.

    Parameters
    ----------
    param_space : dict of str to (float, float)
        Same parameter space used to generate samples.
    results : numpy.ndarray
        Output values corresponding to each Saltelli sample, shape ``(N_total,)``.
    n : int
        Base sample size used in ``generate_saltelli_samples``.

    Returns
    -------
    SobolResult
        First-order and total-order Sobol indices with confidence intervals.

    Raises
    ------
    ImportError
        If SALib is not installed.
    """
    try:
        from SALib.analyze import sobol
    except ImportError:
        raise ImportError(
            "SALib package required for sensitivity analysis. "
            "Install with: pip install 'opensatcom[sensitivity]'"
        )

    names = list(param_space.keys())
    bounds = [list(param_space[k]) for k in names]

    problem: dict[str, Any] = {
        "num_vars": len(names),
        "names": names,
        "bounds": bounds,
    }

    si = sobol.analyze(problem, results, calc_second_order=False, print_to_console=False)

    return SobolResult(
        param_names=names,
        S1=np.array(si["S1"]),
        ST=np.array(si["ST"]),
        S1_conf=np.array(si["S1_conf"]),
        ST_conf=np.array(si["ST_conf"]),
    )
