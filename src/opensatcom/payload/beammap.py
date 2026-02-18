"""BeamMap — grid of interference evaluation points for capacity mapping."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
import pandas as pd

from opensatcom.payload.interference import InterferenceResult


@dataclass(frozen=True)
class BeamMapPoint:
    """A single evaluated point in the beam map grid."""

    az_deg: float
    el_deg: float
    serving_beam_id: str
    result: InterferenceResult


class BeamMap:
    """Collection of evaluated beam map points with analysis methods.

    Parameters
    ----------
    points : list of BeamMapPoint, each holding interference evaluation results
    """

    def __init__(self, points: list[BeamMapPoint]) -> None:
        self._points = list(points)

    @property
    def points(self) -> list[BeamMapPoint]:
        return list(self._points)

    def __len__(self) -> int:
        return len(self._points)

    def __iter__(self) -> Iterator[BeamMapPoint]:
        return iter(self._points)

    def to_dataframe(self) -> pd.DataFrame:
        """Export beam map to a DataFrame for analysis and persistence."""
        records = []
        for p in self._points:
            r = p.result
            records.append({
                "az_deg": p.az_deg,
                "el_deg": p.el_deg,
                "serving_beam_id": p.serving_beam_id,
                "signal_dbw": r.signal_dbw,
                "interference_dbw": r.interference_dbw,
                "noise_dbw": r.noise_dbw,
                "cnir_db": r.cnir_db,
                "sinr_db": r.sinr_db,
                "cn0_dbhz": r.cn0_dbhz,
                "ebn0_db": r.ebn0_db,
                "margin_db": r.margin_db,
                "throughput_mbps": r.throughput_mbps,
            })
        return pd.DataFrame(records)

    @property
    def sinr_db_mean(self) -> float:
        """Mean SINR across all points (excluding inf)."""
        vals = [p.result.sinr_db for p in self._points if np.isfinite(p.result.sinr_db)]
        return float(np.mean(vals)) if vals else 0.0

    @property
    def sinr_db_min(self) -> float:
        """Minimum SINR across all points."""
        vals = [p.result.sinr_db for p in self._points if np.isfinite(p.result.sinr_db)]
        return float(np.min(vals)) if vals else 0.0

    @property
    def cnir_db_mean(self) -> float:
        """Mean C/(N+I) across all points."""
        vals = [p.result.cnir_db for p in self._points]
        return float(np.mean(vals))

    @property
    def margin_db_mean(self) -> float:
        """Mean margin across all points."""
        vals = [p.result.margin_db for p in self._points]
        return float(np.mean(vals))

    @property
    def throughput_mbps_total(self) -> float:
        """Total throughput summed across all points."""
        vals = [
            p.result.throughput_mbps
            for p in self._points
            if p.result.throughput_mbps is not None
        ]
        return float(np.sum(vals)) if vals else 0.0

    def per_beam_summary(self) -> dict[str, dict[str, float]]:
        """Per-beam summary statistics.

        Returns dict mapping beam_id -> {points_served, sinr_db_mean, margin_db_mean}.
        """
        from collections import defaultdict

        beam_points: dict[str, list[BeamMapPoint]] = defaultdict(list)
        for p in self._points:
            beam_points[p.serving_beam_id].append(p)

        summary = {}
        for bid, pts in beam_points.items():
            sinr_vals = [p.result.sinr_db for p in pts if np.isfinite(p.result.sinr_db)]
            summary[bid] = {
                "points_served": float(len(pts)),
                "sinr_db_mean": float(np.mean(sinr_vals)) if sinr_vals else 0.0,
                "margin_db_mean": float(np.mean([p.result.margin_db for p in pts])),
            }
        return summary
