"""Time-series visualization functions using Plotly."""

from __future__ import annotations

from typing import Any

import numpy as np


def plot_link_margin_timeline(
    times_s: np.ndarray,
    margin_db: np.ndarray,
    outages_mask: np.ndarray | None = None,
    threshold_db: float = 0.0,
    title: str = "Link Margin vs Time",
) -> Any:
    """Interactive link margin timeline with hover tooltips and outage shading.

    Parameters
    ----------
    times_s : np.ndarray
        1-D array of time stamps in seconds.
    margin_db : np.ndarray
        1-D array of link margin values in dB, same length as *times_s*.
    outages_mask : np.ndarray or None, optional
        Boolean array indicating outage intervals (``True`` = outage).
        When provided, outage points are plotted as red markers.
        Default is ``None`` (no outage shading).
    threshold_db : float, optional
        Margin threshold in dB drawn as a horizontal dashed line.
        Default is ``0.0``.
    title : str, optional
        Plot title. Default is ``"Link Margin vs Time"``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly figure with margin trace, outage markers, and
        threshold line.
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    # Valid margin line
    valid = ~outages_mask if outages_mask is not None else np.ones(len(times_s), dtype=bool)
    fig.add_trace(go.Scatter(
        x=times_s[valid],
        y=margin_db[valid],
        mode="lines",
        name="Margin (dB)",
        line=dict(color="#1565c0", width=2),
        hovertemplate="Time: %{x:.1f}s<br>Margin: %{y:.2f} dB<extra></extra>",
    ))

    # Outage regions
    if outages_mask is not None and np.any(outages_mask):
        outage_times = times_s[outages_mask]
        fig.add_trace(go.Scatter(
            x=outage_times,
            y=np.zeros(len(outage_times)),
            mode="markers",
            name="Outage",
            marker=dict(color="red", size=4, symbol="x"),
        ))

    # Threshold line
    fig.add_hline(y=threshold_db, line_dash="dash", line_color="red",
                  annotation_text=f"Threshold: {threshold_db} dB")

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Margin (dB)",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_elevation_profile(
    times_s: np.ndarray,
    elev_deg: np.ndarray,
    title: str = "Elevation Profile",
) -> Any:
    """Interactive elevation vs time plot.

    Parameters
    ----------
    times_s : np.ndarray
        1-D array of time stamps in seconds.
    elev_deg : np.ndarray
        1-D array of elevation angles in degrees, same length as *times_s*.
    title : str, optional
        Plot title. Default is ``"Elevation Profile"``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly figure showing elevation angle over time.
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times_s,
        y=elev_deg,
        mode="lines",
        name="Elevation",
        line=dict(color="#2e7d32", width=2),
        hovertemplate="Time: %{x:.1f}s<br>Elevation: %{y:.1f} deg<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Elevation (deg)",
        template="plotly_white",
    )
    return fig
