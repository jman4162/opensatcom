"""Golden test vectors for FSPL and snapshot link budget."""

import math

import pytest

from opensatcom.antenna.pam import PamArrayAntenna
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.constants import SPEED_OF_LIGHT_MPS
from opensatcom.core.models import (
    LinkInputs,
    PropagationConditions,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.link.engine import DefaultLinkEngine
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation


@pytest.mark.golden
class TestFSPLGolden:
    def test_fspl_19_7ghz_1200km(self) -> None:
        """Frozen FSPL value at 19.7 GHz / 1200 km."""
        f_hz = 19.7e9
        range_m = 1200e3
        expected_db = 20.0 * math.log10(
            4.0 * math.pi * range_m * f_hz / SPEED_OF_LIGHT_MPS
        )
        fspl = FreeSpacePropagation()
        result = fspl.total_path_loss_db(f_hz, 30.0, range_m, PropagationConditions())
        # Frozen golden value: ~179.92 dB
        assert result == pytest.approx(expected_db, abs=0.01)
        assert result == pytest.approx(179.92, abs=0.1)


@pytest.mark.golden
class TestSnapshotGolden:
    def test_hello_world_snapshot(self) -> None:
        """Frozen snapshot link budget matching spec Hello World."""
        tx = Terminal("sat", 0.0, 0.0, 550e3)
        rx = Terminal("ut", 47.6062, -122.3321, 50.0, system_noise_temp_k=500.0)
        sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
        tx_ant = PamArrayAntenna(
            nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5, taper=("taylor", -28)
        )
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=500.0)
        inputs = LinkInputs(tx, rx, sc, tx_ant, rx_ant, prop, rf)

        engine = DefaultLinkEngine()
        out = engine.evaluate_snapshot(
            elev_deg=30.0, az_deg=0.0, range_m=1200e3,
            inputs=inputs, cond=PropagationConditions(),
        )

        # Frozen golden values (computed analytically):
        # TX power: 10*log10(200) ≈ 23.01 dBW
        # TX losses: 2.0 dB
        # TX gain: 10*log10(4*pi*64) ≈ 29.05 dBi
        # EIRP ≈ 23.01 - 2.0 + 29.05 = 50.06 dBW
        assert out.eirp_dbw == pytest.approx(50.06, abs=0.1)

        # FSPL at 19.7 GHz / 1200 km ≈ 179.92 dB
        assert out.path_loss_db == pytest.approx(179.92, abs=0.1)

        # G/T = 35 - 10*log10(500) ≈ 35 - 26.99 = 8.01 dB/K
        assert out.gt_dbk == pytest.approx(8.01, abs=0.1)

        # C/N0 = 50.06 - 179.92 + 8.01 + 228.6 ≈ 106.75 dB-Hz
        assert out.cn0_dbhz == pytest.approx(106.75, abs=0.2)

        # Eb/N0 = C/N0 - 10*log10(BW) = 106.75 - 83.01 ≈ 23.74 dB
        assert out.ebn0_db == pytest.approx(23.74, abs=0.2)

        # Margin = Eb/N0 - required = 23.74 - 6.0 ≈ 17.74 dB
        assert out.margin_db == pytest.approx(17.74, abs=0.2)
