"""Network-level world simulation (Tier 3) with traffic scheduling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from opensatcom.core.models import (
    LinkInputs,
    OpsPolicy,
)
from opensatcom.link.engine import DefaultLinkEngine
from opensatcom.world.multisim import MultiSatWorldSim, MultiSatWorldSimOutputs
from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider
from opensatcom.world.scheduler import ProportionalFairScheduler, RoundRobinScheduler
from opensatcom.world.traffic import TrafficProfile


@dataclass
class NetworkSimOutputs:
    """Outputs from network-level simulation, extends MultiSatWorldSimOutputs.

    Parameters
    ----------
    base : MultiSatWorldSimOutputs
        Underlying multi-satellite simulation outputs.
    per_user_throughput_mbps : dict[str, np.ndarray]
        Allocated throughput (Mbps) time-series per user ID.
    total_capacity_mbps : np.ndarray
        Total available link capacity (Mbps) at each timestep.
    user_satisfaction : dict[str, float]
        Fraction of total demand served over the simulation, per user ID
        (0.0 = none served, 1.0 = fully served).
    """

    base: MultiSatWorldSimOutputs
    per_user_throughput_mbps: dict[str, np.ndarray]
    total_capacity_mbps: np.ndarray
    user_satisfaction: dict[str, float]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NetworkSimOutputs):
            return NotImplemented
        return self.base == other.base

    def __hash__(self) -> int:
        return hash(self.base)


class NetworkWorldSim:
    """Tier 3 world simulation: multi-satellite with traffic scheduling.

    At each timestep:
    1. Evaluate link per satellite (via MultiSatWorldSim)
    2. Compute available capacity from link margin + modem
    3. Schedule traffic across users based on demand and capacity
    4. Record per-user throughput and satisfaction metrics

    Parameters
    ----------
    scheduler : str
        Scheduler type: "proportional_fair" (default) or "round_robin".
    """

    def __init__(self, scheduler: str = "proportional_fair") -> None:
        self._scheduler: ProportionalFairScheduler | RoundRobinScheduler
        if scheduler == "round_robin":
            self._scheduler = RoundRobinScheduler()
        else:
            self._scheduler = ProportionalFairScheduler()
        self._engine = DefaultLinkEngine()

    def run(
        self,
        link_inputs: LinkInputs,
        trajectories: dict[str, PrecomputedTrajectory],
        ops: OpsPolicy,
        env: StaticEnvironmentProvider,
        traffic_profile: TrafficProfile,
    ) -> NetworkSimOutputs:
        """Run network simulation with traffic scheduling.

        Parameters
        ----------
        link_inputs : LinkInputs
            Base link inputs (antenna, RF chain, scenario).
        trajectories : dict[str, PrecomputedTrajectory]
            Satellite trajectories keyed by satellite ID.
        ops : OpsPolicy
            Operational policy with min elevation and handover hysteresis.
        env : StaticEnvironmentProvider
            Environment conditions provider.
        traffic_profile : TrafficProfile
            Time-varying traffic demand profile for all users.

        Returns
        -------
        NetworkSimOutputs
            Network-level outputs including per-user throughput allocation
            and satisfaction metrics.
        """
        # First run the multi-sat sim to get link-level results
        multi_sim = MultiSatWorldSim()
        multi_out = multi_sim.run(link_inputs, trajectories, ops, env)

        base_out = multi_out.base
        n_steps = len(base_out.times_s)

        # Determine capacity from margin/throughput at each step
        total_capacity = np.zeros(n_steps)
        bw_hz = link_inputs.scenario.bandwidth_hz

        # Re-evaluate each timestep to get actual Eb/N0 for capacity estimation
        for i in range(n_steps):
            if base_out.outages_mask[i]:
                total_capacity[i] = 0.0
                continue

            # Use throughput if modem is available, else estimate from Eb/N0
            if base_out.throughput_mbps is not None and base_out.throughput_mbps[i] > 0:
                total_capacity[i] = base_out.throughput_mbps[i]
            else:
                # Compute actual Eb/N0 from margin + required value
                actual_ebn0_db = base_out.margin_db[i] + link_inputs.scenario.required_value
                if np.isnan(actual_ebn0_db):
                    total_capacity[i] = 0.0
                else:
                    ebn0_lin = 10.0 ** (actual_ebn0_db / 10.0)
                    capacity_bps = bw_hz * np.log2(1.0 + ebn0_lin)
                    total_capacity[i] = capacity_bps / 1e6

        # Collect all user IDs from traffic profile
        sample_demands = traffic_profile.demands_at(float(base_out.times_s[0]))
        user_ids = [d.user_id for d in sample_demands]

        per_user_throughput: dict[str, np.ndarray] = {
            uid: np.zeros(n_steps) for uid in user_ids
        }

        # Schedule traffic at each timestep
        for i in range(n_steps):
            t_s = float(base_out.times_s[i])
            demands = traffic_profile.demands_at(t_s)
            cap = total_capacity[i]

            allocation = self._scheduler.allocate(demands, cap)
            for uid, allocated in allocation.items():
                if uid in per_user_throughput:
                    per_user_throughput[uid][i] = allocated

        # Compute satisfaction: fraction of demand met over simulation
        user_satisfaction: dict[str, float] = {}
        for uid in user_ids:
            total_demand = 0.0
            total_served = 0.0
            for i in range(n_steps):
                t_s = float(base_out.times_s[i])
                demands = traffic_profile.demands_at(t_s)
                for d in demands:
                    if d.user_id == uid:
                        total_demand += d.demand_mbps
                        total_served += per_user_throughput[uid][i]
                        break
            user_satisfaction[uid] = total_served / total_demand if total_demand > 0 else 0.0

        return NetworkSimOutputs(
            base=multi_out,
            per_user_throughput_mbps=per_user_throughput,
            total_capacity_mbps=total_capacity,
            user_satisfaction=user_satisfaction,
        )
