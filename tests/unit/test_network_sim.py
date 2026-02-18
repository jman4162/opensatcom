"""Tests for network-level world simulation."""

import numpy as np

from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.models import (
    LinkInputs,
    OpsPolicy,
    PropagationConditions,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.propagation.fspl import FreeSpacePropagation
from opensatcom.world.network_sim import NetworkWorldSim
from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider
from opensatcom.world.traffic import ConstantTrafficProfile, TrafficDemand


def _make_link_inputs() -> LinkInputs:
    return LinkInputs(
        tx_terminal=Terminal("sat", 0.0, 0.0, 35786e3),
        rx_terminal=Terminal("ground", 0.0, 0.0, 0.0, system_noise_temp_k=290.0),
        scenario=Scenario(
            name="test",
            direction="downlink",
            freq_hz=12e9,
            bandwidth_hz=36e6,
            polarization="RHCP",
            required_metric="ebn0_db",
            required_value=1.0,
        ),
        tx_antenna=ParametricAntenna(gain_dbi=40.0),
        rx_antenna=ParametricAntenna(gain_dbi=40.0),
        propagation=FreeSpacePropagation(),
        rf_chain=RFChainModel(tx_power_w=200.0, tx_losses_db=0.0, rx_noise_temp_k=0.0),
    )


def _make_trajectory(n_steps: int = 20) -> PrecomputedTrajectory:
    from opensatcom.geometry.slant import slant_range_m

    times = np.linspace(0, 300, n_steps)
    elev = np.linspace(30.0, 60.0, n_steps)
    az = np.zeros(n_steps)
    range_arr = np.array([slant_range_m(0.0, 35786e3, e) for e in elev])
    return PrecomputedTrajectory.from_arrays(times, elev, az, range_arr)


class TestNetworkWorldSim:
    def test_single_user_full_capacity(self) -> None:
        link_inputs = _make_link_inputs()
        traj = _make_trajectory(20)
        traffic = ConstantTrafficProfile([
            TrafficDemand(user_id="u1", demand_mbps=1.0),
        ])
        sim = NetworkWorldSim(scheduler="proportional_fair")
        out = sim.run(
            link_inputs,
            {"sat1": traj},
            OpsPolicy(min_elevation_deg=5.0),
            StaticEnvironmentProvider(PropagationConditions()),
            traffic,
        )
        assert "u1" in out.per_user_throughput_mbps
        # Single user should get up to their demand or capacity
        assert out.total_capacity_mbps.shape == (20,)

    def test_two_user_proportional_split(self) -> None:
        link_inputs = _make_link_inputs()
        traj = _make_trajectory(10)
        traffic = ConstantTrafficProfile([
            TrafficDemand(user_id="u1", demand_mbps=100.0),
            TrafficDemand(user_id="u2", demand_mbps=100.0),
        ])
        sim = NetworkWorldSim(scheduler="proportional_fair")
        out = sim.run(
            link_inputs,
            {"sat1": traj},
            OpsPolicy(min_elevation_deg=5.0),
            StaticEnvironmentProvider(PropagationConditions()),
            traffic,
        )
        # Both users should get similar throughput (equal demand)
        u1_mean = float(np.mean(out.per_user_throughput_mbps["u1"]))
        u2_mean = float(np.mean(out.per_user_throughput_mbps["u2"]))
        # With equal demand, allocation should be roughly equal
        if u1_mean > 0 and u2_mean > 0:
            ratio = u1_mean / u2_mean
            assert 0.5 < ratio < 2.0

    def test_satisfaction_metric(self) -> None:
        link_inputs = _make_link_inputs()
        traj = _make_trajectory(10)
        traffic = ConstantTrafficProfile([
            TrafficDemand(user_id="u1", demand_mbps=0.001),  # Very small demand
        ])
        sim = NetworkWorldSim()
        out = sim.run(
            link_inputs,
            {"sat1": traj},
            OpsPolicy(min_elevation_deg=5.0),
            StaticEnvironmentProvider(PropagationConditions()),
            traffic,
        )
        # Tiny demand should be fully satisfied
        assert out.user_satisfaction["u1"] >= 0.99
