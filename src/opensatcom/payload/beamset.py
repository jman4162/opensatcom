"""BeamSet — collection of beams forming a multi-beam payload."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from opensatcom.payload.beam import Beam

if TYPE_CHECKING:
    from opensatcom.core.models import RFChainModel, Scenario
    from opensatcom.core.protocols import PropagationModel


class BeamSet:
    """A set of satellite beams sharing common scenario, propagation, and RF chain.

    Parameters
    ----------
    beams : list[Beam]
        List of Beam objects forming the multi-beam payload.
    scenario : Scenario
        Link scenario defining frequency, bandwidth, and requirements.
    propagation : PropagationModel
        Propagation model used for path loss computation.
    rf_chain : RFChainModel
        Shared RF chain parameters (e.g., noise temperature).
    """

    def __init__(
        self,
        beams: list[Beam],
        scenario: Scenario,
        propagation: PropagationModel,
        rf_chain: RFChainModel,
    ) -> None:
        self._beams = list(beams)
        self._beam_map = {b.beam_id: b for b in self._beams}
        self.scenario = scenario
        self.propagation = propagation
        self.rf_chain = rf_chain

    def get_beam(self, beam_id: str) -> Beam:
        """Look up a beam by its ID.

        Parameters
        ----------
        beam_id : str
            Unique identifier of the beam to retrieve.

        Returns
        -------
        Beam
            The beam matching the given ID.
        """
        return self._beam_map[beam_id]

    @property
    def beam_ids(self) -> list[str]:
        """List of beam IDs in insertion order."""
        return [b.beam_id for b in self._beams]

    def __len__(self) -> int:
        return len(self._beams)

    def __iter__(self) -> Iterator[Beam]:
        return iter(self._beams)

    def __getitem__(self, idx: int) -> Beam:
        return self._beams[idx]
