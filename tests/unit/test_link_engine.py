"""Tests for the link budget engine."""


import pytest

from opensatcom.antenna.pam import PamArrayAntenna
from opensatcom.antenna.parametric import ParametricAntenna
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


@pytest.fixture
def hello_world_inputs() -> LinkInputs:
    """Hello World fixture matching spec Section 24."""
    tx = Terminal("sat", 0.0, 0.0, 550e3)
    rx = Terminal("ut", 47.6062, -122.3321, 50.0, system_noise_temp_k=500.0)
    sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
    tx_ant = PamArrayAntenna(nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5)
    rx_ant = ParametricAntenna(gain_dbi=35.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=500.0)
    return LinkInputs(tx, rx, sc, tx_ant, rx_ant, prop, rf)


class TestDefaultLinkEngine:
    def test_positive_margin(self, hello_world_inputs: LinkInputs) -> None:
        engine = DefaultLinkEngine()
        out = engine.evaluate_snapshot(
            elev_deg=30.0, az_deg=0.0, range_m=1200e3,
            inputs=hello_world_inputs, cond=PropagationConditions(),
        )
        assert out.margin_db > 0.0

    def test_physically_plausible_values(self, hello_world_inputs: LinkInputs) -> None:
        engine = DefaultLinkEngine()
        out = engine.evaluate_snapshot(
            elev_deg=30.0, az_deg=0.0, range_m=1200e3,
            inputs=hello_world_inputs, cond=PropagationConditions(),
        )
        # EIRP should be reasonable (dBW range 20-70)
        assert 20.0 < out.eirp_dbw < 70.0
        # C/N0 should be positive
        assert out.cn0_dbhz > 50.0
        # Path loss should be substantial
        assert out.path_loss_db > 150.0
        # G/T should be reasonable
        assert out.gt_dbk > 0.0

    def test_complete_breakdown(self, hello_world_inputs: LinkInputs) -> None:
        engine = DefaultLinkEngine()
        out = engine.evaluate_snapshot(
            elev_deg=30.0, az_deg=0.0, range_m=1200e3,
            inputs=hello_world_inputs, cond=PropagationConditions(),
        )
        assert out.breakdown is not None
        expected_keys = {
            "tx_power_dbw", "tx_losses_db", "tx_antenna_gain_dbi",
            "eirp_dbw", "fspl_db", "rain_db", "gas_db", "pointing_db",
            "rx_antenna_gain_dbi", "rx_system_temp_k",
            "cn0_dbhz", "ebn0_db", "margin_db",
        }
        assert set(out.breakdown.keys()) == expected_keys

    def test_uses_terminal_system_temp(self) -> None:
        """Terminal system_noise_temp_k should override rf.rx_noise_temp_k."""
        tx = Terminal("sat", 0.0, 0.0, 550e3)
        rx_with_temp = Terminal("ut", 0.0, 0.0, 50.0, system_noise_temp_k=300.0)
        rx_without_temp = Terminal("ut", 0.0, 0.0, 50.0)
        sc = Scenario("dl", "downlink", 12e9, 100e6, "RHCP", "ebn0_db", 6.0)
        ant = ParametricAntenna(gain_dbi=30.0)
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = RFChainModel(tx_power_w=100.0, tx_losses_db=1.0, rx_noise_temp_k=500.0)

        inputs_with = LinkInputs(tx, rx_with_temp, sc, ant, ant, prop, rf)
        inputs_without = LinkInputs(tx, rx_without_temp, sc, ant, ant, prop, rf)

        engine = DefaultLinkEngine()
        cond = PropagationConditions()
        out_with = engine.evaluate_snapshot(30.0, 0.0, 1000e3, inputs_with, cond)
        out_without = engine.evaluate_snapshot(30.0, 0.0, 1000e3, inputs_without, cond)

        assert out_with.breakdown is not None
        assert out_without.breakdown is not None
        assert out_with.breakdown["rx_system_temp_k"] == 300.0
        assert out_without.breakdown["rx_system_temp_k"] == 500.0
        # Lower noise temp → higher C/N0
        assert out_with.cn0_dbhz > out_without.cn0_dbhz
