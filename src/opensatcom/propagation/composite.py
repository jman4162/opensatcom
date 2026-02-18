"""Composite propagation model summing multiple loss components."""

from __future__ import annotations

from collections.abc import Sequence

from opensatcom.core.models import PropagationConditions
from opensatcom.core.protocols import PropagationModel


class CompositePropagation:
    """Sum losses in dB across multiple propagation components."""

    def __init__(self, components: Sequence[PropagationModel]) -> None:
        self.components = components

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        return sum(
            c.total_path_loss_db(f_hz, elev_deg, range_m, cond)
            for c in self.components
        )
