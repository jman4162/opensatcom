"""Tests for compute_beam_map capacity computation."""

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


def _make_4beam_beamset() -> BeamSet:
    """4-beam payload at cardinal directions."""
    positions = [(0.0, 0.0), (5.0, 0.0), (0.0, 5.0), (5.0, 5.0)]
    beams = []
    for i, (az, el) in enumerate(positions):
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=az, boresight_el_deg=el,
        )
        beams.append(Beam(f"B{i}", az, el, 100.0, ant))

    sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=0.0, rx_noise_temp_k=500.0)
    return BeamSet(beams, sc, prop, rf)


class TestComputeBeamMap:
    def test_correct_point_count(self) -> None:
        bs = _make_4beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        grid_az = np.linspace(-2, 7, 5)
        grid_el = np.linspace(-2, 7, 5)

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3, PropagationConditions()
        )

        assert len(bm) == 25  # 5 x 5

    def test_dataframe_columns(self) -> None:
        bs = _make_4beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        grid_az = np.array([0.0, 5.0])
        grid_el = np.array([0.0, 5.0])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3, PropagationConditions()
        )

        df = bm.to_dataframe()
        assert "sinr_db" in df.columns
        assert "serving_beam_id" in df.columns
        assert len(df) == 4

    def test_nearest_selection(self) -> None:
        """Nearest beam selection assigns by angular distance."""
        bs = _make_4beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        grid_az = np.array([0.5])
        grid_el = np.array([0.5])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3,
            PropagationConditions(), beam_selection="nearest",
        )

        # (0.5, 0.5) is closest to B0 at (0, 0)
        assert bm.points[0].serving_beam_id == "B0"

    def test_max_gain_selection(self) -> None:
        """Max-gain selection picks beam with highest gain toward grid point."""
        bs = _make_4beam_beamset()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)

        # Right at B2 boresight (0, 5)
        grid_az = np.array([0.0])
        grid_el = np.array([5.0])

        bm = compute_beam_map(
            bs, grid_az, grid_el, rx_ant, rx_term, 1200e3,
            PropagationConditions(), beam_selection="max_gain",
        )

        assert bm.points[0].serving_beam_id == "B2"
