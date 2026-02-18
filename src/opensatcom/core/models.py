"""Core datamodels for OpenSatCom.

Frozen dataclasses representing terminals, scenarios, link budget inputs/outputs,
RF chain parameters, and world simulation state. All fields use SI units internally;
dB-domain fields are explicitly named (e.g., ``eirp_dbw``, ``cn0_dbhz``).
"""

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
    """Ground or space terminal.

    Parameters
    ----------
    name : str
        Human-readable terminal identifier (e.g., ``"GEO-Sat"``).
    lat_deg : float
        Geodetic latitude in degrees (positive north).
    lon_deg : float
        Geodetic longitude in degrees (positive east).
    alt_m : float
        Altitude above mean sea level in metres. For GEO satellites
        use ``35_786_000.0``.
    system_noise_temp_k : float or None
        System noise temperature in Kelvin. Required for receive terminals.
    misc : dict or None
        Arbitrary metadata attached to the terminal.
    """

    name: str
    lat_deg: float
    lon_deg: float
    alt_m: float
    system_noise_temp_k: float | None = None
    misc: dict[str, Any] | None = None


@dataclass(frozen=True)
class Scenario:
    """Link scenario definition.

    Parameters
    ----------
    name : str
        Scenario identifier (e.g., ``"Ku-DL"``).
    direction : str
        ``"uplink"`` or ``"downlink"``.
    freq_hz : float
        Carrier frequency in Hz.
    bandwidth_hz : float
        Allocated bandwidth in Hz.
    polarization : str
        Polarization type: ``"RHCP"``, ``"LHCP"``, ``"H"``, or ``"V"``.
    required_metric : str
        Performance metric to evaluate: ``"ebn0_db"``, ``"cn0_dbhz"``,
        or ``"throughput_mbps"``.
    required_value : float
        Minimum required value of the metric.
    misc : dict or None
        Arbitrary metadata.
    """

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
    """Environmental conditions affecting propagation.

    Parameters
    ----------
    availability_target : float or None
        Link availability target as a fraction (e.g., ``0.999`` for 99.9 %).
    rain_rate_mm_per_hr : float or None
        Point rain rate exceeded at the availability target, in mm/h.
    climate_region : str or None
        ITU-R climate region letter (``"A"`` through ``"Q"``).
    misc : dict or None
        Arbitrary metadata.
    """

    availability_target: float | None = None
    rain_rate_mm_per_hr: float | None = None
    climate_region: str | None = None
    misc: dict[str, Any] | None = None


@dataclass(frozen=True)
class ModCod:
    """Modulation and coding scheme.

    Parameters
    ----------
    name : str
        ModCod identifier (e.g., ``"QPSK 1/2"``).
    bits_per_symbol : float
        Bits per symbol for the modulation (e.g., 2.0 for QPSK).
    code_rate : float
        FEC code rate as a fraction (e.g., 0.5 for rate-1/2).
    rolloff : float
        Root-raised-cosine rolloff factor (default 0.2).
    pilot_overhead : float
        Pilot symbol overhead as a fraction (default 0.0).
    impl_margin_db : float
        Implementation margin in dB (default 0.0).
    """

    name: str
    bits_per_symbol: float
    code_rate: float
    rolloff: float = 0.2
    pilot_overhead: float = 0.0
    impl_margin_db: float = 0.0

    def net_spectral_eff_bps_per_hz(self) -> float:
        """Net spectral efficiency accounting for rolloff, pilots, and coding.

        Returns
        -------
        float
            Spectral efficiency in bps/Hz.
        """
        return (
            self.bits_per_symbol
            * self.code_rate
            * (1.0 - self.pilot_overhead)
            / (1.0 + self.rolloff)
        )


@dataclass(frozen=True)
class StateECEF:
    """Time-tagged satellite state in ECEF coordinates.

    Parameters
    ----------
    t_s : float
        Epoch time in seconds since simulation start.
    r_m : numpy.ndarray
        Position vector in ECEF frame, shape ``(3,)``, in metres.
    v_mps : numpy.ndarray or None
        Velocity vector in ECEF frame, shape ``(3,)``, in m/s.
    """

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
    """Operational policy constraints.

    Parameters
    ----------
    min_elevation_deg : float
        Minimum elevation angle for link viability (default 10.0).
    max_scan_deg : float
        Maximum antenna scan angle from boresight (default 60.0).
    handover_hysteresis_s : float
        Minimum dwell time before handover in seconds (default 5.0).
    """

    min_elevation_deg: float = 10.0
    max_scan_deg: float = 60.0
    handover_hysteresis_s: float = 5.0


