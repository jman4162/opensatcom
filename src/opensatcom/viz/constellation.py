"""Constellation and coverage visualizations using Plotly."""

from __future__ import annotations

from typing import Any

import numpy as np


def plot_constellation_coverage(
    sat_tracks: dict[str, tuple[np.ndarray, np.ndarray]],
    min_elevation_deg: float = 10.0,
    title: str = "Satellite Coverage (Az/El)",
) -> Any:
    """Plotly polar plot of satellite tracks (az/el) with coverage cone.

    Each satellite track is plotted in polar coordinates (azimuth as angle,
    90 - elevation as radius so the zenith sits at the center). A dashed
    circle marks the minimum-elevation visibility boundary.

    Parameters
    ----------
    sat_tracks : dict of {str: tuple of (np.ndarray, np.ndarray)}
        Mapping from satellite ID to a ``(azimuth_deg, elevation_deg)``
        pair of 1-D arrays describing the track.
    min_elevation_deg : float, optional
        Minimum elevation angle in degrees for the visibility cone circle.
        Default is ``10.0``.
    title : str, optional
        Plot title. Default is ``"Satellite Coverage (Az/El)"``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly polar figure with satellite tracks and
        minimum-elevation boundary.
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    colors = ["#1565c0", "#c62828", "#2e7d32", "#e65100", "#6a1b9a",
              "#00838f", "#ef6c00", "#283593"]

    for i, (sat_id, (az, el)) in enumerate(sat_tracks.items()):
        color = colors[i % len(colors)]
        # Convert elevation to polar radius: 90 - elevation (zenith at center)
        r = 90.0 - el
        fig.add_trace(go.Scatterpolar(
            r=r,
            theta=az,
            mode="lines+markers",
            name=sat_id,
            line=dict(color=color, width=2),
            marker=dict(size=3),
        ))

    # Minimum elevation circle
    theta_circle = np.linspace(0, 360, 100)
    r_circle = np.full(100, 90.0 - min_elevation_deg)
    fig.add_trace(go.Scatterpolar(
        r=r_circle,
        theta=theta_circle,
        mode="lines",
        name=f"Min elev ({min_elevation_deg}°)",
        line=dict(color="red", width=1, dash="dash"),
        showlegend=True,
    ))

    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(
                range=[0, 90],
                tickvals=[0, 15, 30, 45, 60, 75, 90],
                ticktext=["90°", "75°", "60°", "45°", "30°", "15°", "0°"],
            ),
            angularaxis=dict(direction="clockwise"),
        ),
    )
    return fig
