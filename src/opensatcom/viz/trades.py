"""Trade study visualizations using Plotly."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def plot_pareto_interactive(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    pareto_df: pd.DataFrame,
    title: str = "Pareto Front Analysis",
) -> Any:
    """Interactive Plotly scatter with Pareto front highlighted.

    Renders all design points as semi-transparent markers and overlays the
    Pareto-optimal subset as a connected star-marker trace.

    Parameters
    ----------
    df : pd.DataFrame
        Full DOE / trade-study results containing at least *x_col* and
        *y_col* columns.
    x_col : str
        Column name used for the x-axis (e.g., ``"cost_usd"``).
    y_col : str
        Column name used for the y-axis (e.g., ``"throughput_p50"``).
    pareto_df : pd.DataFrame
        Subset of *df* representing the Pareto-optimal designs.
    title : str, optional
        Plot title. Default is ``"Pareto Front Analysis"``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly figure with all designs and the Pareto front.
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    # All points
    hover_cols = [c for c in df.columns if c not in (x_col, y_col)]
    hover_text = []
    for _, row in df.iterrows():
        parts = [f"{c}: {row[c]:.3f}" if isinstance(row[c], float) else f"{c}: {row[c]}"
                 for c in hover_cols[:5]]  # Limit to 5 hover columns
        hover_text.append("<br>".join(parts))

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="markers",
        name="All designs",
        marker=dict(color="#90caf9", size=8, opacity=0.5),
        text=hover_text,
        hoverinfo="text+x+y",
    ))

    # Pareto front
    pf = pareto_df.sort_values(x_col)
    fig.add_trace(go.Scatter(
        x=pf[x_col],
        y=pf[y_col],
        mode="lines+markers",
        name="Pareto front",
        line=dict(color="#c62828", width=2, dash="dash"),
        marker=dict(color="#1565c0", size=12, symbol="star"),
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        template="plotly_white",
        hovermode="closest",
    )
    return fig


def plot_doe_parallel_coords(
    df: pd.DataFrame,
    objectives: list[str] | None = None,
    title: str = "DOE Parallel Coordinates",
) -> Any:
    """Parallel coordinates plot for DOE results.

    Displays all numeric columns of the DOE results as parallel coordinate
    axes, colored by the first objective column when provided.

    Parameters
    ----------
    df : pd.DataFrame
        DOE results with parameter and objective columns. Only numeric
        columns are included as axes.
    objectives : list of str or None, optional
        Column names to highlight as objectives. The first entry is used
        as the color dimension. Default is ``None`` (color by the last
        numeric column).
    title : str, optional
        Plot title. Default is ``"DOE Parallel Coordinates"``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly parallel-coordinates figure.
    """
    import plotly.graph_objects as go

    # Select numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    color_col: str | None = None
    if objectives and objectives[0] in numeric_cols:
        color_col = objectives[0]
    else:
        color_col = numeric_cols[-1] if numeric_cols else None

    dimensions = []
    for col in numeric_cols:
        dimensions.append(dict(
            label=col,
            values=df[col],
            range=[float(df[col].min()), float(df[col].max())],
        ))

    fig = go.Figure(data=go.Parcoords(
        line=dict(
            color=df[color_col] if color_col else None,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title=color_col) if color_col else None,
        ),
        dimensions=dimensions,
    ))

    fig.update_layout(title=title)
    return fig


def plot_sensitivity_bar(
    param_names: list[str],
    s1: np.ndarray,
    st: np.ndarray,
    s1_conf: np.ndarray | None = None,
    st_conf: np.ndarray | None = None,
    title: str = "Sobol Sensitivity Analysis",
    metric_name: str = "output",
) -> Any:
    """Horizontal bar chart of Sobol first-order and total-order indices.

    Parameters
    ----------
    param_names : list of str
        Parameter names.
    s1 : numpy.ndarray
        First-order Sobol indices.
    st : numpy.ndarray
        Total-order Sobol indices.
    s1_conf : numpy.ndarray or None
        Confidence intervals for S1 (half-width).
    st_conf : numpy.ndarray or None
        Confidence intervals for ST (half-width).
    title : str
        Plot title.
    metric_name : str
        Name of the output metric being analyzed.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly horizontal bar chart.
    """
    import plotly.graph_objects as go

    # Sort by total-order index descending
    order = np.argsort(st)[::-1]
    names_sorted = [param_names[i] for i in order]
    s1_sorted = s1[order]
    st_sorted = st[order]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=names_sorted,
        x=st_sorted,
        orientation="h",
        name="Total-order (ST)",
        marker=dict(color="#1565c0", opacity=0.6),
        error_x=dict(
            type="data",
            array=st_conf[order] if st_conf is not None else None,
            visible=st_conf is not None,
        ),
    ))

    fig.add_trace(go.Bar(
        y=names_sorted,
        x=s1_sorted,
        orientation="h",
        name="First-order (S1)",
        marker=dict(color="#c62828", opacity=0.8),
        error_x=dict(
            type="data",
            array=s1_conf[order] if s1_conf is not None else None,
            visible=s1_conf is not None,
        ),
    ))

    fig.update_layout(
        title=f"{title} — {metric_name}",
        xaxis_title="Sobol Index",
        yaxis_title="Parameter",
        barmode="overlay",
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
    )
    return fig
