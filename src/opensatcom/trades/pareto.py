"""Pareto front extraction and plotting for trade studies."""

from __future__ import annotations

import pandas as pd


def extract_pareto_front(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    minimize_x: bool = True,
    minimize_y: bool = False,
) -> pd.DataFrame:
    """Extract the Pareto-optimal (non-dominated) front from results.

    Parameters
    ----------
    df : pd.DataFrame
        Results DataFrame.
    x_col : str
        Column name for x-axis objective.
    y_col : str
        Column name for y-axis objective.
    minimize_x : bool
        Whether x should be minimized (True) or maximized (False).
    minimize_y : bool
        Whether y should be minimized (True) or maximized (False).

    Returns
    -------
    pd.DataFrame
        Subset of df containing only Pareto-optimal points.
    """
    # Convert objectives: multiply by -1 for maximization so we always minimize
    x = df[x_col].values.copy()
    y = df[y_col].values.copy()
    if not minimize_x:
        x = -x
    if not minimize_y:
        y = -y

    n = len(df)
    is_pareto = [True] * n

    for i in range(n):
        if not is_pareto[i]:
            continue
        for j in range(n):
            if i == j or not is_pareto[j]:
                continue
            # j dominates i if j is <= in both and < in at least one
            if x[j] <= x[i] and y[j] <= y[i] and (x[j] < x[i] or y[j] < y[i]):
                is_pareto[i] = False
                break

    return df.iloc[[i for i in range(n) if is_pareto[i]]].copy()


def plot_pareto(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    pareto_df: pd.DataFrame,
) -> object:
    """Create a scatter plot with Pareto front highlighted.

    Returns matplotlib Figure.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df[x_col], df[y_col], alpha=0.4, label="All points", color="#90caf9")

    # Sort Pareto front for line plot
    pf = pareto_df.sort_values(x_col)
    ax.scatter(pf[x_col], pf[y_col], color="#1565c0", s=80, zorder=5, label="Pareto front")
    ax.plot(pf[x_col], pf[y_col], "r--", linewidth=1.5, alpha=0.7)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title("Pareto Front Analysis")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
