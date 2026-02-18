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


def load_config(path: str | Path) -> ProjectConfig:
    """Load and validate a YAML config file."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    return ProjectConfig.model_validate(raw)
