"""Environment and trajectory providers for WorldSim."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from opensatcom.core.models import PropagationConditions, StateECEF, Terminal


class StaticEnvironmentProvider:
    """Returns fixed propagation conditions for all timesteps.

    Parameters
    ----------
    conditions : PropagationConditions
        Static conditions returned at every time step.
    """

    def __init__(self, conditions: PropagationConditions) -> None:
        self._conditions = conditions

    def conditions(
        self, t_s: float, terminal_a: Terminal, terminal_b: Terminal
    ) -> PropagationConditions:
        """Return the static propagation conditions.

        Parameters
        ----------
        t_s : float
            Simulation time in seconds (unused).
        terminal_a : Terminal
            First terminal (unused).
        terminal_b : Terminal
            Second terminal (unused).

        Returns
        -------
        PropagationConditions
            The fixed conditions provided at construction.
        """
        return self._conditions


@dataclass(frozen=True)
class PrecomputedPassData:
    """Pre-baked pass data: arrays of time, elevation, azimuth, range.

    Parameters
    ----------
    times_s : numpy.ndarray
        Time stamps in seconds, shape ``(N,)``.
    elev_deg : numpy.ndarray
        Elevation angles in degrees, shape ``(N,)``.
    az_deg : numpy.ndarray
        Azimuth angles in degrees, shape ``(N,)``.
    range_m : numpy.ndarray
        Slant ranges in metres, shape ``(N,)``.
    """

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
        """Construct from raw numpy arrays.

        Parameters
        ----------
        times_s : numpy.ndarray
            Time stamps in seconds.
        elev_deg : numpy.ndarray
            Elevation angles in degrees.
        az_deg : numpy.ndarray
            Azimuth angles in degrees.
        range_m : numpy.ndarray
            Slant ranges in metres.

        Returns
        -------
        PrecomputedTrajectory
            Trajectory wrapping the provided arrays.
        """
        return cls(PrecomputedPassData(times_s, elev_deg, az_deg, range_m))

    def states_ecef(
        self, t0_s: float, t1_s: float, dt_s: float
    ) -> list[StateECEF]:
        """Return dummy ECEF states (not used by SimpleWorldSim).

        Parameters
        ----------
        t0_s : float
            Start time in seconds.
        t1_s : float
            End time in seconds.
        dt_s : float
            Time step in seconds.

        Returns
        -------
        list of StateECEF
            Placeholder states with zero position vectors.
        """
        return [
            StateECEF(t_s=t, r_m=np.zeros(3))
            for t in self.pass_data.times_s
        ]

    def get_geometry(self, idx: int) -> tuple[float, float, float]:
        """Get geometry for a given timestep index.

        Parameters
        ----------
        idx : int
            Time step index into the pass data arrays.

        Returns
        -------
        tuple of (float, float, float)
            ``(elev_deg, az_deg, range_m)`` at the given index.
        """
        return (
            float(self.pass_data.elev_deg[idx]),
            float(self.pass_data.az_deg[idx]),
            float(self.pass_data.range_m[idx]),
        )
