"""Trade study visualizations using Plotly."""

from __future__ import annotations

from typing import Any

import pandas as pd


def plot_pareto_interactive(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    pareto_df: pd.DataFrame,
    title: str = "Pareto Front Analysis",
) -> Any:
    """Interactive Plotly scatter with Pareto front highlighted.

    Returns plotly go.Figure.
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

    Parameters
    ----------
    df : pd.DataFrame
        DOE results with parameter and objective columns.
    objectives : list[str] | None
        Columns to highlight as objectives (colored by first objective).

    Returns plotly go.Figure.
    """
    import plotly.graph_objects as go

    # Select numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

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
