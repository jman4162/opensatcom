"""Beam datamodel for multi-beam payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from opensatcom.core.protocols import AntennaModel


@dataclass(frozen=True)
class Beam:
    """A single satellite beam with its own antenna pattern.

    Attributes
    ----------
    beam_id : unique identifier for this beam
    az_deg : boresight azimuth (deg)
    el_deg : boresight elevation (deg)
    tx_power_w : transmit power allocated to this beam (watts)
    antenna : antenna model describing the beam's radiation pattern
    """

    beam_id: str
    az_deg: float
    el_deg: float
    tx_power_w: float
    antenna: AntennaModel

    def gain_toward_dbi(self, az_deg: float, el_deg: float, f_hz: float) -> float:
        """Evaluate beam antenna gain toward a specific direction.

        Parameters
        ----------
        az_deg : target azimuth (deg)
        el_deg : target elevation (deg)
        f_hz : frequency (Hz)

        Returns
        -------
        Gain in dBi toward the specified direction.
        """
        theta = np.array([az_deg])
        phi = np.array([el_deg])
        return float(self.antenna.gain_dbi(theta, phi, f_hz)[0])

    def eirp_toward_dbw(self, az_deg: float, el_deg: float, f_hz: float) -> float:
        """EIRP toward a specific direction."""
        gain = self.gain_toward_dbi(az_deg, el_deg, f_hz)
        from opensatcom.core.units import w_to_dbw

        return w_to_dbw(self.tx_power_w) + gain
