"""Tests for analytic BER performance curves."""


from opensatcom.modem.analytic_curves import AnalyticBERCurve


class TestAnalyticBERCurve:
    def setup_method(self) -> None:
        # QPSK 1/2 reference: ~1.0 dB required Eb/N0 at BLER=1e-5
        self.qpsk = AnalyticBERCurve(
            bits_per_symbol=2.0,
            code_rate=0.5,
            required_ebn0_ref_db=1.0,
        )

    def test_bler_decreases_with_ebn0(self) -> None:
        bler_low = self.qpsk.bler(-2.0)
        bler_mid = self.qpsk.bler(1.0)
        bler_high = self.qpsk.bler(5.0)
        assert bler_low > bler_mid > bler_high

    def test_bler_near_half_at_threshold(self) -> None:
        bler = self.qpsk.bler(1.0)
        assert 0.3 < bler < 0.7  # Near 0.5 at threshold

    def test_bler_bounded(self) -> None:
        assert self.qpsk.bler(-10.0) <= 1.0
        assert self.qpsk.bler(20.0) >= 1e-10

    def test_required_ebn0_increases_for_lower_bler(self) -> None:
        ebn0_1e3 = self.qpsk.required_ebn0_db(1e-3)
        ebn0_1e5 = self.qpsk.required_ebn0_db(1e-5)
        ebn0_1e7 = self.qpsk.required_ebn0_db(1e-7)
        assert ebn0_1e7 > ebn0_1e5 > ebn0_1e3

    def test_required_ebn0_near_reference(self) -> None:
        """At BLER=1e-5, required Eb/N0 should be near the reference."""
        ebn0 = self.qpsk.required_ebn0_db(1e-5)
        assert abs(ebn0 - 1.0) < 3.0  # Within 3 dB of reference

    def test_conforms_to_protocol(self) -> None:
        from opensatcom.core.protocols import PerformanceCurve

        assert isinstance(self.qpsk, PerformanceCurve)

    def test_16apsk_higher_threshold(self) -> None:
        apsk16 = AnalyticBERCurve(
            bits_per_symbol=4.0,
            code_rate=0.75,
            required_ebn0_ref_db=10.21,
        )
        ebn0 = apsk16.required_ebn0_db(1e-5)
        assert ebn0 > self.qpsk.required_ebn0_db(1e-5)
