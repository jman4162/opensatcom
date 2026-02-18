"""Tests for BeamSet."""

import pytest

from opensatcom.antenna.cosine import CosineRolloffAntenna
from opensatcom.core.models import RFChainModel, Scenario
from opensatcom.payload.beam import Beam
from opensatcom.payload.beamset import BeamSet
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation


def _make_beamset(n_beams: int = 3) -> BeamSet:
    """Helper to create a BeamSet with n beams."""
    beams = []
    for i in range(n_beams):
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=float(i * 5), boresight_el_deg=0.0,
        )
        beams.append(Beam(f"B{i}", float(i * 5), 0.0, 100.0, ant))

    scenario = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=100.0, tx_losses_db=2.0, rx_noise_temp_k=500.0)
    return BeamSet(beams, scenario, prop, rf)


class TestBeamSet:
    def test_len(self) -> None:
        bs = _make_beamset(3)
        assert len(bs) == 3

    def test_beam_ids(self) -> None:
        bs = _make_beamset(3)
        assert bs.beam_ids == ["B0", "B1", "B2"]

    def test_get_beam(self) -> None:
        bs = _make_beamset(3)
        b1 = bs.get_beam("B1")
        assert b1.beam_id == "B1"
        assert b1.az_deg == 5.0

    def test_get_beam_missing(self) -> None:
        bs = _make_beamset(2)
        with pytest.raises(KeyError):
            bs.get_beam("B99")

    def test_iter(self) -> None:
        bs = _make_beamset(3)
        ids = [b.beam_id for b in bs]
        assert ids == ["B0", "B1", "B2"]

    def test_getitem(self) -> None:
        bs = _make_beamset(3)
        assert bs[0].beam_id == "B0"
        assert bs[2].beam_id == "B2"

    def test_shared_scenario(self) -> None:
        bs = _make_beamset(2)
        assert bs.scenario.freq_hz == 19.7e9
