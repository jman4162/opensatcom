"""Capacity map computation — evaluates interference across an az/el grid."""

from __future__ import annotations

import numpy as np

from opensatcom.core.models import PropagationConditions, Terminal
from opensatcom.core.protocols import AntennaModel
from opensatcom.payload.beammap import BeamMap, BeamMapPoint
from opensatcom.payload.beamset import BeamSet
from opensatcom.payload.interference import SimpleInterferenceModel


def _select_serving_beam(
    beamset: BeamSet,
    az_deg: float,
    el_deg: float,
    f_hz: float,
    strategy: str,
) -> str:
    """Select which beam serves a given grid point.

    Parameters
    ----------
    beamset : the multi-beam payload
    az_deg, el_deg : grid point direction
    f_hz : frequency
    strategy : "max_gain" or "nearest"
    """
    if strategy == "nearest":
        best_id = ""
        best_dist = float("inf")
        for beam in beamset:
            d = np.sqrt((beam.az_deg - az_deg) ** 2 + (beam.el_deg - el_deg) ** 2)
            if d < best_dist:
                best_dist = d
                best_id = beam.beam_id
        return best_id
    else:  # "max_gain" (default)
        best_id = ""
        best_gain = -float("inf")
        for beam in beamset:
            g = beam.gain_toward_dbi(az_deg, el_deg, f_hz)
            if g > best_gain:
                best_gain = g
                best_id = beam.beam_id
        return best_id


def compute_beam_map(
    beamset: BeamSet,
    grid_az_deg: np.ndarray,
    grid_el_deg: np.ndarray,
    rx_antenna: AntennaModel,
    rx_terminal: Terminal,
    range_m: float,
    cond: PropagationConditions,
    beam_selection: str = "max_gain",
) -> BeamMap:
    """Compute a beam map (capacity/interference map) over an az/el grid.

    Parameters
    ----------
    beamset : multi-beam payload
    grid_az_deg : 1-D array of azimuth values for the grid
    grid_el_deg : 1-D array of elevation values for the grid
    rx_antenna : victim receive antenna
    rx_terminal : victim terminal (for noise temp)
    range_m : slant range to the victim
    cond : propagation conditions
    beam_selection : "max_gain" (default) or "nearest"

    Returns
    -------
    BeamMap with one point per (az, el) grid combination.
    """
    model = SimpleInterferenceModel()
    f_hz = beamset.scenario.freq_hz
    points: list[BeamMapPoint] = []

    for az in grid_az_deg:
        for el in grid_el_deg:
            az_f = float(az)
            el_f = float(el)

            serving_id = _select_serving_beam(
                beamset, az_f, el_f, f_hz, beam_selection
            )

            result = model.evaluate(
                beamset, serving_id, az_f, el_f,
                range_m, rx_antenna, rx_terminal, cond,
            )

            points.append(BeamMapPoint(az_f, el_f, serving_id, result))

    return BeamMap(points)
