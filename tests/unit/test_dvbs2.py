"""Tests for DVB-S2 ModCod table."""


from opensatcom.modem.dvbs2 import (
    DVB_S2_MODCODS,
    get_dvbs2_modcod_table,
    get_dvbs2_performance_curves,
)


class TestDVBS2Table:
    def test_table_count(self) -> None:
        assert len(DVB_S2_MODCODS) == 28

    def test_get_returns_copy(self) -> None:
        t1 = get_dvbs2_modcod_table()
        t2 = get_dvbs2_modcod_table()
        assert t1 is not t2
        assert len(t1) == 28

    def test_qpsk_14_is_lowest_rate(self) -> None:
        mc = DVB_S2_MODCODS[0]
        assert mc.name == "QPSK_1/4"
        assert mc.bits_per_symbol == 2.0
        assert mc.code_rate == 0.25

    def test_thresholds_ordered(self) -> None:
        """Required Eb/N0 should generally increase with spectral efficiency."""
        curves = get_dvbs2_performance_curves()
        thresholds = [curves[mc.name].required_ebn0_db(1e-5) for mc in DVB_S2_MODCODS]
        # Within each modulation family, thresholds should increase
        # Overall they should trend upward
        assert thresholds[-1] > thresholds[0]

    def test_all_modcods_have_curves(self) -> None:
        curves = get_dvbs2_performance_curves()
        for mc in DVB_S2_MODCODS:
            assert mc.name in curves

    def test_rolloff(self) -> None:
        for mc in DVB_S2_MODCODS:
            assert mc.rolloff == 0.2

    def test_spectral_efficiency_positive(self) -> None:
        for mc in DVB_S2_MODCODS:
            assert mc.net_spectral_eff_bps_per_hz() > 0.0
