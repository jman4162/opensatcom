"""Tests for core datamodels."""

import pytest

from opensatcom.core.models import ModCod, RFChainModel, Scenario, Terminal


class TestTerminal:
    def test_frozen(self) -> None:
        t = Terminal("test", 0.0, 0.0, 100.0)
        with pytest.raises(AttributeError):
            t.name = "changed"  # type: ignore[misc]

    def test_optional_fields(self) -> None:
        t = Terminal("test", 0.0, 0.0, 100.0)
        assert t.system_noise_temp_k is None
        assert t.misc is None

    def test_with_system_temp(self) -> None:
        t = Terminal("test", 0.0, 0.0, 100.0, system_noise_temp_k=500.0)
        assert t.system_noise_temp_k == 500.0


class TestScenario:
    def test_frozen(self) -> None:
        s = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
        with pytest.raises(AttributeError):
            s.name = "changed"  # type: ignore[misc]


class TestModCod:
    def test_net_spectral_eff(self) -> None:
        mc = ModCod("QPSK-1/2", bits_per_symbol=2.0, code_rate=0.5, rolloff=0.2)
        expected = 2.0 * 0.5 / 1.2
        assert mc.net_spectral_eff_bps_per_hz() == pytest.approx(expected, rel=1e-10)

    def test_net_spectral_eff_with_pilots(self) -> None:
        mc = ModCod(
            "QPSK-1/2",
            bits_per_symbol=2.0,
            code_rate=0.5,
            rolloff=0.2,
            pilot_overhead=0.05,
        )
        expected = 2.0 * 0.5 * 0.95 / 1.2
        assert mc.net_spectral_eff_bps_per_hz() == pytest.approx(expected, rel=1e-10)

    def test_frozen(self) -> None:
        mc = ModCod("test", 2.0, 0.5)
        with pytest.raises(AttributeError):
            mc.name = "changed"  # type: ignore[misc]


class TestRFChainModel:
    def test_effective_tx_power(self) -> None:
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=3.0, rx_noise_temp_k=500.0)
        # 3 dB loss = half power
        assert rf.effective_tx_power_w() == pytest.approx(100.0, rel=1e-2)

    def test_effective_tx_power_dbw(self) -> None:
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=500.0)
        from opensatcom.core.units import w_to_dbw

        expected = w_to_dbw(200.0) - 2.0
        assert rf.effective_tx_power_dbw() == pytest.approx(expected, rel=1e-10)

    def test_system_temp(self) -> None:
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=300.0)
        assert rf.system_temp_k(200.0) == pytest.approx(500.0)
