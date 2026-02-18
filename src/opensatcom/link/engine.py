"""Default link budget engine."""

from __future__ import annotations

import numpy as np

from opensatcom.core.constants import BOLTZMANN_DBW_PER_K_HZ
from opensatcom.core.models import LinkInputs, LinkOutputs, PropagationConditions
from opensatcom.core.units import lin_to_db10, w_to_dbw


class DefaultLinkEngine:
    """Snapshot link budget engine following spec Section 12."""

    def evaluate_snapshot(
        self,
        elev_deg: float,
        az_deg: float,
        range_m: float,
        inputs: LinkInputs,
        cond: PropagationConditions,
    ) -> LinkOutputs:
        sc = inputs.scenario
        rf = inputs.rf_chain

        # 1. TX power
        tx_power_dbw = w_to_dbw(rf.tx_power_w)
        tx_losses_db = rf.tx_losses_db

        # 2. TX antenna gain
        theta = np.array([elev_deg])
        phi = np.array([az_deg])
        tx_gain_dbi = float(inputs.tx_antenna.gain_dbi(theta, phi, sc.freq_hz)[0])

        # 3. EIRP
        eirp_dbw = tx_power_dbw - tx_losses_db + tx_gain_dbi

        # 4. Path loss (total from propagation model)
        path_loss_db = inputs.propagation.total_path_loss_db(
            sc.freq_hz, elev_deg, range_m, cond
        )

        # 5. RX antenna gain
        rx_gain_dbi = float(inputs.rx_antenna.gain_dbi(theta, phi, sc.freq_hz)[0])

        # 6. System noise temperature
        # Use terminal system_noise_temp_k if set, else rf.rx_noise_temp_k
        rx_terminal = inputs.rx_terminal
        if rx_terminal.system_noise_temp_k is not None:
            tsys_k = rx_terminal.system_noise_temp_k
        else:
            tsys_k = rf.rx_noise_temp_k

        # 7. G/T
        gt_dbk = rx_gain_dbi - lin_to_db10(tsys_k)

        # 8. C/N0 = EIRP - path_loss + G/T - k_boltzmann
        # k_boltzmann is negative in dBW/(K*Hz), so subtracting it adds
        cn0_dbhz = eirp_dbw - path_loss_db + gt_dbk - BOLTZMANN_DBW_PER_K_HZ

        # 9. Eb/N0 = C/N0 - 10*log10(Rb)
        # Compute data rate from bandwidth and spectral efficiency if modem present,
        # otherwise use full bandwidth as bit rate proxy
        data_rate_bps = sc.bandwidth_hz
        if inputs.modem is not None:
            # Use modem to compute throughput later; for Eb/N0 use actual data rate
            modem_result = inputs.modem.throughput_mbps(
                cn0_dbhz - lin_to_db10(sc.bandwidth_hz),  # rough ebn0 estimate
                sc.bandwidth_hz,
                0.0,
            )
            data_rate_bps = modem_result["spectral_eff_bps_per_hz"] * sc.bandwidth_hz

        ebn0_db = cn0_dbhz - lin_to_db10(data_rate_bps)

        # 10. Margin calculation
        if sc.required_metric == "ebn0_db":
            margin_db = ebn0_db - sc.required_value
        elif sc.required_metric == "cn0_dbhz":
            margin_db = cn0_dbhz - sc.required_value
        else:
            margin_db = ebn0_db - sc.required_value

        # 11. Throughput (if modem present)
        throughput_mbps: float | None = None
        if inputs.modem is not None:
            modem_result = inputs.modem.throughput_mbps(
                ebn0_db, sc.bandwidth_hz, 0.0
            )
            throughput_mbps = modem_result["throughput_mbps"]

        # 12. Breakdown dict
        breakdown: dict[str, float] = {
            "tx_power_dbw": tx_power_dbw,
            "tx_losses_db": tx_losses_db,
            "tx_antenna_gain_dbi": tx_gain_dbi,
            "eirp_dbw": eirp_dbw,
            "fspl_db": path_loss_db,
            "rain_db": 0.0,
            "gas_db": 0.0,
            "pointing_db": 0.0,
            "rx_antenna_gain_dbi": rx_gain_dbi,
            "rx_system_temp_k": tsys_k,
            "cn0_dbhz": cn0_dbhz,
            "ebn0_db": ebn0_db,
            "margin_db": margin_db,
        }

        return LinkOutputs(
            eirp_dbw=eirp_dbw,
            gt_dbk=gt_dbk,
            path_loss_db=path_loss_db,
            cn0_dbhz=cn0_dbhz,
            ebn0_db=ebn0_db,
            margin_db=margin_db,
            throughput_mbps=throughput_mbps,
            breakdown=breakdown,
        )
