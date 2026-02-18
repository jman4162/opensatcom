"""Tests for CascadedRFChain with Friis noise cascade and IIP3."""

import pytest

from opensatcom.core.units import db10_to_lin, lin_to_db10
from opensatcom.rf.cascade import T_REF_K, CascadedRFChain, RFStage


class TestRFStage:
    def test_construction(self) -> None:
        stage = RFStage(name="LNA", gain_db=20.0, nf_db=1.0)
        assert stage.name == "LNA"
        assert stage.gain_db == 20.0
        assert stage.nf_db == 1.0
        assert stage.iip3_dbm is None

    def test_with_iip3(self) -> None:
        stage = RFStage(name="LNA", gain_db=20.0, nf_db=1.0, iip3_dbm=-10.0)
        assert stage.iip3_dbm == -10.0


class TestCascadedRFChain:
    def test_empty_stages_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least one stage"):
            CascadedRFChain([], tx_power_w=1.0)

    def test_single_stage_nf(self) -> None:
        """Single stage: cascaded NF equals stage NF."""
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=1.5)
        chain = CascadedRFChain([lna])
        assert chain.cascaded_nf_db() == pytest.approx(1.5, abs=0.01)

    def test_single_stage_noise_temp(self) -> None:
        """T_e = T_ref * (F - 1) for a single stage."""
        nf_db = 1.5
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=nf_db)
        chain = CascadedRFChain([lna])
        f_lin = db10_to_lin(nf_db)
        expected_temp = T_REF_K * (f_lin - 1.0)
        assert chain.cascaded_noise_temp_k() == pytest.approx(expected_temp, abs=0.1)

    def test_friis_two_stage(self) -> None:
        """Classic Friis: LNA (G=20dB, NF=1dB) + Mixer (G=10dB, NF=10dB).

        F_total = F1 + (F2 - 1) / G1
        """
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=1.0)
        mixer = RFStage(name="Mixer", gain_db=10.0, nf_db=10.0)
        chain = CascadedRFChain([lna, mixer])

        f1 = db10_to_lin(1.0)
        f2 = db10_to_lin(10.0)
        g1 = db10_to_lin(20.0)
        f_expected = f1 + (f2 - 1.0) / g1
        nf_expected = lin_to_db10(f_expected)

        assert chain.cascaded_nf_db() == pytest.approx(nf_expected, abs=0.01)

    def test_friis_three_stage(self) -> None:
        """Three-stage Friis cascade."""
        s1 = RFStage(name="LNA", gain_db=25.0, nf_db=0.8)
        s2 = RFStage(name="Filter", gain_db=-2.0, nf_db=2.0)
        s3 = RFStage(name="Mixer", gain_db=10.0, nf_db=8.0)
        chain = CascadedRFChain([s1, s2, s3])

        f1 = db10_to_lin(0.8)
        f2 = db10_to_lin(2.0)
        f3 = db10_to_lin(8.0)
        g1 = db10_to_lin(25.0)
        g2 = db10_to_lin(-2.0)
        f_expected = f1 + (f2 - 1.0) / g1 + (f3 - 1.0) / (g1 * g2)
        nf_expected = lin_to_db10(f_expected)

        assert chain.cascaded_nf_db() == pytest.approx(nf_expected, abs=0.01)

    def test_lna_dominates_noise(self) -> None:
        """With high-gain LNA, later stages contribute little noise."""
        lna = RFStage(name="LNA", gain_db=30.0, nf_db=1.0)
        noisy = RFStage(name="Noisy", gain_db=0.0, nf_db=15.0)
        chain = CascadedRFChain([lna, noisy])
        # NF should be close to LNA alone (within ~0.15 dB)
        assert chain.cascaded_nf_db() == pytest.approx(1.0, abs=0.15)

    def test_total_gain(self) -> None:
        s1 = RFStage(name="LNA", gain_db=20.0, nf_db=1.0)
        s2 = RFStage(name="Filter", gain_db=-3.0, nf_db=3.0)
        chain = CascadedRFChain([s1, s2])
        assert chain.total_gain_db() == pytest.approx(17.0, abs=0.01)

    def test_tx_losses(self) -> None:
        """TX loss chain: all lossy stages."""
        cable = RFStage(name="Cable", gain_db=-1.5, nf_db=1.5)
        feed = RFStage(name="Feed", gain_db=-0.5, nf_db=0.5)
        chain = CascadedRFChain([cable, feed], tx_power_w=100.0)
        assert chain.tx_losses_db() == pytest.approx(2.0, abs=0.01)

    def test_tx_losses_zero_for_gain_chain(self) -> None:
        """TX losses should be 0 if chain has net positive gain."""
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=1.0)
        chain = CascadedRFChain([lna])
        assert chain.tx_losses_db() == 0.0

    def test_to_simple_rf_chain(self) -> None:
        """Backward compatibility: CascadedRFChain → RFChainModel."""
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=1.5)
        chain = CascadedRFChain([lna], tx_power_w=50.0)
        simple = chain.to_simple_rf_chain()
        assert simple.tx_power_w == 50.0
        assert simple.rx_noise_temp_k == pytest.approx(
            chain.cascaded_noise_temp_k(), abs=0.1
        )

    def test_iip3_cascade(self) -> None:
        """IIP3 with two stages."""
        s1 = RFStage(name="LNA", gain_db=20.0, nf_db=1.0, iip3_dbm=-10.0)
        s2 = RFStage(name="Mixer", gain_db=10.0, nf_db=8.0, iip3_dbm=5.0)
        chain = CascadedRFChain([s1, s2])
        iip3 = chain.cascaded_iip3_dbm()
        assert iip3 is not None
        # IIP3 should be finite and less than first stage (degraded by cascade)
        assert iip3 < -10.0  # worse than LNA alone due to mixer

    def test_iip3_none_when_no_stages_have_it(self) -> None:
        s1 = RFStage(name="Filter", gain_db=-2.0, nf_db=2.0)
        chain = CascadedRFChain([s1])
        assert chain.cascaded_iip3_dbm() is None

    def test_n_stages(self) -> None:
        stages = [
            RFStage(name="LNA", gain_db=20.0, nf_db=1.0),
            RFStage(name="Mixer", gain_db=10.0, nf_db=8.0),
        ]
        chain = CascadedRFChain(stages)
        assert chain.n_stages == 2

    def test_repr(self) -> None:
        lna = RFStage(name="LNA", gain_db=20.0, nf_db=1.0)
        chain = CascadedRFChain([lna])
        r = repr(chain)
        assert "LNA" in r
        assert "NF=" in r
        assert "T_e=" in r

    def test_typical_rx_chain(self) -> None:
        """Realistic 4-stage Rx: LNA → BPF → Mixer → IF Amp.

        Verify cascaded temp is dominated by LNA.
        """
        stages = [
            RFStage(name="LNA", gain_db=25.0, nf_db=0.5),
            RFStage(name="BPF", gain_db=-1.0, nf_db=1.0),
            RFStage(name="Mixer", gain_db=-6.0, nf_db=6.0),
            RFStage(name="IF_Amp", gain_db=30.0, nf_db=4.0),
        ]
        chain = CascadedRFChain(stages, tx_power_w=0.0)
        # LNA NF=0.5 dB → ~35 K, total should be close due to high LNA gain
        assert chain.cascaded_noise_temp_k() < 50.0
        # Total gain: 25 - 1 - 6 + 30 = 48 dB
        assert chain.total_gain_db() == pytest.approx(48.0, abs=0.01)