@dataclass(frozen=True)
class LinkInputs:
    """Inputs to a snapshot link budget evaluation.

    Parameters
    ----------
    tx_terminal : Terminal
        Transmitting terminal (satellite for downlink).
    rx_terminal : Terminal
        Receiving terminal (ground station for downlink).
    scenario : Scenario
        Link scenario definition.
    tx_antenna : AntennaModel
        Transmit antenna model.
    rx_antenna : AntennaModel
        Receive antenna model.
    propagation : PropagationModel
        Propagation loss model (e.g., FSPL or composite).
    rf_chain : RFChainModel
        RF chain parameters.
    modem : ModemModel or None
        Optional modem model for throughput computation.
    """

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
    """Outputs from a snapshot link budget evaluation.

    Parameters
    ----------
    eirp_dbw : float
        Effective isotropic radiated power in dBW.
    gt_dbk : float
        Receive figure of merit (G/T) in dB/K.
    path_loss_db : float
        Total propagation path loss in dB.
    cn0_dbhz : float
        Carrier-to-noise-density ratio in dB-Hz.
    ebn0_db : float
        Energy-per-bit to noise-density ratio in dB.
    margin_db : float
        Link margin above the required threshold in dB.
    throughput_mbps : float or None
        Achievable throughput in Mbps (when modem is enabled).
    interference_dbw : float or None
        Total interference power in dBW (multi-beam scenarios).
    sinr_db : float or None
        Signal-to-interference-plus-noise ratio in dB.
    breakdown : dict or None
        Itemised link budget breakdown (keys are parameter names,
        values in dB or dBW).
    """

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
    """RF chain parameters for TX and RX paths.

    Parameters
    ----------
    tx_power_w : float
        Transmitter output power in watts.
    tx_losses_db : float
        Total transmit-side losses in dB (cables, filters, radome).
    rx_noise_temp_k : float
        Additional receive noise temperature contribution in Kelvin.
    misc : dict or None
        Arbitrary metadata.
    """

    tx_power_w: float
    tx_losses_db: float
    rx_noise_temp_k: float
    misc: dict[str, Any] | None = None

    def effective_tx_power_w(self) -> float:
        """TX power after losses, in watts.

        Returns
        -------
        float
            Effective transmit power in watts.
        """
        from opensatcom.core.units import db10_to_lin

        return self.tx_power_w * db10_to_lin(-self.tx_losses_db)

    def effective_tx_power_dbw(self) -> float:
        """TX power after losses, in dBW.

        Returns
        -------
        float
            Effective transmit power in dBW.
        """
        from opensatcom.core.units import w_to_dbw

        return w_to_dbw(self.tx_power_w) - self.tx_losses_db

    def system_temp_k(self, base_temp_k: float) -> float:
        """Total system noise temperature.

        Parameters
        ----------
        base_temp_k : float
            Antenna noise temperature in Kelvin.

        Returns
        -------
        float
            Combined system noise temperature in Kelvin.
        """
        return base_temp_k + self.rx_noise_temp_k


@dataclass(frozen=True)
class WorldSimInputs:
    """Inputs to a world/mission simulation.

    Parameters
    ----------
    link_inputs : LinkInputs
        Link budget configuration.
    sat_traj : TrajectoryProvider
        Satellite trajectory source.
    ops : OpsPolicy
        Operational policy constraints.
    env : EnvironmentProvider
        Time-varying propagation environment.
    t0_s : float
        Simulation start time in seconds.
    t1_s : float
        Simulation end time in seconds.
    dt_s : float
        Time step in seconds.
    """

    link_inputs: LinkInputs
    sat_traj: TrajectoryProvider
    ops: OpsPolicy
    env: EnvironmentProvider
    t0_s: float
    t1_s: float
    dt_s: float


@dataclass(frozen=True)
class WorldSimOutputs:
    """Outputs from a world/mission simulation.

    Parameters
    ----------
    times_s : numpy.ndarray
        Time stamps in seconds, shape ``(N,)``.
    elev_deg : numpy.ndarray
        Elevation angles in degrees, shape ``(N,)``.
    range_m : numpy.ndarray
        Slant ranges in metres, shape ``(N,)``.
    margin_db : numpy.ndarray
        Link margin time series in dB, shape ``(N,)``.
    throughput_mbps : numpy.ndarray or None
        Throughput time series in Mbps (when modem is enabled).
    selected_modcod : list of str or None
        Selected ModCod name at each time step.
    outages_mask : numpy.ndarray
        Boolean mask where ``True`` indicates an outage, shape ``(N,)``.
    summary : dict
        Scalar summary metrics (e.g., ``availability``, ``margin_db_mean``).
    breakdown_timeseries : dict or None
        Per-parameter time series for detailed analysis.
    """

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
