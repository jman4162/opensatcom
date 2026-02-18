"""Tests for traffic demand models."""

import pytest

from opensatcom.world.traffic import (
    ConstantTrafficProfile,
    TimeVaryingTrafficProfile,
    TrafficDemand,
)


class TestTrafficDemand:
    def test_construction(self) -> None:
        d = TrafficDemand(user_id="u1", demand_mbps=10.0)
        assert d.user_id == "u1"
        assert d.demand_mbps == 10.0
        assert d.priority == 0

    def test_with_priority(self) -> None:
        d = TrafficDemand(user_id="u1", demand_mbps=5.0, priority=2)
        assert d.priority == 2


class TestConstantTrafficProfile:
    def test_returns_same_at_all_times(self) -> None:
        demands = [
            TrafficDemand(user_id="u1", demand_mbps=10.0),
            TrafficDemand(user_id="u2", demand_mbps=5.0),
        ]
        profile = ConstantTrafficProfile(demands)
        d0 = profile.demands_at(0.0)
        d100 = profile.demands_at(100.0)
        assert len(d0) == 2
        assert len(d100) == 2
        assert d0[0].demand_mbps == d100[0].demand_mbps

    def test_returns_copy(self) -> None:
        demands = [TrafficDemand(user_id="u1", demand_mbps=10.0)]
        profile = ConstantTrafficProfile(demands)
        d1 = profile.demands_at(0.0)
        d2 = profile.demands_at(0.0)
        assert d1 is not d2


class TestTimeVaryingTrafficProfile:
    def test_ramp_increases(self) -> None:
        base = [TrafficDemand(user_id="u1", demand_mbps=10.0)]
        profile = TimeVaryingTrafficProfile(
            base, pattern="ramp", ramp_factor=2.0, t_start_s=0.0, t_end_s=100.0
        )
        d_start = profile.demands_at(0.0)
        d_end = profile.demands_at(100.0)
        assert d_end[0].demand_mbps > d_start[0].demand_mbps
        assert d_end[0].demand_mbps == pytest.approx(20.0)

    def test_burst_pattern(self) -> None:
        base = [TrafficDemand(user_id="u1", demand_mbps=10.0)]
        profile = TimeVaryingTrafficProfile(
            base, pattern="burst",
            burst_period_s=60.0, burst_multiplier=3.0, burst_duration_s=10.0,
        )
        d_burst = profile.demands_at(5.0)  # Within burst
        d_normal = profile.demands_at(30.0)  # Outside burst
        assert d_burst[0].demand_mbps == pytest.approx(30.0)
        assert d_normal[0].demand_mbps == pytest.approx(10.0)
