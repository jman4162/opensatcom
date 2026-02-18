"""Core datamodels for OpenSatCom."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from opensatcom.core.protocols import (
        AntennaModel,
        EnvironmentProvider,
        PropagationModel,
        TrajectoryProvider,
    )


@dataclass(frozen=True)
class Terminal:
    """Ground or space terminal."""

    name: str
    lat_deg: float
    lon_deg: float
    alt_m: float
    system_noise_temp_k: float | None = None
    misc: dict[str, Any] | None = None


@dataclass(frozen=True)
class Scenario:
    """Link scenario definition."""

    name: str
    direction: str  # "uplink" or "downlink"
    freq_hz: float
    bandwidth_hz: float
    polarization: str  # "RHCP", "LHCP", "H", "V"
    required_metric: str  # "ebn0_db", "cn0_dbhz", "throughput_mbps"
    required_value: float
    misc: dict[str, Any] | None = None


@dataclass(frozen=True)
class PropagationConditions:
    """Environmental conditions affecting propagation."""

    availability_target: float | None = None
    rain_rate_mm_per_hr: float | None = None
    climate_region: str | None = None
    misc: dict[str, Any] | None = None


@dataclass(frozen=True)
class ModCod:
    """Modulation and coding scheme."""

    name: str
    bits_per_symbol: float
    code_rate: float
    rolloff: float = 0.2
    pilot_overhead: float = 0.0
    impl_margin_db: float = 0.0

    def net_spectral_eff_bps_per_hz(self) -> float:
        """Net spectral efficiency accounting for rolloff, pilots, and coding."""
        return (
            self.bits_per_symbol
            * self.code_rate
            * (1.0 - self.pilot_overhead)
            / (1.0 + self.rolloff)
        )


@dataclass(frozen=True)
class StateECEF:
    """Time-tagged satellite state in ECEF coordinates."""

    t_s: float
    r_m: np.ndarray  # shape (3,)
    v_mps: np.ndarray | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StateECEF):
            return NotImplemented
        return (
            self.t_s == other.t_s
            and np.array_equal(self.r_m, other.r_m)
            and (
                (self.v_mps is None and other.v_mps is None)
                or (
                    self.v_mps is not None
                    and other.v_mps is not None
                    and np.array_equal(self.v_mps, other.v_mps)
                )
            )
        )

    def __hash__(self) -> int:
        return hash((self.t_s, self.r_m.tobytes()))


@dataclass(frozen=True)
class OpsPolicy:
    """Operational policy constraints."""

    min_elevation_deg: float = 10.0
    max_scan_deg: float = 60.0
    handover_hysteresis_s: float = 5.0


@dataclass(frozen=True)
class LinkInputs:
    """Inputs to a snapshot link budget evaluation."""

    tx_terminal: Terminal
    rx_terminal: Terminal
    scenario: Scenario
    tx_antenna: AntennaModel
    rx_antenna: AntennaModel
    propagation: PropagationModel
    rf_chain: RFChainModel
    modem: Any | None = None  # ModemModel, optional to avoid circular import


@dataclass(frozen=True)
class LinkOutputs:
    """Outputs from a snapshot link budget evaluation."""

    eirp_dbw: float
    gt_dbk: float
    path_loss_db: float
    cn0_dbhz: float
    ebn0_db: float
    margin_db: float
    throughput_mbps: float | None = None
    interference_dbw: float | None = None
    sinr_db: float | None = None
    breakdown: dict[str, float] | None = None


@dataclass(frozen=True)
class RFChainModel:
    """RF chain parameters for TX and RX paths."""

    tx_power_w: float
    tx_losses_db: float
    rx_noise_temp_k: float
    misc: dict[str, Any] | None = None

    def effective_tx_power_w(self) -> float:
        """TX power after losses, in watts."""
        from opensatcom.core.units import db10_to_lin

        return self.tx_power_w * db10_to_lin(-self.tx_losses_db)

    def effective_tx_power_dbw(self) -> float:
        """TX power after losses, in dBW."""
        from opensatcom.core.units import w_to_dbw

        return w_to_dbw(self.tx_power_w) - self.tx_losses_db

    def system_temp_k(self, base_temp_k: float) -> float:
        """Total system noise temperature."""
        return base_temp_k + self.rx_noise_temp_k


@dataclass(frozen=True)
class WorldSimInputs:
    """Inputs to a world/mission simulation."""

    link_inputs: LinkInputs
    sat_traj: TrajectoryProvider
    ops: OpsPolicy
    env: EnvironmentProvider
    t0_s: float
    t1_s: float
    dt_s: float


@dataclass(frozen=True)
class WorldSimOutputs:
    """Outputs from a world/mission simulation."""

    times_s: np.ndarray
    elev_deg: np.ndarray
    range_m: np.ndarray
    margin_db: np.ndarray
    throughput_mbps: np.ndarray | None
    selected_modcod: list[str] | None
    outages_mask: np.ndarray
    summary: dict[str, float]
    breakdown_timeseries: dict[str, np.ndarray] | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorldSimOutputs):
            return NotImplemented
        return self.summary == other.summary

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.summary.items())))
