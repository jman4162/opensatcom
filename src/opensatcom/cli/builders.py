"""Factory functions translating Pydantic config to domain objects."""

from __future__ import annotations

from opensatcom.antenna.pam import PamArrayAntenna
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.models import (
    LinkInputs,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.core.protocols import AntennaModel, PropagationModel
from opensatcom.io.config_loader import (
    AntennaEndConfig,
    ProjectConfig,
    PropagationSection,
    TerminalSection,
)
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation


def _build_terminal(cfg: TerminalSection) -> Terminal:
    return Terminal(
        name=cfg.name,
        lat_deg=cfg.lat_deg,
        lon_deg=cfg.lon_deg,
        alt_m=cfg.alt_m,
        system_noise_temp_k=cfg.system_noise_temp_k,
    )


def _build_antenna(cfg: AntennaEndConfig) -> AntennaModel:
    if cfg.model == "pam" and cfg.pam is not None:
        pam_cfg = cfg.pam
        taper = None
        if pam_cfg.taper is not None:
            t = pam_cfg.taper
            if "type" in t and "sidelobe_db" in t:
                taper = (t["type"], t["sidelobe_db"])
        return PamArrayAntenna(
            nx=pam_cfg.nx,
            ny=pam_cfg.ny,
            dx_lambda=pam_cfg.dx_lambda,
            dy_lambda=pam_cfg.dy_lambda,
            taper=taper,
        )
    else:
        gain = 0.0
        if cfg.parametric is not None:
            gain = cfg.parametric.gain_dbi
        return ParametricAntenna(gain_dbi=gain)


def _build_propagation(cfg: PropagationSection) -> PropagationModel:
    components = []
    for comp in cfg.components:
        if comp.type == "fspl":
            components.append(FreeSpacePropagation())
        # Other types (itur_rain, itur_gas) are plugin-based, skip for P0
    if not components:
        components.append(FreeSpacePropagation())
    return CompositePropagation(components)


def build_link_inputs_from_config(cfg: ProjectConfig) -> LinkInputs:
    """Build LinkInputs from a validated ProjectConfig."""
    tx_terminal = _build_terminal(cfg.terminals.tx)
    rx_terminal = _build_terminal(cfg.terminals.rx)

    scenario = Scenario(
        name=cfg.scenario.name,
        direction=cfg.scenario.direction,
        freq_hz=cfg.scenario.freq_hz,
        bandwidth_hz=cfg.scenario.bandwidth_hz,
        polarization=cfg.scenario.polarization,
        required_metric=cfg.scenario.required_metric,
        required_value=cfg.scenario.required_value,
        misc=cfg.scenario.misc,
    )

    tx_antenna = _build_antenna(cfg.antenna.tx)
    rx_antenna = _build_antenna(cfg.antenna.rx)
    propagation = _build_propagation(cfg.propagation)

    rf_chain = RFChainModel(
        tx_power_w=cfg.rf_chain.tx_power_w,
        tx_losses_db=cfg.rf_chain.tx_losses_db,
        rx_noise_temp_k=cfg.rf_chain.rx_noise_temp_k,
    )

    return LinkInputs(
        tx_terminal=tx_terminal,
        rx_terminal=rx_terminal,
        scenario=scenario,
        tx_antenna=tx_antenna,
        rx_antenna=rx_antenna,
        propagation=propagation,
        rf_chain=rf_chain,
    )
