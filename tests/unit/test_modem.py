"""Tests for modem, ModCod, and ACM modules."""

import pytest

from opensatcom.core.models import ModCod
from opensatcom.modem.acm import HysteresisACMPolicy
from opensatcom.modem.curves import TablePerformanceCurve
from opensatcom.modem.modem import ModemModel


@pytest.fixture
def sample_modcods() -> list[ModCod]:
    return [
        ModCod("QPSK-1/2", bits_per_symbol=2.0, code_rate=0.5, rolloff=0.2),
        ModCod("QPSK-3/4", bits_per_symbol=2.0, code_rate=0.75, rolloff=0.2),
        ModCod("8PSK-3/4", bits_per_symbol=3.0, code_rate=0.75, rolloff=0.2),
    ]


@pytest.fixture
def sample_curves() -> dict[str, TablePerformanceCurve]:
    # Synthetic performance curves (Eb/N0 vs BLER)
    return {
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


class TestTablePerformanceCurve:
    def test_bler_interpolation(self) -> None:
        curve = TablePerformanceCurve([(0.0, 1.0), (5.0, 0.5), (10.0, 0.0)])
        assert curve.bler(5.0) == pytest.approx(0.5)
        assert curve.bler(2.5) == pytest.approx(0.75)

    def test_required_ebn0(self) -> None:
        curve = TablePerformanceCurve([(0.0, 1.0), (5.0, 0.5), (10.0, 0.0)])
        assert curve.required_ebn0_db(0.5) == pytest.approx(5.0)


class TestHysteresisACMPolicy:
    def test_immediate_downstep(
        self,
        sample_modcods: list[ModCod],
        sample_curves: dict[str, TablePerformanceCurve],
    ) -> None:
        acm = HysteresisACMPolicy(
            sample_modcods, sample_curves, target_bler=1e-3,
            hysteresis_db=1.0, hold_time_s=2.0,
        )
        # Start with high Eb/N0 to move up
        acm.select_modcod(20.0, 0.0)
        acm.select_modcod(20.0, 3.0)
        acm.select_modcod(20.0, 6.0)
        acm.select_modcod(20.0, 9.0)

        # Now drop Eb/N0 sharply — should downstep immediately
        low_mc = acm.select_modcod(3.0, 10.0)
        assert low_mc.name == "QPSK-1/2"

    def test_hysteresis_prevents_premature_upstep(
        self,
        sample_modcods: list[ModCod],
        sample_curves: dict[str, TablePerformanceCurve],
    ) -> None:
        acm = HysteresisACMPolicy(
            sample_modcods, sample_curves, target_bler=1e-3,
            hysteresis_db=1.0, hold_time_s=2.0,
        )
        # Start at lowest ModCod
        mc1 = acm.select_modcod(5.5, 0.0)  # Just above QPSK-1/2 threshold
        assert mc1.name == "QPSK-1/2"

        # Not enough margin for upstep (need threshold + hysteresis)
        mc2 = acm.select_modcod(6.5, 3.0)  # Above QPSK-3/4 threshold but not + hysteresis
        assert mc2.name == "QPSK-1/2"

    def test_hold_time_prevents_fast_upstep(
        self,
        sample_modcods: list[ModCod],
        sample_curves: dict[str, TablePerformanceCurve],
    ) -> None:
        acm = HysteresisACMPolicy(
            sample_modcods, sample_curves, target_bler=1e-3,
            hysteresis_db=0.5, hold_time_s=5.0,
        )
        # Move up to highest ModCod
        acm.select_modcod(20.0, 0.0)
        acm.select_modcod(20.0, 6.0)
        acm.select_modcod(20.0, 12.0)
        # Force downstep
        acm.select_modcod(3.0, 13.0)
        # Try upstep immediately — hold time should prevent it
        mc_held = acm.select_modcod(20.0, 14.0)  # Only 1s after switch
        assert mc_held.name == "QPSK-1/2"

        # After hold time elapses, upstep should be allowed
        mc_up = acm.select_modcod(20.0, 19.0)  # 6s after switch
        assert mc_up.name != "QPSK-1/2"


class TestModemModel:
    def test_throughput_calculation(
        self,
        sample_modcods: list[ModCod],
        sample_curves: dict[str, TablePerformanceCurve],
    ) -> None:
        acm = HysteresisACMPolicy(
            sample_modcods, sample_curves, target_bler=1e-3,
            hysteresis_db=0.5, hold_time_s=2.0,
        )
        modem = ModemModel(sample_modcods, sample_curves, 1e-3, acm)
        result = modem.throughput_mbps(ebn0_db=5.0, bandwidth_hz=200e6, t_s=0.0)

        assert "throughput_mbps" in result
        assert "selected_modcod" in result
        assert "spectral_eff_bps_per_hz" in result
        assert "bler_est" in result
        assert result["throughput_mbps"] > 0.0

    def test_spectral_efficiency(
        self,
        sample_modcods: list[ModCod],
        sample_curves: dict[str, TablePerformanceCurve],
    ) -> None:
        acm = HysteresisACMPolicy(
            sample_modcods, sample_curves, target_bler=1e-3,
            hysteresis_db=0.5, hold_time_s=2.0,
        )
        modem = ModemModel(sample_modcods, sample_curves, 1e-3, acm)
        result = modem.throughput_mbps(ebn0_db=5.0, bandwidth_hz=200e6, t_s=0.0)

        # QPSK-1/2: 2*0.5/1.2 ≈ 0.833 bps/Hz
        expected_spec_eff = 2.0 * 0.5 / 1.2
        assert result["spectral_eff_bps_per_hz"] == pytest.approx(
            expected_spec_eff, rel=1e-6
        )
