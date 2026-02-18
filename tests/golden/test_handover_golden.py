"""Golden tests for multi-satellite handover — frozen reference values."""

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
from opensatcom.world.handover import HandoverPolicy
from opensatcom.world.multisim import MultiSatWorldSim
from opensatcom.world.providers import (
    PrecomputedTrajectory,
    StaticEnvironmentProvider,
)


def _link_inputs() -> LinkInputs:
    tx = Terminal("sat", 0.0, 0.0, 550e3)
    rx = Terminal("ut", 0.0, 0.0, 50.0, system_noise_temp_k=500.0)
    sc = Scenario("dl", "downlink", 12e9, 100e6, "RHCP", "ebn0_db", 6.0)
    ant = ParametricAntenna(gain_dbi=30.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=1.0, rx_noise_temp_k=500.0)
    return LinkInputs(tx, rx, sc, ant, ant, prop, rf)


class TestHandoverGolden:
    def test_complementary_sats_handover_count(self) -> None:
        """Two complementary satellites: exactly 1 handover.

        Sat1 visible steps 0-9 (50° elev), invisible 10-19 (3°).
        Sat2 invisible steps 0-9 (3°), visible 10-19 (50°).
        Expected: 1 handover at step 10.
        """
        n = 20
        times = np.arange(n, dtype=float)
        elev1 = np.concatenate([np.full(10, 50.0), np.full(10, 3.0)])
        elev2 = np.concatenate([np.full(10, 3.0), np.full(10, 50.0)])
        range_m = np.full(n, 800e3)

        traj1 = PrecomputedTrajectory.from_arrays(times, elev1, np.zeros(n), range_m)
        traj2 = PrecomputedTrajectory.from_arrays(times, elev2, np.zeros(n), range_m)

        li = _link_inputs()
        ops = OpsPolicy(min_elevation_deg=10.0, handover_hysteresis_s=0.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        policy = HandoverPolicy(hysteresis_db=0.0, hysteresis_s=0.0)
        sim = MultiSatWorldSim(handover_policy=policy)

        out = sim.run(li, {"sat1": traj1, "sat2": traj2}, ops, env)
        assert out.n_handovers == 1
        assert out.handover_times_s[0] == pytest.approx(10.0)
        assert out.base.summary["availability"] == pytest.approx(1.0)

    def test_full_coverage_availability(self) -> None:
        """Three overlapping satellites should achieve 100% availability.

        All sats at 45° elevation, 800 km range, all visible.
        """
        n = 10
        times = np.arange(n, dtype=float)
        elev = np.full(n, 45.0)
        az = np.zeros(n)
        range_m = np.full(n, 800e3)

        trajs = {}
        for sid in ["sat1", "sat2", "sat3"]:
            trajs[sid] = PrecomputedTrajectory.from_arrays(times, elev, az, range_m)

        li = _link_inputs()
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = MultiSatWorldSim()

        out = sim.run(li, trajs, ops, env)
        assert out.base.summary["availability"] == pytest.approx(1.0)
        assert out.n_handovers == 0  # No reason to handover, all identical
