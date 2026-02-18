"""Composite propagation model summing multiple loss components."""

from __future__ import annotations

from collections.abc import Sequence

from opensatcom.core.models import PropagationConditions
from opensatcom.core.protocols import PropagationModel


class CompositePropagation:
    """Sum losses in dB across multiple propagation components.

    Combines FSPL with atmospheric, rain, and scintillation losses.
    Each component's ``total_path_loss_db`` is called and the results
    are summed in dB domain.

    Parameters
    ----------
    components : Sequence of PropagationModel
        Ordered list of propagation models to combine.

    Examples
    --------
    >>> from opensatcom.propagation import FreeSpacePropagation
    >>> comp = CompositePropagation([FreeSpacePropagation()])
    """

    def __init__(self, components: Sequence[PropagationModel]) -> None:
        self.components = components

    def total_path_loss_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> float:
        """Compute total composite path loss.

        Parameters
        ----------
        f_hz : float
            Carrier frequency in Hz.
        elev_deg : float
            Elevation angle in degrees.
        range_m : float
            Slant range in metres.
        cond : PropagationConditions
            Environmental conditions.

        Returns
        -------
        float
            Sum of all component losses in dB.
        """
        return sum(
            c.total_path_loss_db(f_hz, elev_deg, range_m, cond)
            for c in self.components
        )
