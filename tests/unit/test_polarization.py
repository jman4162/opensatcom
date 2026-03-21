"""Tests for polarization mismatch loss computation."""

import pytest

from opensatcom.link.polarization import polarization_loss_db


class TestPolarizationLoss:
    """Tests for polarization_loss_db."""

    def test_copol_rhcp(self) -> None:
        assert polarization_loss_db("RHCP", "RHCP") == 0.0

    def test_copol_lhcp(self) -> None:
        assert polarization_loss_db("LHCP", "LHCP") == 0.0

    def test_copol_h(self) -> None:
        assert polarization_loss_db("H", "H") == 0.0

    def test_copol_v(self) -> None:
        assert polarization_loss_db("V", "V") == 0.0

    def test_cross_circular_rhcp_lhcp(self) -> None:
        loss = polarization_loss_db("RHCP", "LHCP")
        assert loss == pytest.approx(25.0)

    def test_cross_circular_lhcp_rhcp(self) -> None:
        loss = polarization_loss_db("LHCP", "RHCP")
        assert loss == pytest.approx(25.0)

    def test_cross_linear_h_v(self) -> None:
        loss = polarization_loss_db("H", "V")
        assert loss == pytest.approx(25.0)

    def test_circular_to_linear_3db(self) -> None:
        assert polarization_loss_db("RHCP", "H") == pytest.approx(3.0)
        assert polarization_loss_db("RHCP", "V") == pytest.approx(3.0)
        assert polarization_loss_db("LHCP", "H") == pytest.approx(3.0)
        assert polarization_loss_db("LHCP", "V") == pytest.approx(3.0)

    def test_linear_to_circular_3db(self) -> None:
        assert polarization_loss_db("H", "RHCP") == pytest.approx(3.0)
        assert polarization_loss_db("V", "LHCP") == pytest.approx(3.0)

    def test_custom_cross_pol(self) -> None:
        loss = polarization_loss_db("RHCP", "LHCP", cross_pol_db=30.0)
        assert loss == pytest.approx(30.0)

    def test_case_insensitive(self) -> None:
        assert polarization_loss_db("rhcp", "lhcp") == pytest.approx(25.0)
        assert polarization_loss_db("Rhcp", "Rhcp") == 0.0
