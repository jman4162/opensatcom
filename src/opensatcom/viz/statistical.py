"""Statistical distribution visualizations using Seaborn and Matplotlib."""

from __future__ import annotations

from typing import Any

import numpy as np


def plot_margin_distribution(
    margin_db: np.ndarray,
    title: str = "Link Margin Distribution",
) -> Any:
    """KDE + histogram of margin distribution.

    Returns matplotlib Figure.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    valid = margin_db[~np.isnan(margin_db)]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(valid, kde=True, ax=ax, color="#1565c0", alpha=0.6)
    ax.axvline(0, color="red", linestyle="--", alpha=0.7, label="Zero margin")
    ax.set_xlabel("Margin (dB)")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_modcod_waterfall(
    times_s: np.ndarray,
    selected_modcod: list[str],
    title: str = "ModCod Selection Over Time",
) -> Any:
    """Stacked bar showing ModCod selection over time.

    Returns matplotlib Figure.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Map unique ModCods to colors
    unique_modcods = sorted(set(m for m in selected_modcod if m))
    if not unique_modcods:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.set_title(title)
        return fig

    cmap = plt.colormaps.get_cmap("tab20").resampled(len(unique_modcods))
    mc_to_idx = {mc: i for i, mc in enumerate(unique_modcods)}

    fig, ax = plt.subplots(figsize=(12, 4))
    colors = [cmap(mc_to_idx.get(m, 0)) if m else (0.9, 0.9, 0.9, 1.0)
              for m in selected_modcod]
    ax.bar(times_s, 1, width=times_s[1] - times_s[0] if len(times_s) > 1 else 1,
           color=colors, edgecolor="none")

    # Legend
    import matplotlib.patches as mpatches

    patches = [mpatches.Patch(color=cmap(i), label=mc)
               for i, mc in enumerate(unique_modcods)]
    ax.legend(handles=patches, loc="upper right", fontsize=7, ncol=3)

    ax.set_xlabel("Time (s)")
    ax.set_title(title)
    ax.set_yticks([])
    fig.tight_layout()
    return fig


def plot_availability_heatmap(
    data: np.ndarray,
    x_labels: list[str] | None = None,
    y_labels: list[str] | None = None,
    title: str = "Availability Heatmap",
) -> Any:
    """Seaborn heatmap of availability vs parameter pairs.

    Parameters
    ----------
    data : np.ndarray
        2D array of availability values.

    Returns matplotlib Figure.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        data,
        ax=ax,
        cmap="RdYlGn",
        vmin=0.9,
        vmax=1.0,
        annot=True,
        fmt=".3f",
        xticklabels=x_labels if x_labels else "auto",
        yticklabels=y_labels if y_labels else "auto",
    )
    ax.set_title(title)
    fig.tight_layout()
    return fig
