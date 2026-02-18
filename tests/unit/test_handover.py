"""Tests for handover policy."""

import numpy as np
import pytest

from opensatcom.world.handover import HandoverPolicy


class TestHandoverPolicy:
    def test_construction(self) -> None:
        policy = HandoverPolicy(hysteresis_db=3.0, hysteresis_s=5.0)
        assert policy.hysteresis_db == 3.0
        assert policy.hysteresis_s == 5.0

    def test_invalid_metric(self) -> None:
        with pytest.raises(ValueError, match="metric must be"):
            HandoverPolicy(metric="invalid")

    def test_single_sat_no_handover(self) -> None:
        """With one satellite, never handover."""
        policy = HandoverPolicy()
        policy.reset()
        d = policy.evaluate(0.0, ["sat1"], [10.0], [True])
        assert d.selected_sat_idx == 0
        assert d.selected_sat_id == "sat1"
        assert not d.is_handover

    def test_selects_best_initial(self) -> None:
        """First evaluation picks the best visible satellite."""
        policy = HandoverPolicy(hysteresis_db=0.0, hysteresis_s=0.0)
        policy.reset(initial_sat_idx=0)
        # sat2 has better margin
        d = policy.evaluate(
            0.0, ["sat1", "sat2"], [5.0, 15.0], [True, True]
        )
        # Initial sat is 0, but sat2 is better by 10 dB > hysteresis 0
        assert d.selected_sat_idx == 1
        assert d.is_handover

    def test_hysteresis_prevents_premature_handover(self) -> None:
        """Small advantage doesn't trigger handover."""
        policy = HandoverPolicy(hysteresis_db=5.0, hysteresis_s=0.0)
        policy.reset(initial_sat_idx=0)

        # sat2 better by only 2 dB < hysteresis 5 dB
        d = policy.evaluate(
            0.0, ["sat1", "sat2"], [10.0, 12.0], [True, True]
        )
        assert d.selected_sat_idx == 0
        assert not d.is_handover

    def test_hysteresis_timer(self) -> None:
        """Handover blocked if too recent."""
        policy = HandoverPolicy(hysteresis_db=1.0, hysteresis_s=10.0)
        policy.reset(initial_sat_idx=0)

        # Force a handover at t=0
        d1 = policy.evaluate(
            0.0, ["sat1", "sat2"], [0.0, 20.0], [True, True]
        )
        assert d1.selected_sat_idx == 1
        assert d1.is_handover

        # At t=5, sat1 is better but timer not elapsed (10s)
        d2 = policy.evaluate(
            5.0, ["sat1", "sat2"], [25.0, 5.0], [True, True]
        )
        assert d2.selected_sat_idx == 1  # stays on sat2
        assert not d2.is_handover

        # At t=11, timer elapsed, sat1 much better
        d3 = policy.evaluate(
            11.0, ["sat1", "sat2"], [25.0, 5.0], [True, True]
        )
        assert d3.selected_sat_idx == 0  # handover to sat1
        assert d3.is_handover

    def test_forced_handover_when_invisible(self) -> None:
        """Handover forced when current satellite becomes invisible."""
        policy = HandoverPolicy(hysteresis_db=100.0, hysteresis_s=100.0)
        policy.reset(initial_sat_idx=0)

        # Current sat not visible, must handover regardless of hysteresis
        d = policy.evaluate(
            0.0, ["sat1", "sat2"], [0.0, 10.0], [False, True]
        )
        assert d.selected_sat_idx == 1
        assert d.is_handover

    def test_no_visible_sats(self) -> None:
        """When no satellites visible, keep current (outage)."""
        policy = HandoverPolicy()
        policy.reset(initial_sat_idx=0)
        d = policy.evaluate(
            0.0, ["sat1", "sat2"], [0.0, 0.0], [False, False]
        )
        assert d.selected_sat_idx == 0
        assert not d.is_handover
        assert np.isnan(d.margin_db)

    def test_elevation_metric(self) -> None:
        """Handover using elevation metric."""
        policy = HandoverPolicy(hysteresis_db=5.0, hysteresis_s=0.0, metric="elevation")
        policy.reset(initial_sat_idx=0)

        # sat2 has much higher elevation
        d = policy.evaluate(
            0.0, ["sat1", "sat2"], [20.0, 70.0], [True, True]
        )
        assert d.selected_sat_idx == 1

    def test_reset(self) -> None:
        """Reset restores initial state."""
        policy = HandoverPolicy()
        policy.reset(initial_sat_idx=1)
        d = policy.evaluate(
            0.0, ["sat1", "sat2"], [10.0, 10.0], [True, True]
        )
        assert d.selected_sat_idx == 1  # stays on initial

    def test_empty_sats_rejected(self) -> None:
        policy = HandoverPolicy()
        policy.reset()
        with pytest.raises(ValueError, match="No satellites"):
            policy.evaluate(0.0, [], [], [])

    def test_all_margins_in_decision(self) -> None:
        """Decision includes all satellite margins."""
        policy = HandoverPolicy()
        policy.reset()
        d = policy.evaluate(
            0.0, ["a", "b", "c"], [5.0, 10.0, 3.0], [True, True, True]
        )
        assert d.all_margins_db == [5.0, 10.0, 3.0]
