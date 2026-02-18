"""Tests for beam map report generation."""

import numpy as np

from opensatcom.antenna.cosine import CosineRolloffAntenna
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.models import (
    PropagationConditions,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.payload.beam import Beam
from opensatcom.payload.beamset import BeamSet
from opensatcom.payload.capacity import compute_beam_map
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation
from opensatcom.reports.beammap import render_beammap_report


def _make_beam_map():
    """Build a small 2-beam beam map for testing."""
    ant0 = CosineRolloffAntenna(
        peak_gain_dbi=35.0, theta_3db_deg=2.0,
        boresight_az_deg=0.0, boresight_el_deg=0.0,
    )
    ant1 = CosineRolloffAntenna(
        peak_gain_dbi=35.0, theta_3db_deg=2.0,
        boresight_az_deg=5.0, boresight_el_deg=0.0,
    )
    beams = [
        Beam("B0", 0.0, 0.0, 100.0, ant0),
        Beam("B1", 5.0, 0.0, 100.0, ant1),
    ]
    sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=0.0, rx_noise_temp_k=500.0)
    bs = BeamSet(beams, sc, prop, rf)

    rx_ant = ParametricAntenna(gain_dbi=35.0)
    rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

    grid_az = np.array([0.0, 2.5, 5.0])
    grid_el = np.array([0.0])

    return compute_beam_map(
        bs, grid_az, grid_el, rx_ant, rx_term, 1200e3, PropagationConditions()
    )


class TestBeamMapReport:
    def test_report_contains_beam_ids(self, tmp_path) -> None:
        bm = _make_beam_map()
        out = tmp_path / "report.html"
        render_beammap_report(bm, {}, out)

        html = out.read_text()
        assert "B0" in html
        assert "B1" in html

    def test_report_contains_sinr(self, tmp_path) -> None:
        bm = _make_beam_map()
        out = tmp_path / "report.html"
        render_beammap_report(bm, {}, out)

        html = out.read_text()
        assert "SINR" in html

    def test_report_contains_images(self, tmp_path) -> None:
        bm = _make_beam_map()
        out = tmp_path / "report.html"
        render_beammap_report(bm, {}, out)

        html = out.read_text()
        assert "<img" in html
        assert "data:image/png;base64," in html

    def test_report_with_plots_dir(self, tmp_path) -> None:
        bm = _make_beam_map()
        out = tmp_path / "report.html"
        plots = tmp_path / "plots"
        render_beammap_report(bm, {}, out, plots_dir=plots)

        assert (plots / "sinr_map.png").exists()
        assert (plots / "cnir_map.png").exists()

    def test_report_returns_path(self, tmp_path) -> None:
        bm = _make_beam_map()
        out = tmp_path / "report.html"
        result = render_beammap_report(bm, {}, out)
        assert result == out
        assert out.exists()
