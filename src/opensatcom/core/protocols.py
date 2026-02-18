"""Protocol definitions for OpenSatCom public interfaces."""

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
    """Interface for antenna gain models."""

    def gain_dbi(
        self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float
    ) -> np.ndarray: ...

    def eirp_dbw(
        self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float
    ) -> float: ...


@runtime_checkable
class PropagationModel(Protocol):
    """Interface for propagation loss models."""

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float: ...


@runtime_checkable
class PerformanceCurve(Protocol):
    """Interface for modem performance curves (Eb/N0 vs BLER)."""

    def bler(self, ebn0_db: float) -> float: ...

    def required_ebn0_db(self, target_bler: float) -> float: ...


@runtime_checkable
class ACMPolicy(Protocol):
    """Interface for adaptive coding and modulation selection."""

    def select_modcod(self, ebn0_db: float, t_s: float) -> ModCod: ...


@runtime_checkable
class LinkEngine(Protocol):
    """Interface for link budget evaluation."""

    def evaluate_snapshot(
        self,
        elev_deg: float,
        az_deg: float,
        range_m: float,
        inputs: LinkInputs,
        cond: PropagationConditions,
    ) -> LinkOutputs: ...


@runtime_checkable
class TrajectoryProvider(Protocol):
    """Interface for satellite trajectory generation."""

    def states_ecef(
        self, t0_s: float, t1_s: float, dt_s: float
    ) -> list[StateECEF]: ...


@runtime_checkable
class EnvironmentProvider(Protocol):
    """Interface for time-varying propagation conditions."""

    def conditions(
        self, t_s: float, terminal_a: Terminal, terminal_b: Terminal
    ) -> PropagationConditions: ...
