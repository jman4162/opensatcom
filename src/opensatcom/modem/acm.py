"""Adaptive Coding and Modulation policy with hysteresis."""

from __future__ import annotations

from opensatcom.core.models import ModCod
from opensatcom.core.protocols import PerformanceCurve


class HysteresisACMPolicy:
    """ACM policy with hysteresis to prevent ModCod flapping.

    ModCods are sorted by required Eb/N0 (ascending = least demanding first).
    Step down (to lower ModCod) immediately when Eb/N0 drops below threshold.
    Step up (to higher ModCod) only when Eb/N0 exceeds threshold + hysteresis
    and hold time has elapsed since last switch.

    Parameters
    ----------
    modcods : list[ModCod]
        Available ModCod configurations to select from.
    curves : dict[str, PerformanceCurve]
        Mapping of ModCod name to its performance curve, used to look up
        the required Eb/N0 for each ModCod at the target BLER.
    target_bler : float
        Target block error rate used to compute Eb/N0 thresholds.
    hysteresis_db : float, optional
        Additional Eb/N0 margin (in dB) required to step up to a higher
        ModCod, preventing rapid oscillation. Default is 0.5.
    hold_time_s : float, optional
        Minimum time (in seconds) that must elapse after the last ModCod
        switch before an upstep is permitted. Default is 2.0.
    """

    def __init__(
        self,
        modcods: list[ModCod],
        curves: dict[str, PerformanceCurve],
        target_bler: float,
        hysteresis_db: float = 0.5,
        hold_time_s: float = 2.0,
    ) -> None:
        # Sort by required Eb/N0 (ascending)
        self._modcods = sorted(
            modcods,
            key=lambda mc: curves[mc.name].required_ebn0_db(target_bler),
        )
        self._curves = curves
        self._target_bler = target_bler
        self._hysteresis_db = hysteresis_db
        self._hold_time_s = hold_time_s

        # Precompute thresholds
        self._thresholds = [
            curves[mc.name].required_ebn0_db(target_bler) + mc.impl_margin_db
            for mc in self._modcods
        ]

        self._current_idx = 0
        self._last_switch_t_s = -float("inf")

    def select_modcod(self, ebn0_db: float, t_s: float) -> ModCod:
        """Select ModCod based on current Eb/N0 and time.

        Parameters
        ----------
        ebn0_db : float
            Current measured Eb/N0 in dB.
        t_s : float
            Current simulation time in seconds.

        Returns
        -------
        ModCod
            The selected ModCod for the current link conditions.
        """
        # Immediate downstep if current ModCod can't be supported
        while (
            self._current_idx > 0
            and ebn0_db < self._thresholds[self._current_idx]
        ):
            self._current_idx -= 1
            self._last_switch_t_s = t_s

        # Try upstep with hysteresis + hold time
        time_since_switch = t_s - self._last_switch_t_s
        if time_since_switch >= self._hold_time_s:
            next_idx = self._current_idx + 1
            if next_idx < len(self._modcods):
                if ebn0_db >= self._thresholds[next_idx] + self._hysteresis_db:
                    self._current_idx = next_idx
                    self._last_switch_t_s = t_s

        return self._modcods[self._current_idx]

    def reset(self) -> None:
        """Reset ACM state.

        Returns
        -------
        None
        """
        self._current_idx = 0
        self._last_switch_t_s = -float("inf")
