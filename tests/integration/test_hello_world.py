"""Integration test: spec Hello World example works end-to-end."""

import pytest

from opensatcom.antenna import PamArrayAntenna, ParametricAntenna
from opensatcom.core import LinkInputs, PropagationConditions, Scenario, Terminal
from opensatcom.link import DefaultLinkEngine
from opensatcom.propagation import CompositePropagation, FreeSpacePropagation
from opensatcom.rf import RFChainModel


@pytest.mark.integration
class TestHelloWorld:
    def test_spec_hello_world(self) -> None:
        """Exact Hello World code from spec Section 24."""
        tx = Terminal("sat", 0, 0, 550e3)
        rx = Terminal("ut", 47.6062, -122.3321, 50, system_noise_temp_k=500)

        sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)

        tx_ant = PamArrayAntenna(
            nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5, taper=("taylor", -28)
        )
        rx_ant = ParametricAntenna(gain_dbi=35)

        prop = CompositePropagation([FreeSpacePropagation()])
        rf = RFChainModel(tx_power_w=200, tx_losses_db=2.0, rx_noise_temp_k=500)

        inputs = LinkInputs(tx, rx, sc, tx_ant, rx_ant, prop, rf)

        engine = DefaultLinkEngine()
        out = engine.evaluate_snapshot(
            elev_deg=30, az_deg=0, range_m=1200e3,
            inputs=inputs, cond=PropagationConditions(),
        )

        # All three metrics should be printable and positive
        assert out.margin_db > 0
        assert out.ebn0_db > 0
        assert out.cn0_dbhz > 0

        # Should have complete breakdown
        assert out.breakdown is not None
        assert len(out.breakdown) == 13

    def test_hello_world_imports(self) -> None:
        """Verify all imports from spec Hello World work."""
