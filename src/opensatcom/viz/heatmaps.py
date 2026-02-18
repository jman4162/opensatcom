"""Heatmap and 3D surface visualizations using Plotly."""

from __future__ import annotations

from typing import Any

import numpy as np


def plot_beam_map_interactive(
    beam_map_df: Any,
    metric: str = "sinr_db",
    title: str = "Beam Coverage Map",
) -> Any:
    """Interactive beam map heatmap with hover details.

    Parameters
    ----------
    beam_map_df : pd.DataFrame
        DataFrame with columns: az_deg, el_deg, sinr_db, margin_db, beam_id, etc.
    metric : str
        Metric column to color by.

    Returns plotly go.Figure.
    """
    import plotly.graph_objects as go

    hover_cols = [c for c in beam_map_df.columns if c not in ("az_deg", "el_deg")]
    hover_text = []
    for _, row in beam_map_df.iterrows():
        parts = [f"{c}: {row[c]:.2f}" if isinstance(row[c], float) else f"{c}: {row[c]}"
                 for c in hover_cols]
        hover_text.append("<br>".join(parts))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=beam_map_df["az_deg"],
        y=beam_map_df["el_deg"],
        mode="markers",
        marker=dict(
            size=10,
            color=beam_map_df[metric],
            colorscale="RdYlGn",
            colorbar=dict(title=metric),
            line=dict(width=0.5, color="black"),
        ),
        text=hover_text,
        hoverinfo="text",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Azimuth (deg)",
        yaxis_title="Elevation (deg)",
        template="plotly_white",
    )
    return fig


def plot_rain_attenuation_surface(
    freqs_ghz: np.ndarray,
    elevs_deg: np.ndarray,
    rain_rate_mm_per_hr: float = 25.0,
    title: str = "Rain Attenuation vs Frequency & Elevation",
) -> Any:
    """3D surface plot of rain loss vs frequency vs elevation.

    Returns plotly go.Figure.
    """
    import plotly.graph_objects as go

    from opensatcom.core.models import PropagationConditions
    from opensatcom.propagation.rain import RainAttenuationP618

    model = RainAttenuationP618(rain_rate_mm_per_hr=rain_rate_mm_per_hr)
    cond = PropagationConditions()

    freq_grid, elev_grid = np.meshgrid(freqs_ghz, elevs_deg)
    loss_grid = np.zeros_like(freq_grid)
    for i in range(freq_grid.shape[0]):
        for j in range(freq_grid.shape[1]):
            loss_grid[i, j] = model.total_path_loss_db(
                freq_grid[i, j] * 1e9, elev_grid[i, j], 1e6, cond
            )

    fig = go.Figure(data=[go.Surface(
        x=freqs_ghz,
        y=elevs_deg,
        z=loss_grid,
        colorscale="YlOrRd",
        colorbar=dict(title="Loss (dB)"),
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="Frequency (GHz)",
            yaxis_title="Elevation (deg)",
            zaxis_title="Rain Loss (dB)",
        ),
    )
    return fig
