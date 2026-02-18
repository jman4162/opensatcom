"""Tests for Beam datamodel."""

import pytest

from opensatcom.antenna.cosine import CosineRolloffAntenna
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.payload.beam import Beam


class TestBeam:
    def test_construction(self) -> None:
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        beam = Beam(
            beam_id="B1", az_deg=0.0, el_deg=0.0,
            tx_power_w=100.0, antenna=ant,
        )
        assert beam.beam_id == "B1"
        assert beam.az_deg == 0.0
        assert beam.el_deg == 0.0
        assert beam.tx_power_w == 100.0

    def test_gain_toward_boresight(self) -> None:
        """Gain at boresight should equal peak gain."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        beam = Beam("B1", 0.0, 0.0, 100.0, ant)
        assert beam.gain_toward_dbi(0.0, 0.0, 19.7e9) == pytest.approx(35.0)

    def test_gain_off_axis(self) -> None:
        """Gain off-axis should be less than peak."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        beam = Beam("B1", 0.0, 0.0, 100.0, ant)
        assert beam.gain_toward_dbi(3.0, 0.0, 19.7e9) < 35.0

    def test_eirp_toward(self) -> None:
        from opensatcom.core.units import w_to_dbw

        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        beam = Beam("B1", 0.0, 0.0, 100.0, ant)
        eirp = beam.eirp_toward_dbw(0.0, 0.0, 19.7e9)
        assert eirp == pytest.approx(w_to_dbw(100.0) + 35.0)

    def test_frozen(self) -> None:
        ant = ParametricAntenna(gain_dbi=30.0)
        beam = Beam("B1", 0.0, 0.0, 100.0, ant)
        with pytest.raises(AttributeError):
            beam.beam_id = "B2"  # type: ignore[misc]

    def test_with_parametric_antenna(self) -> None:
        """Beam works with any AntennaModel (ParametricAntenna gives constant gain)."""
        ant = ParametricAntenna(gain_dbi=30.0)
        beam = Beam("B1", 0.0, 0.0, 50.0, ant)
        # Parametric antenna returns same gain everywhere
        assert beam.gain_toward_dbi(0.0, 0.0, 19.7e9) == pytest.approx(30.0)
        assert beam.gain_toward_dbi(10.0, 10.0, 19.7e9) == pytest.approx(30.0)
