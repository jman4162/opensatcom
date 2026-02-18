"""Golden tests for CascadedRFChain — frozen reference values."""

import pytest

from opensatcom.rf.cascade import CascadedRFChain, RFStage


class TestRFCascadeGolden:
    def test_typical_rx_chain_noise_temp(self) -> None:
        """Frozen value: 4-stage Rx chain noise temperature.

        LNA(G=25,NF=0.5) → BPF(G=-1,NF=1) → Mixer(G=-6,NF=6) → IF(G=30,NF=4)
        """
        stages = [
            RFStage(name="LNA", gain_db=25.0, nf_db=0.5),
            RFStage(name="BPF", gain_db=-1.0, nf_db=1.0),
            RFStage(name="Mixer", gain_db=-6.0, nf_db=6.0),
            RFStage(name="IF_Amp", gain_db=30.0, nf_db=4.0),
        ]
        chain = CascadedRFChain(stages)
        assert chain.cascaded_noise_temp_k() == pytest.approx(46.01, abs=0.5)
        assert chain.total_gain_db() == pytest.approx(48.0, abs=0.01)
        assert chain.cascaded_nf_db() == pytest.approx(0.65, abs=0.05)

    def test_two_stage_friis_frozen(self) -> None:
        """Frozen: LNA(G=20,NF=1) + Mixer(G=10,NF=10) → NF ≈ 1.30 dB."""
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=1.0)
        mixer = RFStage(name="Mixer", gain_db=10.0, nf_db=10.0)
        chain = CascadedRFChain([lna, mixer])
        assert chain.cascaded_nf_db() == pytest.approx(1.30, abs=0.05)
        assert chain.cascaded_noise_temp_k() == pytest.approx(101.2, abs=1.0)
