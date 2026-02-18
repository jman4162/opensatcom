"""Tests for RF chain model."""

import pytest

from opensatcom.core.models import RFChainModel


class TestRFChainModel:
    def test_3db_loss_halves_power(self) -> None:
        rf = RFChainModel(tx_power_w=100.0, tx_losses_db=3.0, rx_noise_temp_k=300.0)
        assert rf.effective_tx_power_w() == pytest.approx(50.0, rel=2e-2)

    def test_zero_loss(self) -> None:
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=0.0, rx_noise_temp_k=300.0)
        assert rf.effective_tx_power_w() == pytest.approx(200.0, rel=1e-10)

    def test_effective_dbw(self) -> None:
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=300.0)
        from opensatcom.core.units import w_to_dbw

        assert rf.effective_tx_power_dbw() == pytest.approx(w_to_dbw(200.0) - 2.0)

    def test_system_temp_addition(self) -> None:
        rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=300.0)
        assert rf.system_temp_k(200.0) == pytest.approx(500.0)
