"""Environment and trajectory providers for WorldSim."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from opensatcom.core.models import PropagationConditions, StateECEF, Terminal


class StaticEnvironmentProvider:
    """Returns fixed propagation conditions for all timesteps."""

    def __init__(self, conditions: PropagationConditions) -> None:
        self._conditions = conditions

    def conditions(
        self, t_s: float, terminal_a: Terminal, terminal_b: Terminal
    ) -> PropagationConditions:
        return self._conditions


@dataclass(frozen=True)
class PrecomputedPassData:
    """Pre-baked pass data: arrays of time, elevation, azimuth, range."""

    times_s: np.ndarray
    elev_deg: np.ndarray
    az_deg: np.ndarray
    range_m: np.ndarray

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PrecomputedPassData):
            return NotImplemented
        return (
            np.array_equal(self.times_s, other.times_s)
            and np.array_equal(self.elev_deg, other.elev_deg)
        )

    def __hash__(self) -> int:
        return hash(self.times_s.tobytes())


class PrecomputedTrajectory:
    """Trajectory provider from pre-computed pass data.

    Stores az/el/range arrays directly — no ECEF conversion needed.
    The states_ecef method returns dummy states (the WorldSim uses
    the az/el/range directly via get_geometry).
    """

    def __init__(self, pass_data: PrecomputedPassData) -> None:
        self.pass_data = pass_data

    @classmethod
    def from_arrays(
        cls,
        times_s: np.ndarray,
        elev_deg: np.ndarray,
        az_deg: np.ndarray,
        range_m: np.ndarray,
    ) -> PrecomputedTrajectory:
        return cls(PrecomputedPassData(times_s, elev_deg, az_deg, range_m))

    def states_ecef(
        self, t0_s: float, t1_s: float, dt_s: float
    ) -> list[StateECEF]:
        """Return dummy ECEF states (not used by SimpleWorldSim)."""
        return [
            StateECEF(t_s=t, r_m=np.zeros(3))
            for t in self.pass_data.times_s
        ]

    def get_geometry(self, idx: int) -> tuple[float, float, float]:
        """Get (elev_deg, az_deg, range_m) for a given timestep index."""
        return (
            float(self.pass_data.elev_deg[idx]),
            float(self.pass_data.az_deg[idx]),
            float(self.pass_data.range_m[idx]),
        )
