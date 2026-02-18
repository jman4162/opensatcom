"""Simple world simulation engine (Tier 1: single sat ↔ terminal)."""

from __future__ import annotations

import numpy as np

from opensatcom.core.models import (
    LinkInputs,
    OpsPolicy,
    WorldSimOutputs,
)
from opensatcom.link.engine import DefaultLinkEngine
from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider


class SimpleWorldSim:
    """Tier 1 world simulation: single satellite to terminal time-series.

    Evaluates a snapshot link budget at each time step along a pre-computed
    satellite pass, applying operational policy checks (minimum elevation)
    and collecting margin, throughput, and outage statistics.

    Examples
    --------
    >>> sim = SimpleWorldSim()
    >>> result = sim.run(link_inputs, trajectory, OpsPolicy(), env)
    >>> result.summary["availability"]
    0.95
    """

    def __init__(self) -> None:
        self._engine = DefaultLinkEngine()

    def run(
        self,
        link_inputs: LinkInputs,
        trajectory: PrecomputedTrajectory,
        ops: OpsPolicy,
        env: StaticEnvironmentProvider,
    ) -> WorldSimOutputs:
        """Run the Tier 1 simulation over a satellite pass.

        Parameters
        ----------
        link_inputs : LinkInputs
            Link configuration (terminals, antennas, propagation, RF chain).
        trajectory : PrecomputedTrajectory
            Pre-computed satellite trajectory with elevation, azimuth,
            and range arrays.
        ops : OpsPolicy
            Operational constraints (min elevation, max scan angle).
        env : StaticEnvironmentProvider
            Environment provider for propagation conditions at each step.

        Returns
        -------
        WorldSimOutputs
            Time-series results with margin, throughput, outage mask,
            and scalar summary statistics.
        """
        pd = trajectory.pass_data
        n_steps = len(pd.times_s)

        margins = np.zeros(n_steps)
        throughputs = np.zeros(n_steps)
        outages = np.zeros(n_steps, dtype=bool)
        modcod_names: list[str] = []
        breakdown_ts: dict[str, np.ndarray] = {}

        for i in range(n_steps):
            elev = float(pd.elev_deg[i])
            az = float(pd.az_deg[i])
            rng = float(pd.range_m[i])
            t = float(pd.times_s[i])

            # Ops policy check
            if elev < ops.min_elevation_deg:
                outages[i] = True
                margins[i] = float("nan")
                throughputs[i] = 0.0
                modcod_names.append("")
                continue

            cond = env.conditions(t, link_inputs.tx_terminal, link_inputs.rx_terminal)
            out = self._engine.evaluate_snapshot(elev, az, rng, link_inputs, cond)

            margins[i] = out.margin_db
            if out.margin_db < 0:
                outages[i] = True

            if out.throughput_mbps is not None:
                throughputs[i] = out.throughput_mbps
            else:
                throughputs[i] = 0.0

            if out.breakdown is not None:
                modcod_names.append(
                    out.breakdown.get("selected_modcod", "")  # type: ignore[arg-type]
                    if "selected_modcod" in out.breakdown
                    else ""
                )
            else:
                modcod_names.append("")

            # Collect breakdown time-series
            if out.breakdown is not None:
                for key, val in out.breakdown.items():
                    if key not in breakdown_ts:
                        breakdown_ts[key] = np.full(n_steps, float("nan"))
                    breakdown_ts[key][i] = val

        # Compute summary
        valid_mask = ~outages
        n_valid = int(np.sum(valid_mask))
        dt_s = float(pd.times_s[1] - pd.times_s[0]) if n_steps > 1 else 1.0
        outage_seconds = float(np.sum(outages)) * dt_s
        availability = n_valid / n_steps if n_steps > 0 else 0.0

        valid_margins = margins[valid_mask] if n_valid > 0 else np.array([0.0])

        summary: dict[str, float] = {
            "availability": availability,
            "outage_seconds": outage_seconds,
            "margin_db_min": float(np.nanmin(valid_margins)) if n_valid > 0 else 0.0,
            "margin_db_mean": float(np.nanmean(valid_margins)) if n_valid > 0 else 0.0,
            "margin_db_p05": float(np.nanpercentile(valid_margins, 5)) if n_valid > 0 else 0.0,
            "margin_db_p50": float(np.nanpercentile(valid_margins, 50)) if n_valid > 0 else 0.0,
            "margin_db_p95": float(np.nanpercentile(valid_margins, 95)) if n_valid > 0 else 0.0,
            "throughput_mbps_mean": float(np.mean(throughputs[valid_mask])) if n_valid > 0 else 0.0,
        }

        return WorldSimOutputs(
            times_s=pd.times_s,
            elev_deg=pd.elev_deg,
            range_m=pd.range_m,
            margin_db=margins,
            throughput_mbps=throughputs if link_inputs.modem is not None else None,
            selected_modcod=modcod_names if link_inputs.modem is not None else None,
            outages_mask=outages,
            summary=summary,
            breakdown_timeseries=breakdown_ts if breakdown_ts else None,
        )
