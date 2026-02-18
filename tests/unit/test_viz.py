"""Tests for visualization module."""

import numpy as np
import pandas as pd


class TestTimelinePlots:
    def test_link_margin_timeline_returns_figure(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.timeline import plot_link_margin_timeline

        times = np.linspace(0, 600, 100)
        margin = np.random.default_rng(42).normal(5.0, 2.0, 100)
        outages = margin < 0

        fig = plot_link_margin_timeline(times, margin, outages)
        assert isinstance(fig, go.Figure)

    def test_elevation_profile_returns_figure(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.timeline import plot_elevation_profile

        times = np.linspace(0, 600, 100)
        elev = np.concatenate([np.linspace(10, 80, 50), np.linspace(80, 10, 50)])

        fig = plot_elevation_profile(times, elev)
        assert isinstance(fig, go.Figure)


class TestHeatmapPlots:
    def test_beam_map_interactive_returns_figure(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.heatmaps import plot_beam_map_interactive

        df = pd.DataFrame({
            "az_deg": [0, 1, 2, 0, 1, 2],
            "el_deg": [30, 30, 30, 35, 35, 35],
            "sinr_db": [10.0, 12.0, 8.0, 11.0, 13.0, 9.0],
            "margin_db": [3.0, 5.0, 1.0, 4.0, 6.0, 2.0],
            "beam_id": ["b1", "b1", "b2", "b1", "b1", "b2"],
        })
        fig = plot_beam_map_interactive(df)
        assert isinstance(fig, go.Figure)

    def test_rain_attenuation_surface(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.heatmaps import plot_rain_attenuation_surface

        freqs = np.array([4, 12, 20, 30])
        elevs = np.array([10, 30, 60, 90])
        fig = plot_rain_attenuation_surface(freqs, elevs)
        assert isinstance(fig, go.Figure)


class TestStatisticalPlots:
    def test_margin_distribution_returns_figure(self) -> None:
        import matplotlib.figure

        from opensatcom.viz.statistical import plot_margin_distribution

        margin = np.random.default_rng(42).normal(5.0, 2.0, 200)
        fig = plot_margin_distribution(margin)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_modcod_waterfall_returns_figure(self) -> None:
        import matplotlib.figure

        from opensatcom.viz.statistical import plot_modcod_waterfall

        times = np.linspace(0, 100, 50)
        modcods = ["QPSK_1/2"] * 20 + ["QPSK_3/4"] * 20 + ["8PSK_2/3"] * 10
        fig = plot_modcod_waterfall(times, modcods)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_availability_heatmap_returns_figure(self) -> None:
        import matplotlib.figure

        from opensatcom.viz.statistical import plot_availability_heatmap

        data = np.random.default_rng(42).uniform(0.95, 1.0, (4, 5))
        fig = plot_availability_heatmap(data)
        assert isinstance(fig, matplotlib.figure.Figure)


class TestTradesPlots:
    def test_pareto_interactive(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.trades import plot_pareto_interactive

        df = pd.DataFrame({
            "cost": np.random.default_rng(42).uniform(10, 100, 50),
            "throughput": np.random.default_rng(42).uniform(1, 50, 50),
        })
        pareto = df.iloc[:5]
        fig = plot_pareto_interactive(df, "cost", "throughput", pareto)
        assert isinstance(fig, go.Figure)

    def test_doe_parallel_coords(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.trades import plot_doe_parallel_coords

        df = pd.DataFrame({
            "freq_hz": np.random.default_rng(42).uniform(10e9, 30e9, 20),
            "tx_power_w": np.random.default_rng(42).uniform(10, 200, 20),
            "margin_db": np.random.default_rng(42).normal(5, 3, 20),
        })
        fig = plot_doe_parallel_coords(df, objectives=["margin_db"])
        assert isinstance(fig, go.Figure)


class TestConstellationPlot:
    def test_constellation_coverage(self) -> None:
        import plotly.graph_objects as go

        from opensatcom.viz.constellation import plot_constellation_coverage

        tracks = {
            "sat1": (np.linspace(0, 360, 50), np.linspace(10, 60, 50)),
            "sat2": (np.linspace(90, 270, 50), np.linspace(20, 70, 50)),
        }
        fig = plot_constellation_coverage(tracks)
        assert isinstance(fig, go.Figure)
