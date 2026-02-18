"""YAML config loading with Pydantic v2 validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator


class ProjectSection(BaseModel):
    name: str
    seed: int = 42
    output_dir: str = "./runs"


class ScenarioSection(BaseModel):
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
    name: str
    lat_deg: float
    lon_deg: float
    alt_m: float
    system_noise_temp_k: float | None = None


class TerminalsSection(BaseModel):
    tx: TerminalSection
    rx: TerminalSection


class ParametricAntennaConfig(BaseModel):
    gain_dbi: float = 0.0
    scan_loss_model: str = "none"


class PamAntennaConfig(BaseModel):
    nx: int = 1
    ny: int = 1
    dx_lambda: float = 0.5
    dy_lambda: float = 0.5
    taper: dict[str, Any] | None = None
    steering: dict[str, Any] | None = None
    impairments: dict[str, Any] | None = None


class AntennaEndConfig(BaseModel):
    model: str = "parametric"
    parametric: ParametricAntennaConfig | None = None
    pam: PamAntennaConfig | None = None
    coupling: dict[str, Any] | None = None


class AntennaSection(BaseModel):
    tx: AntennaEndConfig
    rx: AntennaEndConfig


class RFChainSection(BaseModel):
    tx_power_w: float
    tx_losses_db: float
    rx_noise_temp_k: float


class PropagationComponentConfig(BaseModel):
    type: str
    availability_target: float | None = None
    climate_region: str | None = None


class PropagationSection(BaseModel):
    model: str = "composite"
    components: list[PropagationComponentConfig] = []


class ModemSection(BaseModel):
    enabled: bool = False
    target_bler: float = 1e-5
    modcod_table: str | None = None
    curves: dict[str, Any] | None = None
    acm_policy: dict[str, Any] | None = None


class WorldOpsPolicy(BaseModel):
    min_elevation_deg: float = 10.0
    max_scan_deg: float = 60.0


class WorldSection(BaseModel):
    enabled: bool = False
    t0_s: float = 0.0
    t1_s: float = 600.0
    dt_s: float = 1.0
    trajectory: dict[str, Any] | None = None
    ops_policy: WorldOpsPolicy = WorldOpsPolicy()


class ReportsSection(BaseModel):
    format: str = "html"
    include_plots: bool = True


class CosineAntennaConfig(BaseModel):
    peak_gain_dbi: float
    theta_3db_deg: float
    sidelobe_floor_dbi: float = -20.0


class BeamConfig(BaseModel):
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
    """Load and validate a YAML config file."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    return ProjectConfig.model_validate(raw)
