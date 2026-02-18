"""Golden tests for beam map / multi-beam interference computations.

These tests freeze known-good values to catch regressions.
If the interference math or antenna model changes, update the
golden values after verifying correctness.
"""

import numpy as np
import pytest

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

# Shared test fixtures
_SC = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
_PROP = CompositePropagation([FreeSpacePropagation()])
_RF = RFChainModel(tx_power_w=100.0, tx_losses_db=0.0, rx_noise_temp_k=500.0)
_RX_ANT = ParametricAntenna(gain_dbi=35.0)
_RX_TERM = Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)
_RANGE_M = 1200e3


@pytest.mark.golden
class TestBeamMapGolden:
    def test_2beam_midpoint_sinr(self) -> None:
        """Frozen: 2 beams at (0,0) and (5,0), victim at (2.5,0).

        Both beams have equal gain at the midpoint → SINR = 0 dB.
        """
        ant0 = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        ant1 = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=5.0, boresight_el_deg=0.0,
        )
        b0 = Beam("B0", 0.0, 0.0, 100.0, ant0)
        b1 = Beam("B1", 5.0, 0.0, 100.0, ant1)
        bs = BeamSet([b0, b1], _SC, _PROP, _RF)

        model = SimpleInterferenceModel()
        result = model.evaluate(
            bs, "B0", 2.5, 0.0, _RANGE_M, _RX_ANT, _RX_TERM, PropagationConditions()
        )

        # Frozen golden values
        assert result.sinr_db == pytest.approx(0.0, abs=0.01)
        assert result.cn0_dbhz == pytest.approx(92.94, abs=0.1)
        assert result.cnir_db == pytest.approx(-0.42, abs=0.1)
        assert result.margin_db == pytest.approx(3.93, abs=0.1)

    def test_4beam_capacity_map(self) -> None:
        """Frozen: 4 beams in a square, 5x5 grid, aggregate metrics."""
        positions = [(0.0, 0.0), (5.0, 0.0), (0.0, 5.0), (5.0, 5.0)]
        beams = []
        for i, (az, el) in enumerate(positions):
            ant = CosineRolloffAntenna(
                peak_gain_dbi=35.0, theta_3db_deg=2.0,
                boresight_az_deg=az, boresight_el_deg=el,
            )
            beams.append(Beam(f"B{i}", az, el, 100.0, ant))

        bs = BeamSet(beams, _SC, _PROP, _RF)
        grid_az = np.arange(-2, 8, 2.0)
        grid_el = np.arange(-2, 8, 2.0)

        bm = compute_beam_map(
            bs, grid_az, grid_el, _RX_ANT, _RX_TERM, _RANGE_M, PropagationConditions()
        )

        # Frozen golden values
        assert len(bm) == 25
        assert bm.sinr_db_mean == pytest.approx(31.08, abs=0.1)
        assert bm.sinr_db_min == pytest.approx(11.92, abs=0.1)
        assert bm.margin_db_mean == pytest.approx(10.68, abs=0.1)

    def test_single_beam_infinite_sinr(self) -> None:
        """Single beam: no interference → SINR = infinity."""
        import math

        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        beam = Beam("B0", 0.0, 0.0, 100.0, ant)
        bs = BeamSet([beam], _SC, _PROP, _RF)

        model = SimpleInterferenceModel()
        result = model.evaluate(
            bs, "B0", 0.0, 0.0, _RANGE_M, _RX_ANT, _RX_TERM, PropagationConditions()
        )

        assert result.sinr_db == math.inf
        assert result.cn0_dbhz > 90.0
