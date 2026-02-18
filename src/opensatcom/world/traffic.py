"""Traffic demand models for network-level simulation (Tier 3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrafficDemand:
    """Single user traffic demand at a point in time.

    Parameters
    ----------
    user_id : str
        Unique identifier for the user.
    demand_mbps : float
        Requested throughput in Mbps.
    priority : int, optional
        Scheduling priority (higher values = higher priority, default 0).
    lat_deg : float, optional
        User latitude in degrees (default 0.0).
    lon_deg : float, optional
        User longitude in degrees (default 0.0).
    alt_m : float, optional
        User altitude in meters (default 0.0).
    """

    user_id: str
    demand_mbps: float
    priority: int = 0
    lat_deg: float = 0.0
    lon_deg: float = 0.0
    alt_m: float = 0.0


class TrafficProfile:
    """Base class for time-varying traffic demand profiles."""

    def demands_at(self, t_s: float) -> list[TrafficDemand]:
        """Return traffic demands at a given simulation time.

        Parameters
        ----------
        t_s : float
            Simulation time in seconds.

        Returns
        -------
        list[TrafficDemand]
            List of per-user traffic demands at time ``t_s``.
        """
        raise NotImplementedError


class ConstantTrafficProfile(TrafficProfile):
    """Traffic profile with constant demands over time.

    Parameters
    ----------
    demands : list[TrafficDemand]
        Fixed list of user demands.
    """

    def __init__(self, demands: list[TrafficDemand]) -> None:
        self._demands = demands

    def demands_at(self, t_s: float) -> list[TrafficDemand]:
        """Return constant traffic demands regardless of time.

        Parameters
        ----------
        t_s : float
            Simulation time in seconds (unused).

        Returns
        -------
        list[TrafficDemand]
            Copy of the fixed demand list.
        """
        return list(self._demands)


class TimeVaryingTrafficProfile(TrafficProfile):
    """Traffic profile with time-varying patterns.

    Supports ramp and burst patterns per user.

    Parameters
    ----------
    base_demands : list[TrafficDemand]
        Base demand levels.
    pattern : str
        Pattern type: "ramp" (linear increase), "burst" (periodic spikes).
    ramp_factor : float
        For "ramp": max multiplier at end of simulation.
    burst_period_s : float
        For "burst": period in seconds between bursts.
    burst_multiplier : float
        For "burst": demand multiplier during burst.
    burst_duration_s : float
        For "burst": duration of each burst.
    t_start_s : float
        Simulation start time for ramp scaling.
    t_end_s : float
        Simulation end time for ramp scaling.
    """

    def __init__(
        self,
        base_demands: list[TrafficDemand],
        pattern: str = "ramp",
        ramp_factor: float = 2.0,
        burst_period_s: float = 60.0,
        burst_multiplier: float = 3.0,
        burst_duration_s: float = 10.0,
        t_start_s: float = 0.0,
        t_end_s: float = 600.0,
    ) -> None:
        self._base = base_demands
        self._pattern = pattern
        self._ramp_factor = ramp_factor
        self._burst_period_s = burst_period_s
        self._burst_multiplier = burst_multiplier
        self._burst_duration_s = burst_duration_s
        self._t_start = t_start_s
        self._t_end = t_end_s

    def demands_at(self, t_s: float) -> list[TrafficDemand]:
        """Return scaled traffic demands based on the configured pattern.

        For ``"ramp"`` pattern, demand scales linearly from 1.0 at
        ``t_start_s`` to ``ramp_factor`` at ``t_end_s``.  For ``"burst"``
        pattern, demand is multiplied by ``burst_multiplier`` during
        periodic burst windows.

        Parameters
        ----------
        t_s : float
            Simulation time in seconds.

        Returns
        -------
        list[TrafficDemand]
            Demand list with ``demand_mbps`` scaled by the time-dependent
            pattern multiplier.
        """
        if self._pattern == "ramp":
            duration = self._t_end - self._t_start
            if duration <= 0:
                scale = 1.0
            else:
                frac = min(max((t_s - self._t_start) / duration, 0.0), 1.0)
                scale = 1.0 + (self._ramp_factor - 1.0) * frac
        elif self._pattern == "burst":
            phase = (t_s % self._burst_period_s)
            scale = self._burst_multiplier if phase < self._burst_duration_s else 1.0
        else:
            scale = 1.0

        return [
            TrafficDemand(
                user_id=d.user_id,
                demand_mbps=d.demand_mbps * scale,
                priority=d.priority,
                lat_deg=d.lat_deg,
                lon_deg=d.lon_deg,
                alt_m=d.alt_m,
            )
            for d in self._base
        ]
