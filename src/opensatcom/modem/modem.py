"""Modem model composing ModCod list, performance curves, and ACM policy."""

from __future__ import annotations

from opensatcom.core.models import ModCod
from opensatcom.core.protocols import ACMPolicy, PerformanceCurve


class ModemModel:
    """Modem that maps (Eb/N0, bandwidth, time) to throughput."""

    def __init__(
        self,
        modcods: list[ModCod],
        curves: dict[str, PerformanceCurve],
        target_bler: float,
        acm_policy: ACMPolicy,
    ) -> None:
        self.modcods = modcods
        self.curves = curves
        self.target_bler = target_bler
        self.acm_policy = acm_policy

    def throughput_mbps(
        self, ebn0_db: float, bandwidth_hz: float, t_s: float
    ) -> dict[str, float | str]:
        """Compute throughput for given conditions.

        Returns dict with keys:
        - throughput_mbps
        - selected_modcod (name)
        - spectral_eff_bps_per_hz
        - bler_est
        """
        selected = self.acm_policy.select_modcod(ebn0_db, t_s)
        spec_eff = selected.net_spectral_eff_bps_per_hz()
        bler_est = self.curves[selected.name].bler(ebn0_db)
        throughput_bps = spec_eff * bandwidth_hz * (1.0 - bler_est)
        throughput_mbps = throughput_bps / 1e6

        return {
            "throughput_mbps": throughput_mbps,
            "selected_modcod": selected.name,
            "spectral_eff_bps_per_hz": spec_eff,
            "bler_est": bler_est,
        }
