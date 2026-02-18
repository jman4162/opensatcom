"""Resource schedulers for network-level simulation."""

from __future__ import annotations

from opensatcom.world.traffic import TrafficDemand


class ProportionalFairScheduler:
    """Allocates capacity proportional to demand and channel quality.

    Proportional fair: each user gets capacity proportional to their
    demand weighted by priority, subject to total capacity constraint.

    Parameters
    ----------
    alpha : float
        Fairness parameter. alpha=1.0 is pure proportional fair.
    """

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = alpha

    def allocate(
        self, users: list[TrafficDemand], capacity_mbps: float
    ) -> dict[str, float]:
        """Allocate capacity across users.

        Returns dict mapping user_id to allocated Mbps.
        Total allocation never exceeds capacity_mbps.
        """
        if not users or capacity_mbps <= 0:
            return {u.user_id: 0.0 for u in users}

        # Weighted demand: demand * (priority + 1) ^ alpha
        weights = {}
        for u in users:
            w = u.demand_mbps * ((u.priority + 1) ** self.alpha)
            weights[u.user_id] = max(w, 0.0)

        total_weight = sum(weights.values())
        if total_weight <= 0:
            return {u.user_id: 0.0 for u in users}

        # Proportional allocation
        allocation: dict[str, float] = {}
        total_demand = sum(u.demand_mbps for u in users)

        if total_demand <= capacity_mbps:
            # Enough capacity for everyone
            for u in users:
                allocation[u.user_id] = u.demand_mbps
        else:
            # Proportional fair split
            for u in users:
                share = weights[u.user_id] / total_weight
                allocated = share * capacity_mbps
                # Don't allocate more than demanded
                allocation[u.user_id] = min(allocated, u.demand_mbps)

        return allocation


class RoundRobinScheduler:
    """Simple round-robin scheduler: equal share to each user.

    Each user gets capacity / n_users, capped at their demand.
    Remaining capacity from users whose demand is below their equal
    share is not redistributed.
    """

    def allocate(
        self, users: list[TrafficDemand], capacity_mbps: float
    ) -> dict[str, float]:
        """Allocate capacity equally across users.

        Parameters
        ----------
        users : list[TrafficDemand]
            List of user traffic demands to schedule.
        capacity_mbps : float
            Total available capacity in Mbps.

        Returns
        -------
        dict[str, float]
            Mapping of user_id to allocated throughput in Mbps.
        """
        if not users or capacity_mbps <= 0:
            return {u.user_id: 0.0 for u in users}

        equal_share = capacity_mbps / len(users)
        allocation: dict[str, float] = {}

        # First pass: allocate min(equal_share, demand)
        remaining = capacity_mbps
        unsatisfied = []
        for u in users:
            alloc = min(equal_share, u.demand_mbps)
            allocation[u.user_id] = alloc
            remaining -= alloc
            if alloc < equal_share and remaining > 0:
                pass  # User doesn't need full share
            elif alloc >= u.demand_mbps:
                remaining += 0  # Already handled
            else:
                unsatisfied.append(u.user_id)

        return allocation
