"""YAML config loading with Pydantic v2 validation.

All configuration sections are Pydantic ``BaseModel`` subclasses loaded
from a YAML file via :func:`load_config`. Fields use SI units where
applicable and match the names used in the corresponding core datamodels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator


class ProjectSection(BaseModel):
    """Project metadata and output settings."""

    name: str
    seed: int = 42
    output_dir: str = "./runs"


class ScenarioSection(BaseModel):
    """Link scenario configuration (frequency, bandwidth, polarization)."""

    name: str
    direction: str
    freq_hz: float
    bandwidth_hz: float
    polarization: str
    required_metric: str
    required_value: float
    misc: dict[str, Any] | None = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("uplink", "downlink"):
            raise ValueError("direction must be 'uplink' or 'downlink'")
        return v


class TerminalSection(BaseModel):
    """Single terminal definition (ground station or satellite)."""

    name: str
    lat_deg: float
    lon_deg: float
    alt_m: float
    system_noise_temp_k: float | None = None


class TerminalsSection(BaseModel):
    """TX and RX terminal pair."""

    tx: TerminalSection
    rx: TerminalSection


class ParametricAntennaConfig(BaseModel):
    """Configuration for a fixed-gain parametric antenna."""

    gain_dbi: float = 0.0
    scan_loss_model: str = "none"


class PamAntennaConfig(BaseModel):
    """Configuration for a PAM phased-array antenna."""

    nx: int = 1
    ny: int = 1
    dx_lambda: float = 0.5
    dy_lambda: float = 0.5
    taper: dict[str, Any] | None = None
    steering: dict[str, Any] | None = None
    impairments: dict[str, Any] | None = None


class CouplingConfig(BaseModel):
    """EdgeFEM mutual-coupling configuration."""

    enabled: bool = False
    source: str = "edgefem"
    artifact_path: str | None = None
    metadata_path: str | None = None
    steering_az_deg: float = 0.0
    steering_el_deg: float = 0.0


class AntennaEndConfig(BaseModel):
    """Antenna configuration for one end of the link (TX or RX)."""

    model: str = "parametric"
    parametric: ParametricAntennaConfig | None = None
    pam: PamAntennaConfig | None = None
    coupling: CouplingConfig | None = None


class AntennaSection(BaseModel):
    """TX and RX antenna configuration pair."""

    tx: AntennaEndConfig
    rx: AntennaEndConfig


class RFStageConfig(BaseModel):
    """Configuration for a single RF stage in a cascaded chain."""

    name: str
    gain_db: float
    nf_db: float
    iip3_dbm: float | None = None


class RFChainSection(BaseModel):
    """RF chain configuration (power, losses, noise, optional cascaded stages)."""

    tx_power_w: float
    tx_losses_db: float = 0.0
    rx_noise_temp_k: float = 0.0
    stages: list[RFStageConfig] | None = None


class PropagationComponentConfig(BaseModel):
    """Configuration for a single propagation loss component."""

    type: str
    availability_target: float | None = None
    climate_region: str | None = None


class PropagationSection(BaseModel):
    """Propagation model configuration with optional composite components."""

    model: str = "composite"
    components: list[PropagationComponentConfig] = []


class ModemSection(BaseModel):
    """Modem configuration (DVB-S2 ModCod table and ACM policy)."""

    enabled: bool = False
    target_bler: float = 1e-5
    modcod_table: str | None = None
    curves: dict[str, Any] | None = None
    acm_policy: dict[str, Any] | None = None


class WorldOpsPolicy(BaseModel):
    """Operational policy constraints for world simulation."""

    min_elevation_deg: float = 10.0
    max_scan_deg: float = 60.0
    handover_hysteresis_s: float = 5.0
    handover_hysteresis_db: float = 3.0
    handover_metric: str = "margin"


class WorldSection(BaseModel):
    """World/mission simulation configuration (time window, trajectory)."""

    enabled: bool = False
    t0_s: float = 0.0
    t1_s: float = 600.0
    dt_s: float = 1.0
    trajectory: dict[str, Any] | None = None
    trajectories: dict[str, dict[str, Any]] | None = None
    ops_policy: WorldOpsPolicy = WorldOpsPolicy()


class ReportsSection(BaseModel):
    """Report generation settings."""

    format: str = "html"
    include_plots: bool = True


class CosineAntennaConfig(BaseModel):
    """Configuration for a cosine-rolloff antenna pattern."""

    peak_gain_dbi: float
    theta_3db_deg: float
    sidelobe_floor_dbi: float = -20.0


class BeamConfig(BaseModel):
    """Configuration for a single beam in a multi-beam payload."""

    beam_id: str
    az_deg: float
    el_deg: float
    tx_power_w: float
    antenna: AntennaEndConfig = AntennaEndConfig()
    cosine: CosineAntennaConfig | None = None

    @field_validator("beam_id")
    @classmethod
    def validate_beam_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("beam_id must not be empty")
        return v


class PayloadSection(BaseModel):
    """Multi-beam payload configuration (beams, grid, beam selection)."""

    beams: list[BeamConfig]
    beam_selection: str = "max_gain"
    grid_az_range: list[float]
    grid_el_range: list[float]
    grid_step_deg: float = 1.0

    @field_validator("beams")
    @classmethod
    def validate_beams_nonempty(cls, v: list[BeamConfig]) -> list[BeamConfig]:
        if not v:
            raise ValueError("payload.beams must contain at least one beam")
        return v

    @field_validator("beam_selection")
    @classmethod
    def validate_beam_selection(cls, v: str) -> str:
        if v not in ("max_gain", "nearest"):
            raise ValueError("beam_selection must be 'max_gain' or 'nearest'")
        return v


class ProjectConfig(BaseModel):
    """Top-level project configuration combining all sections."""

    project: ProjectSection
    scenario: ScenarioSection
    terminals: TerminalsSection
    antenna: AntennaSection
    rf_chain: RFChainSection
    propagation: PropagationSection = PropagationSection()
    modem: ModemSection | None = None
    world: WorldSection | None = None
    reports: ReportsSection | None = None
    payload: PayloadSection | None = None


def load_config(path: str | Path) -> ProjectConfig:
    """Load and validate a YAML config file.

    Parameters
    ----------
    path : str or Path
        Path to the YAML configuration file.

    Returns
    -------
    ProjectConfig
        Validated project configuration.

    Raises
    ------
    pydantic.ValidationError
        If the YAML content fails schema validation.
    """
    with open(path) as f:
        raw = yaml.safe_load(f)
    return ProjectConfig.model_validate(raw)
