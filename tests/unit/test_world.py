"""Tests for WorldSim Tier 1."""

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
from opensatcom.world.providers import (
    PrecomputedTrajectory,
    StaticEnvironmentProvider,
)
from opensatcom.world.sim import SimpleWorldSim


@pytest.fixture
def basic_link_inputs() -> LinkInputs:
    tx = Terminal("sat", 0.0, 0.0, 550e3)
    rx = Terminal("ut", 0.0, 0.0, 50.0, system_noise_temp_k=500.0)
    sc = Scenario("dl", "downlink", 12e9, 100e6, "RHCP", "ebn0_db", 6.0)
    ant = ParametricAntenna(gain_dbi=30.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=1.0, rx_noise_temp_k=500.0)
    return LinkInputs(tx, rx, sc, ant, ant, prop, rf)


@pytest.fixture
def synthetic_pass() -> PrecomputedTrajectory:
    """20-step synthetic pass from 5 deg to 80 deg and back."""
    n = 20
    times = np.arange(n, dtype=float)
    # Elevation: rise from 5 to 80, then back to 5
    elev = np.concatenate([
        np.linspace(5.0, 80.0, n // 2),
        np.linspace(80.0, 5.0, n // 2),
    ])
    az = np.zeros(n)
    range_m_arr = np.concatenate([
        np.linspace(1500e3, 550e3, n // 2),
        np.linspace(550e3, 1500e3, n // 2),
    ])
    return PrecomputedTrajectory.from_arrays(times, elev, az, range_m_arr)


class TestSimpleWorldSim:
    def test_ops_policy_masks_low_elevation(
        self, basic_link_inputs: LinkInputs, synthetic_pass: PrecomputedTrajectory
    ) -> None:
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = SimpleWorldSim()
        out = sim.run(basic_link_inputs, synthetic_pass, ops, env)

        # Steps at 5 deg elevation should be outages
        low_elev_mask = synthetic_pass.pass_data.elev_deg < 10.0
        assert np.all(out.outages_mask[low_elev_mask])

    def test_summary_contains_required_keys(
        self, basic_link_inputs: LinkInputs, synthetic_pass: PrecomputedTrajectory
    ) -> None:
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = SimpleWorldSim()
        out = sim.run(basic_link_inputs, synthetic_pass, ops, env)

        required_keys = {
            "availability", "outage_seconds",
            "margin_db_min", "margin_db_mean",
            "margin_db_p05", "margin_db_p50", "margin_db_p95",
            "throughput_mbps_mean",
        }
        assert required_keys.issubset(set(out.summary.keys()))

    def test_availability_calculation(
        self, basic_link_inputs: LinkInputs, synthetic_pass: PrecomputedTrajectory
    ) -> None:
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = SimpleWorldSim()
        out = sim.run(basic_link_inputs, synthetic_pass, ops, env)

        # Availability should be between 0 and 1
        assert 0.0 <= out.summary["availability"] <= 1.0
        # Some steps are below 10 deg, so availability < 1
        assert out.summary["availability"] < 1.0
        # But most steps are above 10 deg
        assert out.summary["availability"] > 0.5

    def test_all_above_min_elev(self, basic_link_inputs: LinkInputs) -> None:
        """If all elevations are above min, availability should be 1.0."""
        n = 10
        traj = PrecomputedTrajectory.from_arrays(
            times_s=np.arange(n, dtype=float),
            elev_deg=np.full(n, 45.0),
            az_deg=np.zeros(n),
            range_m=np.full(n, 800e3),
        )
        ops = OpsPolicy(min_elevation_deg=10.0)
        env = StaticEnvironmentProvider(PropagationConditions())
        sim = SimpleWorldSim()
        out = sim.run(basic_link_inputs, traj, ops, env)

        assert out.summary["availability"] == pytest.approx(1.0)
        assert not np.any(out.outages_mask)
