"""Golden test vectors for modem/DVB-S2 module."""

import pytest

from opensatcom.modem.dvbs2 import get_dvbs2_modcod_table, get_dvbs2_performance_curves


@pytest.mark.golden
class TestModemGolden:
    def test_qpsk_12_required_ebn0(self) -> None:
        """Frozen: QPSK 1/2 required Eb/N0 at BLER=1e-5."""
        curves = get_dvbs2_performance_curves()
        ebn0 = curves["QPSK_1/2"].required_ebn0_db(1e-5)
        assert ebn0 == pytest.approx(3.011, abs=0.05)

    def test_16apsk_34_throughput(self) -> None:
        """Frozen: 16APSK 3/4 spectral efficiency and throughput at 36 MHz BW."""
        table = get_dvbs2_modcod_table()
        mc = next(m for m in table if m.name == "16APSK_3/4")
        spec_eff = mc.net_spectral_eff_bps_per_hz()
        bw_hz = 36e6
        throughput_mbps = spec_eff * bw_hz / 1e6
        assert spec_eff == pytest.approx(2.5, abs=0.01)
        assert throughput_mbps == pytest.approx(90.0, abs=0.5)
