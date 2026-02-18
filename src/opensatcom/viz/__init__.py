"""Beautiful interactive and static visualizations for OpenSatCom."""

from opensatcom.viz.constellation import plot_constellation_coverage
from opensatcom.viz.heatmaps import plot_beam_map_interactive, plot_rain_attenuation_surface
from opensatcom.viz.statistical import (
    plot_availability_heatmap,
    plot_margin_distribution,
    plot_modcod_waterfall,
)
from opensatcom.viz.timeline import plot_elevation_profile, plot_link_margin_timeline
from opensatcom.viz.trades import plot_doe_parallel_coords, plot_pareto_interactive

__all__ = [
    "plot_availability_heatmap",
    "plot_beam_map_interactive",
    "plot_constellation_coverage",
    "plot_doe_parallel_coords",
    "plot_elevation_profile",
    "plot_link_margin_timeline",
    "plot_margin_distribution",
    "plot_modcod_waterfall",
    "plot_pareto_interactive",
    "plot_rain_attenuation_surface",
]
