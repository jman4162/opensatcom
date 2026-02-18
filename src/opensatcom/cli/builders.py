"""Factory functions translating Pydantic config to domain objects."""

from __future__ import annotations

from typing import Any

import numpy as np

from opensatcom.antenna.cosine import CosineRolloffAntenna
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
    BeamConfig,
    ModemSection,
    ProjectConfig,
    PropagationSection,
    RFChainSection,
    TerminalSection,
)
from opensatcom.payload.beam import Beam
from opensatcom.payload.beamset import BeamSet
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
    # Coupling-aware antenna from EdgeFEM artifact
    if cfg.coupling is not None and cfg.coupling.enabled:
        from opensatcom.antenna.coupling import CouplingAwareAntenna

        if cfg.coupling.artifact_path is None:
            raise ValueError("coupling.artifact_path required when coupling enabled")
        return CouplingAwareAntenna.from_npz(
            cfg.coupling.artifact_path,
            steering_az_deg=cfg.coupling.steering_az_deg,
            steering_el_deg=cfg.coupling.steering_el_deg,
        )

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
    from opensatcom.propagation.gas import GaseousAbsorptionP676
    from opensatcom.propagation.rain import RainAttenuationP618
    from opensatcom.propagation.scintillation import ScintillationLoss

    components = []
    for comp in cfg.components:
        if comp.type == "fspl":
            components.append(FreeSpacePropagation())
        elif comp.type in ("itur_rain", "rain"):
            components.append(
                RainAttenuationP618(
                    availability_target=comp.availability_target or 0.99,
                    climate_region=comp.climate_region,
                )
            )
        elif comp.type in ("itur_gas", "gas"):
            components.append(GaseousAbsorptionP676())
        elif comp.type == "scintillation":
            components.append(
                ScintillationLoss(
                    availability_target=comp.availability_target or 0.99,
                )
            )
    if not components:
        components.append(FreeSpacePropagation())
    return CompositePropagation(components)


def _build_rf_chain(cfg: RFChainSection) -> RFChainModel:
    """Build RFChainModel, using cascaded stages if present."""
    if cfg.stages:
        from opensatcom.rf.cascade import CascadedRFChain, RFStage

        stages = [
            RFStage(
                name=s.name,
                gain_db=s.gain_db,
                nf_db=s.nf_db,
                iip3_dbm=s.iip3_dbm,
            )
            for s in cfg.stages
        ]
        cascade = CascadedRFChain(stages, tx_power_w=cfg.tx_power_w)
        return cascade.to_simple_rf_chain()
    return RFChainModel(
        tx_power_w=cfg.tx_power_w,
        tx_losses_db=cfg.tx_losses_db,
        rx_noise_temp_k=cfg.rx_noise_temp_k,
    )


def _build_modem(cfg_modem: ModemSection) -> Any:
    """Build ModemModel from config, defaulting to DVB-S2 built-in table."""
    from opensatcom.modem.acm import HysteresisACMPolicy
    from opensatcom.modem.dvbs2 import get_dvbs2_modcod_table, get_dvbs2_performance_curves
    from opensatcom.modem.modem import ModemModel

    modcods = get_dvbs2_modcod_table()
    curves = get_dvbs2_performance_curves()
    target_bler = cfg_modem.target_bler

    acm_kwargs: dict[str, float] = {}
    if cfg_modem.acm_policy:
        if "hysteresis_db" in cfg_modem.acm_policy:
            acm_kwargs["hysteresis_db"] = cfg_modem.acm_policy["hysteresis_db"]
        if "hold_time_s" in cfg_modem.acm_policy:
            acm_kwargs["hold_time_s"] = cfg_modem.acm_policy["hold_time_s"]

    acm_policy = HysteresisACMPolicy(
        modcods=modcods,
        curves=curves,
        target_bler=target_bler,
        **acm_kwargs,
    )

    return ModemModel(
        modcods=modcods,
        curves=curves,
        target_bler=target_bler,
        acm_policy=acm_policy,
    )


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

    rf_chain = _build_rf_chain(cfg.rf_chain)

    modem = None
    if cfg.modem is not None and cfg.modem.enabled:
        modem = _build_modem(cfg.modem)

    return LinkInputs(
        tx_terminal=tx_terminal,
        rx_terminal=rx_terminal,
        scenario=scenario,
        tx_antenna=tx_antenna,
        rx_antenna=rx_antenna,
        propagation=propagation,
        rf_chain=rf_chain,
        modem=modem,
    )


def _build_beam_antenna(beam_cfg: BeamConfig) -> AntennaModel:
    """Build antenna for a beam — uses cosine config if present, else standard dispatch."""
    if beam_cfg.cosine is not None:
        c = beam_cfg.cosine
        return CosineRolloffAntenna(
            peak_gain_dbi=c.peak_gain_dbi,
            theta_3db_deg=c.theta_3db_deg,
            sidelobe_floor_dbi=c.sidelobe_floor_dbi,
            boresight_az_deg=beam_cfg.az_deg,
            boresight_el_deg=beam_cfg.el_deg,
        )
    return _build_antenna(beam_cfg.antenna)


def build_beamset_from_config(cfg: ProjectConfig) -> BeamSet:
    """Build a BeamSet from a validated ProjectConfig with payload section."""
    if cfg.payload is None:
        raise ValueError("Config must have a 'payload' section for beammap command")

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

    propagation = _build_propagation(cfg.propagation)

    rf_chain = _build_rf_chain(cfg.rf_chain)

    beams = []
    for bc in cfg.payload.beams:
        ant = _build_beam_antenna(bc)
        beams.append(Beam(
            beam_id=bc.beam_id,
            az_deg=bc.az_deg,
            el_deg=bc.el_deg,
            tx_power_w=bc.tx_power_w,
            antenna=ant,
        ))

    return BeamSet(beams, scenario, propagation, rf_chain)


def build_beam_grid(cfg: ProjectConfig) -> tuple[np.ndarray, np.ndarray]:
    """Build az/el evaluation grid from config payload section."""
    if cfg.payload is None:
        raise ValueError("Config must have a 'payload' section")

    az_range = cfg.payload.grid_az_range
    el_range = cfg.payload.grid_el_range
    step = cfg.payload.grid_step_deg

    grid_az = np.arange(az_range[0], az_range[1] + step / 2, step)
    grid_el = np.arange(el_range[0], el_range[1] + step / 2, step)
    return grid_az, grid_el
