"""DVB-S2 built-in ModCod table and performance curves."""

from __future__ import annotations

from opensatcom.core.models import ModCod
from opensatcom.core.protocols import PerformanceCurve
from opensatcom.modem.analytic_curves import AnalyticBERCurve

# DVB-S2 standard ModCod definitions
# (name, bits_per_symbol, code_rate, required_ebn0_db at BLER=1e-5)
_DVB_S2_TABLE: list[tuple[str, float, float, float]] = [
    # QPSK (2 bits/symbol)
    ("QPSK_1/4", 2.0, 0.25, -2.35),
    ("QPSK_1/3", 2.0, 1 / 3, -1.24),
    ("QPSK_2/5", 2.0, 0.4, -0.30),
    ("QPSK_1/2", 2.0, 0.5, 1.00),
    ("QPSK_3/5", 2.0, 0.6, 2.23),
    ("QPSK_2/3", 2.0, 2 / 3, 3.10),
    ("QPSK_3/4", 2.0, 0.75, 4.03),
    ("QPSK_4/5", 2.0, 0.8, 4.68),
    ("QPSK_5/6", 2.0, 5 / 6, 5.18),
    ("QPSK_8/9", 2.0, 8 / 9, 6.20),
    ("QPSK_9/10", 2.0, 0.9, 6.42),
    # 8PSK (3 bits/symbol)
    ("8PSK_3/5", 3.0, 0.6, 5.50),
    ("8PSK_2/3", 3.0, 2 / 3, 6.62),
    ("8PSK_3/4", 3.0, 0.75, 7.91),
    ("8PSK_5/6", 3.0, 5 / 6, 9.35),
    ("8PSK_8/9", 3.0, 8 / 9, 10.69),
    ("8PSK_9/10", 3.0, 0.9, 10.98),
    # 16APSK (4 bits/symbol)
    ("16APSK_2/3", 4.0, 2 / 3, 8.97),
    ("16APSK_3/4", 4.0, 0.75, 10.21),
    ("16APSK_4/5", 4.0, 0.8, 11.03),
    ("16APSK_5/6", 4.0, 5 / 6, 11.61),
    ("16APSK_8/9", 4.0, 8 / 9, 12.89),
    ("16APSK_9/10", 4.0, 0.9, 13.13),
    # 32APSK (5 bits/symbol)
    ("32APSK_3/4", 5.0, 0.75, 12.73),
    ("32APSK_4/5", 5.0, 0.8, 13.64),
    ("32APSK_5/6", 5.0, 5 / 6, 14.28),
    ("32APSK_8/9", 5.0, 8 / 9, 15.69),
    ("32APSK_9/10", 5.0, 0.9, 16.05),
]


DVB_S2_MODCODS: list[ModCod] = [
    ModCod(
        name=name,
        bits_per_symbol=bps,
        code_rate=cr,
        rolloff=0.2,
    )
    for name, bps, cr, _ in _DVB_S2_TABLE
]


def get_dvbs2_modcod_table() -> list[ModCod]:
    """Return the full DVB-S2 ModCod table."""
    return list(DVB_S2_MODCODS)


def get_dvbs2_performance_curves() -> dict[str, PerformanceCurve]:
    """Return analytic performance curves for all DVB-S2 ModCods."""
    curves: dict[str, PerformanceCurve] = {}
    for name, bps, cr, req_ebn0 in _DVB_S2_TABLE:
        curves[name] = AnalyticBERCurve(
            bits_per_symbol=bps,
            code_rate=cr,
            required_ebn0_ref_db=req_ebn0,
        )
    return curves
