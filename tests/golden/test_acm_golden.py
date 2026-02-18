"""Golden test for ACM ModCod selection sequence."""

import pytest

from opensatcom.core.models import ModCod
from opensatcom.modem.acm import HysteresisACMPolicy
from opensatcom.modem.curves import TablePerformanceCurve


@pytest.mark.golden
class TestACMGolden:
    def test_modcod_selection_sequence(self) -> None:
        """Deterministic ModCod selection for a known Eb/N0 time profile."""
        modcods = [
            ModCod("QPSK-1/2", bits_per_symbol=2.0, code_rate=0.5, rolloff=0.2),
            ModCod("QPSK-3/4", bits_per_symbol=2.0, code_rate=0.75, rolloff=0.2),
            ModCod("8PSK-3/4", bits_per_symbol=3.0, code_rate=0.75, rolloff=0.2),
        ]
        curves = {
            "QPSK-1/2": TablePerformanceCurve([
                (0.0, 0.5), (2.0, 0.1), (4.0, 1e-3), (6.0, 1e-6), (10.0, 1e-10),
            ]),
            "QPSK-3/4": TablePerformanceCurve([
                (2.0, 0.5), (4.0, 0.1), (6.0, 1e-3), (8.0, 1e-6), (12.0, 1e-10),
            ]),
            "8PSK-3/4": TablePerformanceCurve([
                (4.0, 0.5), (6.0, 0.1), (8.0, 1e-3), (10.0, 1e-6), (14.0, 1e-10),
            ]),
        }
        acm = HysteresisACMPolicy(
            modcods, curves, target_bler=1e-3,
            hysteresis_db=0.5, hold_time_s=2.0,
        )

        # Known time profile: ramp up, hold, drop, recover
        ebn0_profile = [
            (5.0, 0.0),   # t=0: above QPSK-1/2, start
            (8.0, 3.0),   # t=3: high enough for QPSK-3/4 + hysteresis
            (12.0, 6.0),  # t=6: high enough for 8PSK-3/4 + hysteresis
            (12.0, 9.0),  # t=9: hold at 8PSK-3/4
            (3.0, 10.0),  # t=10: crash → immediate downstep
            (8.0, 11.0),  # t=11: recovering, but hold time blocks upstep
            (8.0, 13.0),  # t=13: hold time elapsed, can upstep
        ]

        expected_sequence = [
            "QPSK-1/2",  # t=0
            "QPSK-3/4",  # t=3
            "8PSK-3/4",  # t=6
            "8PSK-3/4",  # t=9
            "QPSK-1/2",  # t=10
            "QPSK-1/2",  # t=11 (hold time blocks)
            "QPSK-3/4",  # t=13 (hold time elapsed, upstep with hysteresis)
        ]

        actual_sequence = []
        for ebn0, t in ebn0_profile:
            mc = acm.select_modcod(ebn0, t)
            actual_sequence.append(mc.name)

        assert actual_sequence == expected_sequence
