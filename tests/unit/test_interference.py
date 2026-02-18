"""Tests for the interference model."""

import math

import pytest

from opensatcom.antenna.cosine import CosineRolloffAntenna
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.models import (
    PropagationConditions,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.payload.beam import Beam
from opensatcom.payload.beamset import BeamSet
from opensatcom.payload.interference import InterferenceResult, SimpleInterferenceModel
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation


def _make_scenario() -> Scenario:
    return Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)


def _make_rx_terminal() -> Terminal:
    return Terminal("ut", 0.0, 0.0, 0.0, system_noise_temp_k=500.0)


def _make_rf() -> RFChainModel:
    return RFChainModel(tx_power_w=100.0, tx_losses_db=0.0, rx_noise_temp_k=500.0)


class TestInterferenceResult:
    def test_frozen(self) -> None:
        r = InterferenceResult(
            serving_beam_id="B0", signal_dbw=10.0, interference_dbw=-30.0,
            noise_dbw=-20.0, cnir_db=20.0, sinr_db=40.0,
            cn0_dbhz=80.0, ebn0_db=10.0, margin_db=4.0,
        )
        with pytest.raises(AttributeError):
            r.sinr_db = 99.0  # type: ignore[misc]


class TestSimpleInterferenceModel:
    def test_single_beam_no_interference(self) -> None:
        """With a single beam, interference is zero and SINR is infinite."""
        ant = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        beam = Beam("B0", 0.0, 0.0, 100.0, ant)
        sc = _make_scenario()
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = _make_rf()
        bs = BeamSet([beam], sc, prop, rf)

        model = SimpleInterferenceModel()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = _make_rx_terminal()

        result = model.evaluate(
            bs, "B0", 0.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        assert result.serving_beam_id == "B0"
        assert result.sinr_db == math.inf
        assert result.signal_dbw > -100  # some reasonable signal level
        assert result.cn0_dbhz > 50.0  # physically plausible C/N0
        assert result.margin_db > 0.0

    def test_single_beam_matches_link_engine(self) -> None:
        """Single beam interference result should match DefaultLinkEngine C/N0."""
        from opensatcom.core.models import LinkInputs
        from opensatcom.link.engine import DefaultLinkEngine

        ant = ParametricAntenna(gain_dbi=35.0)
        beam = Beam("B0", 0.0, 0.0, 100.0, ant)
        sc = _make_scenario()
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = _make_rf()
        bs = BeamSet([beam], sc, prop, rf)

        # Interference model
        model = SimpleInterferenceModel()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = _make_rx_terminal()
        result = model.evaluate(
            bs, "B0", 0.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        # Reference: DefaultLinkEngine
        tx_term = Terminal("sat", 0.0, 0.0, 550e3)
        link_inputs = LinkInputs(
            tx_terminal=tx_term,
            rx_terminal=rx_term,
            scenario=sc,
            tx_antenna=ant,
            rx_antenna=rx_ant,
            propagation=prop,
            rf_chain=rf,
        )
        engine = DefaultLinkEngine()
        link_out = engine.evaluate_snapshot(
            elev_deg=0.0, az_deg=0.0, range_m=1200e3,
            inputs=link_inputs, cond=PropagationConditions(),
        )

        # C/N0 should match (both use same EIRP, path loss, G/T)
        assert result.cn0_dbhz == pytest.approx(link_out.cn0_dbhz, abs=0.01)

    def test_two_beams_finite_sinr(self) -> None:
        """Two beams: interference from non-serving beam produces finite SINR."""
        ant0 = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        ant1 = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=5.0, boresight_el_deg=0.0,
        )
        beam0 = Beam("B0", 0.0, 0.0, 100.0, ant0)
        beam1 = Beam("B1", 5.0, 0.0, 100.0, ant1)

        sc = _make_scenario()
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = _make_rf()
        bs = BeamSet([beam0, beam1], sc, prop, rf)

        model = SimpleInterferenceModel()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = _make_rx_terminal()

        # Evaluate at boresight of B0 — B1 is 5° away
        result = model.evaluate(
            bs, "B0", 0.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        assert result.sinr_db < math.inf
        assert result.sinr_db > 0  # serving beam should dominate at boresight
        assert result.interference_dbw < result.signal_dbw
        assert result.cnir_db < result.cn0_dbhz  # C/(N+I) < C/N0

    def test_interference_summed_in_linear(self) -> None:
        """Interference from multiple beams should sum in linear domain."""
        # Create 3 beams with identical power at different angles
        beams = []
        for i in range(3):
            ant = CosineRolloffAntenna(
                peak_gain_dbi=35.0, theta_3db_deg=2.0,
                boresight_az_deg=float(i * 5), boresight_el_deg=0.0,
            )
            beams.append(Beam(f"B{i}", float(i * 5), 0.0, 100.0, ant))

        sc = _make_scenario()
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = _make_rf()
        bs = BeamSet(beams, sc, prop, rf)

        model = SimpleInterferenceModel()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = _make_rx_terminal()

        # At B0 boresight: B1 and B2 interfere
        result_3beam = model.evaluate(
            bs, "B0", 0.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        # With only B0 and B1: less interference
        bs2 = BeamSet(beams[:2], sc, prop, rf)
        result_2beam = model.evaluate(
            bs2, "B0", 0.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        # More interferers = worse SINR
        assert result_3beam.sinr_db < result_2beam.sinr_db

    def test_midpoint_between_beams(self) -> None:
        """At midpoint between two beams, both beams have equal gain → SINR ~0 dB."""
        ant0 = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=0.0, boresight_el_deg=0.0,
        )
        ant1 = CosineRolloffAntenna(
            peak_gain_dbi=35.0, theta_3db_deg=2.0,
            boresight_az_deg=4.0, boresight_el_deg=0.0,
        )
        beam0 = Beam("B0", 0.0, 0.0, 100.0, ant0)
        beam1 = Beam("B1", 4.0, 0.0, 100.0, ant1)

        sc = _make_scenario()
        prop = CompositePropagation([FreeSpacePropagation()])
        rf = _make_rf()
        bs = BeamSet([beam0, beam1], sc, prop, rf)

        model = SimpleInterferenceModel()
        rx_ant = ParametricAntenna(gain_dbi=35.0)
        rx_term = _make_rx_terminal()

        # At midpoint (2, 0): both beams have equal gain
        result = model.evaluate(
            bs, "B0", 2.0, 0.0, 1200e3, rx_ant, rx_term, PropagationConditions()
        )

        # SINR should be ~0 dB (equal signal and interference)
        assert result.sinr_db == pytest.approx(0.0, abs=0.01)
