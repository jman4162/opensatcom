"""Inter-beam interference model for multi-beam payloads."""

from __future__ import annotations

import math
from dataclasses import dataclass

from opensatcom.core.constants import BOLTZMANN_DBW_PER_K_HZ
from opensatcom.core.models import PropagationConditions, Terminal
from opensatcom.core.protocols import AntennaModel
from opensatcom.core.units import db10_to_lin, lin_to_db10
from opensatcom.payload.beamset import BeamSet


@dataclass(frozen=True)
class InterferenceResult:
    """Result of an interference evaluation at a single point.

    All power values are in dB domain. Interference and noise are summed
    in linear domain then converted.
    """

    serving_beam_id: str
    signal_dbw: float
    interference_dbw: float
    noise_dbw: float
    cnir_db: float
    sinr_db: float
    cn0_dbhz: float
    ebn0_db: float
    margin_db: float
    throughput_mbps: float | None = None


class SimpleInterferenceModel:
    """Evaluate signal, interference, and noise for a multi-beam payload.

    For a victim at a given direction and range:
    1. Signal (C) = serving beam's EIRP toward victim / path_loss * rx_gain
    2. Interference (I) = sum of non-serving beams' EIRP / path_loss * rx_gain
    3. Noise (N) = kB * T_sys * bandwidth
    4. SINR = C / I  (linear, then to dB)
    5. C/(N+I) = C / (N + I)

    Path loss is the same for all beams (same satellite, same range to victim).
    """

    def evaluate(
        self,
        beamset: BeamSet,
        serving_beam_id: str,
        victim_az_deg: float,
        victim_el_deg: float,
        range_m: float,
        rx_antenna: AntennaModel,
        rx_terminal: Terminal,
        cond: PropagationConditions,
    ) -> InterferenceResult:
        """Evaluate interference at a single victim location.

        Parameters
        ----------
        beamset : the multi-beam payload
        serving_beam_id : which beam is serving this victim
        victim_az_deg, victim_el_deg : direction to the victim (from satellite)
        range_m : slant range to the victim
        rx_antenna : victim's receive antenna model
        rx_terminal : victim terminal (for system noise temp)
        cond : propagation conditions
        """
        sc = beamset.scenario
        rf = beamset.rf_chain
        serving_beam = beamset.get_beam(serving_beam_id)

        # Path loss (same for all beams — same satellite)
        path_loss_db = beamset.propagation.total_path_loss_db(
            sc.freq_hz, victim_el_deg, range_m, cond
        )
        path_loss_lin = db10_to_lin(path_loss_db)

        # RX antenna gain toward satellite direction
        import numpy as np

        rx_gain_dbi = float(
            rx_antenna.gain_dbi(
                np.array([victim_az_deg]), np.array([victim_el_deg]), sc.freq_hz
            )[0]
        )
        rx_gain_lin = db10_to_lin(rx_gain_dbi)

        # Signal power from serving beam (watts at receiver)
        serving_eirp_dbw = serving_beam.eirp_toward_dbw(
            victim_az_deg, victim_el_deg, sc.freq_hz
        )
        c_w = db10_to_lin(serving_eirp_dbw) / path_loss_lin * rx_gain_lin

        # Interference from non-serving beams (sum in linear watts)
        i_total_w = 0.0
        for beam in beamset:
            if beam.beam_id == serving_beam_id:
                continue
            beam_eirp_dbw = beam.eirp_toward_dbw(
                victim_az_deg, victim_el_deg, sc.freq_hz
            )
            i_j_w = db10_to_lin(beam_eirp_dbw) / path_loss_lin * rx_gain_lin
            i_total_w += i_j_w

        # Noise power
        tsys_k = (
            rx_terminal.system_noise_temp_k
            if rx_terminal.system_noise_temp_k is not None
            else rf.rx_noise_temp_k
        )
        # N = kB * T_sys * bandwidth  (watts)
        k_b_lin = db10_to_lin(BOLTZMANN_DBW_PER_K_HZ)  # W/(K·Hz)
        n_w = k_b_lin * tsys_k * sc.bandwidth_hz

        # Convert to dB
        signal_dbw = lin_to_db10(c_w)
        interference_dbw = lin_to_db10(i_total_w) if i_total_w > 0 else -math.inf
        noise_dbw = lin_to_db10(n_w)

        # C/(N+I) in dB
        cnir_db = lin_to_db10(c_w / (n_w + i_total_w))

        # SINR in dB (C/I)
        sinr_db = lin_to_db10(c_w / i_total_w) if i_total_w > 0 else math.inf

        # C/N0 = C / (kB * T_sys) in dB-Hz
        cn0_dbhz = lin_to_db10(c_w / (k_b_lin * tsys_k))

        # Eb/N0 = C/N0 - 10*log10(bandwidth)
        ebn0_db = cn0_dbhz - lin_to_db10(sc.bandwidth_hz)

        # Margin relative to scenario requirement
        if sc.required_metric == "ebn0_db":
            margin_db = ebn0_db - sc.required_value
        elif sc.required_metric == "cn0_dbhz":
            margin_db = cn0_dbhz - sc.required_value
        else:
            margin_db = ebn0_db - sc.required_value

        return InterferenceResult(
            serving_beam_id=serving_beam_id,
            signal_dbw=signal_dbw,
            interference_dbw=interference_dbw,
            noise_dbw=noise_dbw,
            cnir_db=cnir_db,
            sinr_db=sinr_db,
            cn0_dbhz=cn0_dbhz,
            ebn0_db=ebn0_db,
            margin_db=margin_db,
        )
