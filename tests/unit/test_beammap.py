"""Tests for BeamMap datamodel."""

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
from opensatcom.payload.interference import SimpleInterferenceModel
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation


def _make_2beam_beamset() -> BeamSet:
    """Two beams at (0,0) and (5,0) with 2deg beamwidth."""
    ant0 = CosineRolloffAntenna(
        peak_gain_dbi=35.0, theta_3db_deg=2.0,
        boresight_az_deg=0.0, boresight_el_deg=0.0,
    )
    ant1 = CosineRolloffAntenna(
        peak_gain_dbi=35.0, theta_3db_deg=2.0,
        boresight_az_deg=5.0, boresight_el_deg=0.0,
    )
    beam0 = Beam("B0", 0.0, 0.0, 100.0, ant0)
    beam1 = Beam("B1", 5.0, 0.0, 100.0, ant1)
    sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=0.0, rx_noise_temp_k=500.0)
    return BeamSet([beam0, beam1], sc, prop, rf)


class TestBeamMap:
    def test_beam_assignment_9point_grid(self) -> None:
        """2-beam, 9-point grid: each point assigned correct serving beam."""
        bs = _make_2beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        # 3x3 grid: az in [-1, 2.5, 6], el in [-1, 0, 1]
        grid_az = np.array([-1.0, 2.5, 6.0])
        grid_el = np.array([-1.0, 0.0, 1.0])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3,
            PropagationConditions(), beam_selection="max_gain",
        )

        assert len(bm) == 9

        # Check serving beam assignments
        for p in bm:
            if p.az_deg < 2.5:
                assert p.serving_beam_id == "B0"
            elif p.az_deg > 2.5:
                assert p.serving_beam_id == "B1"
            # At midpoint (2.5), either is acceptable

    def test_sinr_worse_near_edge(self) -> None:
        """SINR at beam boresight should be better than at beam edge."""
        bs = _make_2beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        model = SimpleInterferenceModel()

        # At B0 boresight (0, 0)
        result_center = model.evaluate(
            bs, "B0", 0.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )
        # At beam edge (2.0, 0) -- near B1
        result_edge = model.evaluate(
            bs, "B0", 2.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        assert result_center.sinr_db > result_edge.sinr_db

    def test_to_dataframe(self) -> None:
        bs = _make_2beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        grid_az = np.array([0.0, 5.0])
        grid_el = np.array([0.0])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3, PropagationConditions()
        )

        df = bm.to_dataframe()
        assert len(df) == 2
        expected_cols = {
            "az_deg", "el_deg", "serving_beam_id", "signal_dbw",
            "interference_dbw", "noise_dbw", "cnir_db", "sinr_db",
            "cn0_dbhz", "ebn0_db", "margin_db", "throughput_mbps",
        }
        assert set(df.columns) == expected_cols

    def test_summary_stats(self) -> None:
        bs = _make_2beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        grid_az = np.array([0.0, 2.5, 5.0])
        grid_el = np.array([0.0])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3, PropagationConditions()
        )

        assert bm.sinr_db_mean > 0
        assert bm.sinr_db_min >= 0
        assert isinstance(bm.cnir_db_mean, float)
        assert isinstance(bm.margin_db_mean, float)

    def test_per_beam_summary(self) -> None:
        bs = _make_2beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        grid_az = np.array([0.0, 5.0])
        grid_el = np.array([0.0])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3, PropagationConditions()
        )

        summary = bm.per_beam_summary()
        assert "B0" in summary
        assert "B1" in summary
        assert summary["B0"]["points_served"] == 1.0
        assert summary["B1"]["points_served"] == 1.0
