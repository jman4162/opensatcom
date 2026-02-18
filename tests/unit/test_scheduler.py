"""Tests for resource schedulers."""

import pytest

from opensatcom.world.scheduler import ProportionalFairScheduler, RoundRobinScheduler
from opensatcom.world.traffic import TrafficDemand


class TestProportionalFairScheduler:
    def test_allocates_proportionally(self) -> None:
        users = [
            TrafficDemand(user_id="u1", demand_mbps=10.0),
            TrafficDemand(user_id="u2", demand_mbps=30.0),
        ]
        sched = ProportionalFairScheduler()
        alloc = sched.allocate(users, capacity_mbps=20.0)
        assert alloc["u1"] + alloc["u2"] <= 20.0 + 1e-6
        assert alloc["u2"] > alloc["u1"]  # Higher demand gets more

    def test_total_never_exceeds_capacity(self) -> None:
        users = [
            TrafficDemand(user_id="u1", demand_mbps=100.0),
            TrafficDemand(user_id="u2", demand_mbps=100.0),
        ]
        sched = ProportionalFairScheduler()
        alloc = sched.allocate(users, capacity_mbps=50.0)
        assert sum(alloc.values()) <= 50.0 + 1e-6

    def test_full_capacity_when_demand_low(self) -> None:
        users = [
            TrafficDemand(user_id="u1", demand_mbps=5.0),
            TrafficDemand(user_id="u2", demand_mbps=5.0),
        ]
        sched = ProportionalFairScheduler()
        alloc = sched.allocate(users, capacity_mbps=100.0)
        assert alloc["u1"] == pytest.approx(5.0)
        assert alloc["u2"] == pytest.approx(5.0)

    def test_empty_users(self) -> None:
        sched = ProportionalFairScheduler()
        alloc = sched.allocate([], capacity_mbps=100.0)
        assert alloc == {}


class TestRoundRobinScheduler:
    def test_splits_evenly(self) -> None:
        users = [
            TrafficDemand(user_id="u1", demand_mbps=100.0),
            TrafficDemand(user_id="u2", demand_mbps=100.0),
        ]
        sched = RoundRobinScheduler()
        alloc = sched.allocate(users, capacity_mbps=50.0)
        assert alloc["u1"] == pytest.approx(25.0)
        assert alloc["u2"] == pytest.approx(25.0)

    def test_caps_at_demand(self) -> None:
        users = [
            TrafficDemand(user_id="u1", demand_mbps=5.0),
            TrafficDemand(user_id="u2", demand_mbps=100.0),
        ]
        sched = RoundRobinScheduler()
        alloc = sched.allocate(users, capacity_mbps=100.0)
        assert alloc["u1"] == pytest.approx(5.0)  # Capped at demand

    def test_total_never_exceeds_capacity(self) -> None:
        users = [
            TrafficDemand(user_id=f"u{i}", demand_mbps=100.0)
            for i in range(10)
        ]
        sched = RoundRobinScheduler()
        alloc = sched.allocate(users, capacity_mbps=50.0)
        assert sum(alloc.values()) <= 50.0 + 1e-6
