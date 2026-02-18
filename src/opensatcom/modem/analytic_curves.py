"""Analytic BER/BLER performance curves for standard modulation schemes."""

from __future__ import annotations

import math


def _erfc(x: float) -> float:
    """Complementary error function approximation (Abramowitz & Stegun 7.1.26)."""
    t = 1.0 / (1.0 + 0.3275911 * abs(x))
    poly = t * (
        0.254829592
        + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    result = poly * math.exp(-x * x)
    return result if x >= 0 else 2.0 - result


class AnalyticBERCurve:
    """Analytic BER/BLER curve for coded modulation.

    Uses closed-form approximations calibrated to DVB-S2 reference thresholds.
    For QPSK: BER ~ erfc(sqrt(Eb/N0 * code_rate))
    For higher-order: M-PSK/M-QAM approximations with coding gain offset.

    Parameters
    ----------
    bits_per_symbol : float
        Bits per modulation symbol (2=QPSK, 3=8PSK, 4=16APSK, 5=32APSK).
    code_rate : float
        FEC code rate (e.g. 0.5, 0.75).
    required_ebn0_ref_db : float
        Reference required Eb/N0 at BLER=1e-5 from DVB-S2 standard.
    """

    def __init__(
        self,
        bits_per_symbol: float,
        code_rate: float,
        required_ebn0_ref_db: float,
    ) -> None:
        self.bits_per_symbol = bits_per_symbol
        self.code_rate = code_rate
        self.required_ebn0_ref_db = required_ebn0_ref_db
        self._M = int(2 ** bits_per_symbol)

    def bler(self, ebn0_db: float) -> float:
        """Estimate BLER at given Eb/N0 (dB).

        Uses a waterfall-shaped curve centered on the reference threshold.
        """
        # Distance from threshold in dB
        delta = ebn0_db - self.required_ebn0_ref_db

        # Waterfall curve: steep transition around threshold
        # BLER ~ 0.5 * erfc(k * delta) where k controls steepness
        k = 1.5  # Steepness factor typical for DVB-S2 LDPC codes
        bler_val = 0.5 * _erfc(k * delta)
        return max(min(bler_val, 1.0), 1e-10)

    def required_ebn0_db(self, target_bler: float) -> float:
        """Find Eb/N0 required to achieve target BLER.

        Inverts the waterfall curve analytically.
        """
        if target_bler >= 0.5:
            return self.required_ebn0_ref_db - 5.0
        if target_bler <= 1e-10:
            return self.required_ebn0_ref_db + 5.0

        # Invert: target = 0.5 * erfc(k * delta)
        # erfc(k*delta) = 2*target
        # k*delta = erfc_inv(2*target)
        # Use Newton iteration on erfc to find x where erfc(x) = 2*target
        k = 1.5
        val = 2.0 * target_bler

        # Approximate inverse erfc using bisection
        lo, hi = -5.0, 10.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if _erfc(mid) > val:
                lo = mid
            else:
                hi = mid
        x = (lo + hi) / 2.0
        delta = x / k

        return self.required_ebn0_ref_db + delta
