"""Golden test for mission simulation with synthetic 20-step pass."""

import numpy as np
import pytest

from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.models import (
    LinkInputs,
    OpsPolicy,
    PropagationConditions,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation
from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider
from opensatcom.world.sim import SimpleWorldSim


@pytest.mark.golden
class TestMissionGolden:
    def test_synthetic_20_step_pass(self) -> None:
        """Frozen summary metrics for a synthetic 20-step pass."""
        tx = Terminal("sat", 0.0, 0.0, 550e3)
        rx = Terminal("ut", 0.0, 0.0, 50.0, system_noise_temp_k=500.0)
        sc = Scenario("dl", "downlink", 12e9, 100e6, "RHCP", "ebn0_db", 6.0)
        ant = ParametricAntenna(gain_dbi=30.0)
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = RFChainModel(tx_power_w=100.0, tx_losses_db=1.0, rx_noise_temp_k=500.0)
        inputs = LinkInputs(tx, rx, sc, ant, ant, prop, rf)

        n = 20
        times = np.arange(n, dtype=float)
        elev = np.concatenate([
            np.linspace(5.0, 80.0, n // 2),
            np.linspace(80.0, 5.0, n // 2),
        ])
        az = np.zeros(n)
        range_m = np.concatenate([
            np.linspace(1500e3, 550e3, n // 2),
            np.linspace(550e3, 1500e3, n // 2),
        ])
        traj = PrecomputedTrajectory.from_arrays(times, elev, az, range_m)

        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())

        sim = SimpleWorldSim()
        out = sim.run(inputs, traj, ops, env)

        # Frozen golden summary values
        # 2 out of 20 steps below 10 deg (first and last)
        assert out.summary["availability"] == pytest.approx(0.9, abs=0.05)
        assert out.summary["outage_seconds"] == pytest.approx(2.0, abs=1.0)

        # All valid margins should be positive (link closes)
        assert out.summary["margin_db_min"] > 0.0
        assert out.summary["margin_db_mean"] > 0.0
        assert out.summary["margin_db_p50"] > 0.0

        # Margin at zenith (close range) should be higher than at low elev
        valid_margins = out.margin_db[~out.outages_mask]
        assert np.nanmax(valid_margins) > np.nanmin(valid_margins)
