"""Golden test vectors for network simulation."""

import pytest

from opensatcom.world.scheduler import ProportionalFairScheduler
from opensatcom.world.traffic import TrafficDemand


@pytest.mark.golden
class TestNetworkGolden:
    def test_proportional_fair_2_users(self) -> None:
        """Frozen: 2 users with known demands and limited capacity."""
        users = [
            TrafficDemand(user_id="u1", demand_mbps=20.0),
            TrafficDemand(user_id="u2", demand_mbps=40.0),
        ]
        sched = ProportionalFairScheduler()
        alloc = sched.allocate(users, capacity_mbps=30.0)

        # u1 demands 20, u2 demands 40, total=60, capacity=30
        # Proportional: u1 gets 20/60*30=10, u2 gets 40/60*30=20
        assert alloc["u1"] == pytest.approx(10.0, abs=0.1)
        assert alloc["u2"] == pytest.approx(20.0, abs=0.1)
        assert alloc["u1"] + alloc["u2"] <= 30.0 + 0.01
