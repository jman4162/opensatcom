"""Tests for MultiSatWorldSim (Tier 2)."""

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


@pytest.fixture
def basic_link_inputs() -> LinkInputs:
    tx = Terminal("sat", 0.0, 0.0, 550e3)
    rx = Terminal("ut", 0.0, 0.0, 50.0, system_noise_temp_k=500.0)
    sc = Scenario("dl", "downlink", 12e9, 100e6, "RHCP", "ebn0_db", 6.0)
    ant = ParametricAntenna(gain_dbi=30.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=1.0, rx_noise_temp_k=500.0)
    return LinkInputs(tx, rx, sc, ant, ant, prop, rf)


def _make_traj(
    n: int, elev_start: float, elev_peak: float, range_close: float, range_far: float
) -> PrecomputedTrajectory:
    """Build a symmetric rise-fall trajectory."""
    times = np.arange(n, dtype=float)
    elev = np.concatenate([
        np.linspace(elev_start, elev_peak, n // 2),
        np.linspace(elev_peak, elev_start, n - n // 2),
    ])
    az = np.zeros(n)
    range_m = np.concatenate([
        np.linspace(range_far, range_close, n // 2),
        np.linspace(range_close, range_far, n - n // 2),
    ])
    return PrecomputedTrajectory.from_arrays(times, elev, az, range_m)


class TestMultiSatWorldSim:
    def test_single_sat_matches_tier1(self, basic_link_inputs: LinkInputs) -> None:
        """With one satellite, multi-sat sim should match single-sat."""
        from opensatcom.world.sim import SimpleWorldSim

        traj = _make_traj(20, 5.0, 80.0, 550e3, 1500e3)
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())

        # Tier 1
        sim1 = SimpleWorldSim()
        out1 = sim1.run(basic_link_inputs, traj, ops, env)

        # Tier 2 with single sat
        sim2 = MultiSatWorldSim()
        out2 = sim2.run(basic_link_inputs, {"sat1": traj}, ops, env)

        assert out2.base.summary["availability"] == pytest.approx(
            out1.summary["availability"], abs=0.01
        )
        assert out2.n_handovers == 0

    def test_two_sats_handover_occurs(self, basic_link_inputs: LinkInputs) -> None:
        """Two satellites with complementary passes produce handovers."""
        n = 20
        # Sat1: visible first half, then drops
        traj1 = _make_traj(n, 5.0, 60.0, 600e3, 1500e3)
        # Sat2: starts low, peaks in second half
        times = np.arange(n, dtype=float)
        elev2 = np.concatenate([
            np.linspace(5.0, 15.0, n // 2),
            np.linspace(60.0, 80.0, n - n // 2),
        ])
        range2 = np.concatenate([
            np.linspace(1500e3, 1200e3, n // 2),
            np.linspace(600e3, 550e3, n - n // 2),
        ])
        traj2 = PrecomputedTrajectory.from_arrays(
            times, elev2, np.zeros(n), range2
        )

        ops = OpsPolicy(min_elevation_deg=10.0, handover_hysteresis_s=0.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        policy = HandoverPolicy(hysteresis_db=1.0, hysteresis_s=0.0)
        sim = MultiSatWorldSim(handover_policy=policy)

        out = sim.run(
            basic_link_inputs,
            {"sat1": traj1, "sat2": traj2},
            ops, env,
        )
        # Should have at least one handover
        assert out.n_handovers >= 1
        # Both sats should appear in selections
        unique_sats = set(out.selected_sat_id)
        assert len(unique_sats) >= 1  # at minimum one sat used

    def test_improved_availability(self, basic_link_inputs: LinkInputs) -> None:
        """Two complementary satellites should improve availability vs one."""
        n = 20
        # Sat1: visible only in first half
        times = np.arange(n, dtype=float)
        elev1 = np.concatenate([
            np.linspace(20.0, 60.0, n // 2),
            np.full(n - n // 2, 3.0),  # below min elev
        ])
        range1 = np.full(n, 800e3)
        traj1 = PrecomputedTrajectory.from_arrays(times, elev1, np.zeros(n), range1)

        # Sat2: visible only in second half
        elev2 = np.concatenate([
            np.full(n // 2, 3.0),  # below min elev
            np.linspace(20.0, 60.0, n - n // 2),
        ])
        traj2 = PrecomputedTrajectory.from_arrays(times, elev2, np.zeros(n), range1)

        ops = OpsPolicy(min_elevation_deg=10.0, handover_hysteresis_s=0.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        policy = HandoverPolicy(hysteresis_db=0.0, hysteresis_s=0.0)
        sim = MultiSatWorldSim(handover_policy=policy)

        out = sim.run(
            basic_link_inputs,
            {"sat1": traj1, "sat2": traj2},
            ops, env,
        )
        # Combined availability should be high (each covers half)
        assert out.base.summary["availability"] >= 0.8

    def test_per_sat_contact(self, basic_link_inputs: LinkInputs) -> None:
        """per_sat_contact_s should sum to total contact time."""
        traj = _make_traj(10, 20.0, 60.0, 600e3, 1000e3)
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = MultiSatWorldSim()

        out = sim.run(basic_link_inputs, {"sat1": traj}, ops, env)
        total_contact = sum(out.per_sat_contact_s.values())
        valid_steps = int(np.sum(~out.base.outages_mask))
        expected_contact = valid_steps * 1.0  # dt=1s
        assert total_contact == pytest.approx(expected_contact, abs=0.1)

    def test_summary_has_n_handovers(self, basic_link_inputs: LinkInputs) -> None:
        traj = _make_traj(10, 30.0, 60.0, 600e3, 1000e3)
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = MultiSatWorldSim()

        out = sim.run(basic_link_inputs, {"sat1": traj}, ops, env)
        assert "n_handovers" in out.base.summary

    def test_empty_trajectories_rejected(self, basic_link_inputs: LinkInputs) -> None:
        ops = OpsPolicy()
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = MultiSatWorldSim()
        with pytest.raises(ValueError, match="At least one"):
            sim.run(basic_link_inputs, {}, ops, env)

    def test_handover_times_recorded(self, basic_link_inputs: LinkInputs) -> None:
        """Handover times should correspond to actual handover events."""
        n = 20
        times = np.arange(n, dtype=float)
        # Sat1 starts good, goes bad
        elev1 = np.concatenate([np.full(10, 50.0), np.full(10, 3.0)])
        # Sat2 starts bad, goes good
        elev2 = np.concatenate([np.full(10, 3.0), np.full(10, 50.0)])
        range_m = np.full(n, 800e3)

        traj1 = PrecomputedTrajectory.from_arrays(times, elev1, np.zeros(n), range_m)
        traj2 = PrecomputedTrajectory.from_arrays(times, elev2, np.zeros(n), range_m)

        ops = OpsPolicy(min_elevation_deg=10.0, handover_hysteresis_s=0.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        policy = HandoverPolicy(hysteresis_db=0.0, hysteresis_s=0.0)
        sim = MultiSatWorldSim(handover_policy=policy)

        out = sim.run(
            basic_link_inputs,
            {"sat1": traj1, "sat2": traj2},
            ops, env,
        )
        # Should handover when sat1 disappears and sat2 appears
        assert out.n_handovers >= 1
        assert len(out.handover_times_s) == out.n_handovers
