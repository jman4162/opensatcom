"""Performance curve implementations for modem Eb/N0 vs BLER mapping."""

from __future__ import annotations

import numpy as np


class TablePerformanceCurve:
    """Table-based performance curve using interpolation.

    Accepts a list of (ebn0_db, bler) points sorted by ebn0_db ascending.
    Uses np.interp for lookup — no scipy dependency.

    Parameters
    ----------
    points : list[tuple[float, float]]
        List of (ebn0_db, bler) pairs defining the performance curve.
        Points are sorted internally by ebn0_db ascending.
    """

    def __init__(self, points: list[tuple[float, float]]) -> None:
        sorted_pts = sorted(points, key=lambda p: p[0])
        self._ebn0_db = np.array([p[0] for p in sorted_pts])
        self._bler = np.array([p[1] for p in sorted_pts])

    def bler(self, ebn0_db: float) -> float:
        """Interpolate BLER at given Eb/N0.

        Parameters
        ----------
        ebn0_db : float
            Energy per bit to noise spectral density ratio in dB.

        Returns
        -------
        float
            Interpolated block error rate at the given Eb/N0.
        """
        return float(np.interp(ebn0_db, self._ebn0_db, self._bler))

    def required_ebn0_db(self, target_bler: float) -> float:
        """Find Eb/N0 required to achieve target BLER.

        Interpolates in reversed BLER→Eb/N0 direction (BLER decreases with Eb/N0).

        Parameters
        ----------
        target_bler : float
            Desired block error rate threshold.

        Returns
        -------
        float
            Required Eb/N0 in dB to achieve the target BLER.
        """
        # BLER is monotonically decreasing with Eb/N0, so reverse for interp
        return float(
            np.interp(target_bler, self._bler[::-1], self._ebn0_db[::-1])
        )
