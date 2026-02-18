"""Multi-satellite world simulation (Tier 2) with handover."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from opensatcom.core.models import (
    LinkInputs,
    OpsPolicy,
    WorldSimOutputs,
)
from opensatcom.link.engine import DefaultLinkEngine
from opensatcom.world.handover import HandoverDecision, HandoverPolicy
from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider


@dataclass(frozen=True)
class MultiSatWorldSimOutputs:
    """Outputs from multi-satellite simulation, extends WorldSimOutputs."""

    base: WorldSimOutputs
    selected_sat_id: list[str]
    handover_times_s: list[float]
    n_handovers: int
    per_sat_contact_s: dict[str, float]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MultiSatWorldSimOutputs):
            return NotImplemented
        return self.base.summary == other.base.summary

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.base.summary.items())))


class MultiSatWorldSim:
    """Tier 2 world simulation: multiple satellites with handover.

    Evaluates link budget for each satellite at each timestep, applies
    handover policy to select serving satellite, and produces combined
    time-series output.

    Parameters
    ----------
    handover_policy : HandoverPolicy | None
        Handover policy.  Defaults to hysteresis-based with values from OpsPolicy.
    """

    def __init__(self, handover_policy: HandoverPolicy | None = None) -> None:
        self._engine = DefaultLinkEngine()
        self._policy = handover_policy

    def run(
        self,
        link_inputs: LinkInputs,
        trajectories: dict[str, PrecomputedTrajectory],
        ops: OpsPolicy,
        env: StaticEnvironmentProvider,
    ) -> MultiSatWorldSimOutputs:
        """Run multi-satellite simulation.

        Parameters
        ----------
        link_inputs : LinkInputs
            Base link inputs (shared antenna, RF chain, scenario).
        trajectories : dict[str, PrecomputedTrajectory]
            Satellite trajectories keyed by satellite ID.
        ops : OpsPolicy
            Operational policy with min elevation and handover hysteresis.
        env : StaticEnvironmentProvider
            Environment conditions provider.
        """
        if not trajectories:
            raise ValueError("At least one satellite trajectory required")

        sat_ids = list(trajectories.keys())
        n_sats = len(sat_ids)

        # Use first trajectory to determine time grid
        first_traj = trajectories[sat_ids[0]]
        times_s = first_traj.pass_data.times_s
        n_steps = len(times_s)

        # Set up handover policy
        policy = self._policy or HandoverPolicy(
            hysteresis_db=3.0,
            hysteresis_s=ops.handover_hysteresis_s,
        )
        policy.reset(initial_sat_idx=0)

        # Pre-evaluate all satellites at all timesteps
        # margins[sat_idx][step_idx] and elevations
        all_margins = np.full((n_sats, n_steps), float("nan"))
        all_elevations = np.full((n_sats, n_steps), 0.0)
        all_throughputs = np.full((n_sats, n_steps), 0.0)
        all_visible = np.zeros((n_sats, n_steps), dtype=bool)

        for s_idx, sat_id in enumerate(sat_ids):
            traj = trajectories[sat_id]
            pd = traj.pass_data
            for i in range(n_steps):
                elev = float(pd.elev_deg[i])
                az = float(pd.az_deg[i])
                rng = float(pd.range_m[i])
                t = float(pd.times_s[i])

                all_elevations[s_idx, i] = elev

                if elev < ops.min_elevation_deg:
                    all_visible[s_idx, i] = False
                    continue

                all_visible[s_idx, i] = True
                cond = env.conditions(
                    t, link_inputs.tx_terminal, link_inputs.rx_terminal
                )
                out = self._engine.evaluate_snapshot(
                    elev, az, rng, link_inputs, cond
                )
                all_margins[s_idx, i] = out.margin_db
                if out.throughput_mbps is not None:
                    all_throughputs[s_idx, i] = out.throughput_mbps

        # Run handover decision at each timestep
        selected_margins = np.zeros(n_steps)
        selected_throughputs = np.zeros(n_steps)
        selected_elevations = np.zeros(n_steps)
        selected_ranges = np.zeros(n_steps)
        outages = np.zeros(n_steps, dtype=bool)
        selected_sat_ids: list[str] = []
        handover_times: list[float] = []
        decisions: list[HandoverDecision] = []

        for i in range(n_steps):
            t = float(times_s[i])
            step_metrics = (
                [float(all_margins[s, i]) for s in range(n_sats)]
                if policy.metric == "margin"
                else [float(all_elevations[s, i]) for s in range(n_sats)]
            )
            step_visible = [bool(all_visible[s, i]) for s in range(n_sats)]

            decision = policy.evaluate(t, sat_ids, step_metrics, step_visible)
            decisions.append(decision)

            s_idx = decision.selected_sat_idx
            selected_sat_ids.append(decision.selected_sat_id)

            if decision.is_handover:
                handover_times.append(t)

            if not all_visible[s_idx, i]:
                outages[i] = True
                selected_margins[i] = float("nan")
                selected_throughputs[i] = 0.0
            else:
                margin = all_margins[s_idx, i]
                selected_margins[i] = margin
                selected_throughputs[i] = all_throughputs[s_idx, i]
                if margin < 0:
                    outages[i] = True

            traj = trajectories[sat_ids[s_idx]]
            selected_elevations[i] = float(traj.pass_data.elev_deg[i])
            selected_ranges[i] = float(traj.pass_data.range_m[i])

        # Compute summary
        valid_mask = ~outages
        n_valid = int(np.sum(valid_mask))
        dt_s = float(times_s[1] - times_s[0]) if n_steps > 1 else 1.0
        outage_seconds = float(np.sum(outages)) * dt_s
        availability = n_valid / n_steps if n_steps > 0 else 0.0

        valid_margins_arr = (
            selected_margins[valid_mask] if n_valid > 0 else np.array([0.0])
        )

        summary: dict[str, float] = {
            "availability": availability,
            "outage_seconds": outage_seconds,
            "margin_db_min": float(np.nanmin(valid_margins_arr)) if n_valid > 0 else 0.0,
            "margin_db_mean": float(np.nanmean(valid_margins_arr)) if n_valid > 0 else 0.0,
            "margin_db_p05": (
                float(np.nanpercentile(valid_margins_arr, 5)) if n_valid > 0 else 0.0
            ),
            "margin_db_p50": (
                float(np.nanpercentile(valid_margins_arr, 50)) if n_valid > 0 else 0.0
            ),
            "margin_db_p95": (
                float(np.nanpercentile(valid_margins_arr, 95)) if n_valid > 0 else 0.0
            ),
            "throughput_mbps_mean": (
                float(np.mean(selected_throughputs[valid_mask])) if n_valid > 0 else 0.0
            ),
            "n_handovers": float(len(handover_times)),
        }

        # Per-satellite contact time
        per_sat_contact: dict[str, float] = {sid: 0.0 for sid in sat_ids}
        for i, sid in enumerate(selected_sat_ids):
            if not outages[i]:
                per_sat_contact[sid] += dt_s

        base = WorldSimOutputs(
            times_s=times_s,
            elev_deg=selected_elevations,
            range_m=selected_ranges,
            margin_db=selected_margins,
            throughput_mbps=(
                selected_throughputs if link_inputs.modem is not None else None
            ),
            selected_modcod=None,
            outages_mask=outages,
            summary=summary,
        )

        return MultiSatWorldSimOutputs(
            base=base,
            selected_sat_id=selected_sat_ids,
            handover_times_s=handover_times,
            n_handovers=len(handover_times),
            per_sat_contact_s=per_sat_contact,
        )
