"""Handover heuristic for multi-satellite scenarios (Tier 2)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HandoverDecision:
    """Result of a handover evaluation at one timestep."""

    selected_sat_idx: int
    selected_sat_id: str
    is_handover: bool
    margin_db: float
    all_margins_db: list[float]


class HandoverPolicy:
    """Hysteresis-based handover policy.

    Selects the satellite with the best metric (margin or elevation).
    A handover from the current satellite only occurs if a candidate
    exceeds the current satellite's metric by ``hysteresis_db`` and
    the hysteresis timer (``hysteresis_s``) has elapsed since the last
    handover.

    Parameters
    ----------
    hysteresis_db : float
        Minimum margin advantage (dB) for a candidate to trigger handover.
    hysteresis_s : float
        Minimum time (seconds) between handovers.
    metric : str
        Selection metric: "margin" or "elevation".
    """

    def __init__(
        self,
        hysteresis_db: float = 3.0,
        hysteresis_s: float = 5.0,
        metric: str = "margin",
    ) -> None:
        if metric not in ("margin", "elevation"):
            raise ValueError(f"metric must be 'margin' or 'elevation', got '{metric}'")
        self.hysteresis_db = hysteresis_db
        self.hysteresis_s = hysteresis_s
        self.metric = metric
        self._current_sat_idx: int = 0
        self._last_handover_t: float = -np.inf

    def reset(self, initial_sat_idx: int = 0) -> None:
        """Reset handover state for a new simulation run."""
        self._current_sat_idx = initial_sat_idx
        self._last_handover_t = -np.inf

    def evaluate(
        self,
        t_s: float,
        sat_ids: list[str],
        metrics: list[float],
        visible: list[bool],
    ) -> HandoverDecision:
        """Evaluate handover decision at one timestep.

        Parameters
        ----------
        t_s : float
            Current simulation time in seconds.
        sat_ids : list[str]
            Satellite identifiers.
        metrics : list[float]
            Per-satellite metric values (margin_db or elevation_deg).
        visible : list[bool]
            Per-satellite visibility flags (above min elevation).

        Returns
        -------
        HandoverDecision
        """
        n_sats = len(sat_ids)
        if n_sats == 0:
            raise ValueError("No satellites to evaluate")

        # Filter to visible satellites
        visible_indices = [i for i in range(n_sats) if visible[i]]

        if not visible_indices:
            # No visible satellites — keep current (will be outage)
            return HandoverDecision(
                selected_sat_idx=self._current_sat_idx,
                selected_sat_id=sat_ids[self._current_sat_idx],
                is_handover=False,
                margin_db=float("nan"),
                all_margins_db=list(metrics),
            )

        # Find best visible candidate
        best_idx = max(visible_indices, key=lambda i: metrics[i])
        best_metric = metrics[best_idx]

        # Current satellite metric (if visible)
        current_visible = self._current_sat_idx in visible_indices
        current_metric = metrics[self._current_sat_idx] if current_visible else -np.inf

        # Handover logic
        time_since_last = t_s - self._last_handover_t
        timer_ok = time_since_last >= self.hysteresis_s

        if not current_visible:
            # Must handover — current satellite not visible
            self._current_sat_idx = best_idx
            self._last_handover_t = t_s
            is_handover = True
        elif best_idx != self._current_sat_idx and timer_ok:
            advantage = best_metric - current_metric
            if advantage > self.hysteresis_db:
                self._current_sat_idx = best_idx
                self._last_handover_t = t_s
                is_handover = True
            else:
                is_handover = False
        else:
            is_handover = False

        return HandoverDecision(
            selected_sat_idx=self._current_sat_idx,
            selected_sat_id=sat_ids[self._current_sat_idx],
            is_handover=is_handover,
            margin_db=metrics[self._current_sat_idx],
            all_margins_db=list(metrics),
        )
