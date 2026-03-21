"""Composite propagation model summing multiple loss components."""

from __future__ import annotations

from collections.abc import Sequence

from opensatcom.core.models import PropagationConditions
from opensatcom.core.protocols import PropagationModel

# Map class names to standard breakdown keys
_COMPONENT_KEY_MAP: dict[str, str] = {
    "FreeSpacePropagation": "fspl_db",
    "RainAttenuationP618": "rain_attenuation_db",
    "GaseousAbsorptionP676": "gaseous_absorption_db",
    "ScintillationLoss": "scintillation_db",
}


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

    def per_component_losses_db(
        self,
        f_hz: float,
        elev_deg: float,
        range_m: float,
        cond: PropagationConditions,
    ) -> dict[str, float]:
        """Compute per-component path losses.

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
        dict of str to float
            Mapping from component key name to its loss in dB.
            Keys use standard names: ``fspl_db``, ``rain_attenuation_db``,
            ``gaseous_absorption_db``, ``scintillation_db``.
        """
        result: dict[str, float] = {}
        for comp in self.components:
            class_name = type(comp).__name__
            key = _COMPONENT_KEY_MAP.get(class_name, f"{class_name}_db")
            result[key] = comp.total_path_loss_db(f_hz, elev_deg, range_m, cond)
        return result
