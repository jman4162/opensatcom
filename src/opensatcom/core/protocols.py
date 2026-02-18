"""Protocol definitions for OpenSatCom public interfaces.

All pluggable components implement these ``typing.Protocol`` interfaces.
Use ``runtime_checkable`` protocols for isinstance checks at configuration time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np

if TYPE_CHECKING:
    from opensatcom.core.models import (
        LinkInputs,
        LinkOutputs,
        ModCod,
        PropagationConditions,
        StateECEF,
        Terminal,
    )


@runtime_checkable
class AntennaModel(Protocol):
    """Interface for antenna gain models.

    Implementations must provide ``gain_dbi`` (vectorised over angles)
    and ``eirp_dbw`` (scalar convenience for link budgets).
    """

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray:
        """Compute antenna gain over an array of directions.

        Parameters
        ----------
        theta_deg : numpy.ndarray
            Elevation angles in degrees.
        phi_deg : numpy.ndarray
            Azimuth angles in degrees.
        f_hz : float
            Carrier frequency in Hz.

        Returns
        -------
        numpy.ndarray
            Gain values in dBi, same shape as *theta_deg*.
        """
        ...

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float:
        """Compute EIRP toward a specific direction.

        Parameters
        ----------
        theta_deg : float
            Elevation angle in degrees.
        phi_deg : float
            Azimuth angle in degrees.
        f_hz : float
            Carrier frequency in Hz.
        tx_power_w : float
            Transmit power in watts.

        Returns
        -------
        float
            EIRP in dBW.
        """
        ...


@runtime_checkable
class PropagationModel(Protocol):
    """Interface for propagation loss models.

    Implementations compute total one-way path loss in dB for a given
    frequency, geometry, and environmental conditions.
    """

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        """Compute total path loss.

        Parameters
        ----------
        f_hz : float
            Carrier frequency in Hz.
        elev_deg : float
            Elevation angle in degrees.
        range_m : float
            Slant range in metres.
        cond : PropagationConditions
            Environmental conditions (rain, climate, availability).

        Returns
        -------
        float
            Total path loss in dB (positive value).
        """
        ...


@runtime_checkable
class PerformanceCurve(Protocol):
    """Interface for modem performance curves (Eb/N0 vs BLER).

    Maps Eb/N0 to block error rate and vice versa for a given ModCod.
    """

    def bler(self, ebn0_db: float) -> float:
        """Compute BLER at a given Eb/N0.

        Parameters
        ----------
        ebn0_db : float
            Energy-per-bit to noise-density ratio in dB.

        Returns
        -------
        float
            Block error rate (0.0 to 1.0).
        """
        ...

    def required_ebn0_db(self, target_bler: float) -> float:
        """Find the minimum Eb/N0 that achieves the target BLER.

        Parameters
        ----------
        target_bler : float
            Desired block error rate threshold.

        Returns
        -------
        float
            Required Eb/N0 in dB.
        """
        ...


@runtime_checkable
class ACMPolicy(Protocol):
    """Interface for adaptive coding and modulation selection.

    Selects the best ModCod for current channel conditions,
    optionally with hysteresis to prevent rapid switching.
    """

    def select_modcod(self, ebn0_db: float, t_s: float) -> ModCod:
        """Select a ModCod for the current Eb/N0 and time.

        Parameters
        ----------
        ebn0_db : float
            Current Eb/N0 in dB.
        t_s : float
            Current simulation time in seconds.

        Returns
        -------
        ModCod
            Selected modulation and coding scheme.
        """
        ...


@runtime_checkable
class LinkEngine(Protocol):
    """Interface for link budget evaluation.

    Computes a full snapshot link budget from geometry and link parameters.
    """

    def evaluate_snapshot(
        self,
        elev_deg: float,
        az_deg: float,
        range_m: float,
        inputs: LinkInputs,
        cond: PropagationConditions,
    ) -> LinkOutputs:
        """Evaluate a snapshot link budget.

        Parameters
        ----------
        elev_deg : float
            Elevation angle in degrees.
        az_deg : float
            Azimuth angle in degrees.
        range_m : float
            Slant range in metres.
        inputs : LinkInputs
            Link configuration (terminals, antennas, propagation, RF chain).
        cond : PropagationConditions
            Environmental conditions.

        Returns
        -------
        LinkOutputs
            Complete link budget results.
        """
        ...


@runtime_checkable
class TrajectoryProvider(Protocol):
    """Interface for satellite trajectory generation.

    Provides time-tagged ECEF states for a satellite over a simulation window.
    """

    def states_ecef(
        self, t0_s: float, t1_s: float, dt_s: float
    ) -> list[StateECEF]:
        """Generate satellite states over a time window.

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
            Satellite states at each time step.
        """
        ...


@runtime_checkable
class EnvironmentProvider(Protocol):
    """Interface for time-varying propagation conditions.

    Returns propagation conditions that may vary with time and terminal locations.
    """

    def conditions(
        self, t_s: float, terminal_a: Terminal, terminal_b: Terminal
    ) -> PropagationConditions:
        """Get propagation conditions at a given time and link geometry.

        Parameters
        ----------
        t_s : float
            Simulation time in seconds.
        terminal_a : Terminal
            First terminal (typically satellite).
        terminal_b : Terminal
            Second terminal (typically ground station).

        Returns
        -------
        PropagationConditions
            Environmental conditions at this time step.
        """
        ...
