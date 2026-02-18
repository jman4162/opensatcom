"""Cascaded RF chain model with Friis noise figure and IIP3 cascade."""

from __future__ import annotations

from dataclasses import dataclass

from opensatcom.core.models import RFChainModel
from opensatcom.core.units import db10_to_lin, lin_to_db10

# IEEE standard reference temperature
T_REF_K = 290.0


@dataclass(frozen=True)
class RFStage:
    """A single RF stage (LNA, filter, mixer, PA, etc.).

    Parameters
    ----------
    name : str
        Human-readable stage identifier (e.g., "LNA", "BPF", "PA").
    gain_db : float
        Stage gain in dB.  Use negative values for lossy elements (filters, cables).
    nf_db : float
        Noise figure in dB.  For a passive loss of L dB, NF = L dB.
    iip3_dbm : float | None
        Input-referred third-order intercept point in dBm.
        None means the stage is assumed linear (e.g., passive filter).
    """

    name: str
    gain_db: float
    nf_db: float
    iip3_dbm: float | None = None


class CascadedRFChain:
    """Multi-stage RF chain with Friis noise cascade and IIP3 cascade.

    Supports both TX and RX chain analysis.  For a receive chain the key
    output is cascaded noise temperature; for a transmit chain the key
    output is total gain/loss from PA to antenna feed.

    Parameters
    ----------
    stages : list[RFStage]
        Ordered list of stages from input to output.
    tx_power_w : float
        Transmit power at PA output in watts (for TX chain context).
    """

    def __init__(self, stages: list[RFStage], tx_power_w: float = 1.0) -> None:
        if not stages:
            raise ValueError("CascadedRFChain requires at least one stage")
        self._stages = list(stages)
        self._tx_power_w = tx_power_w

    @property
    def stages(self) -> list[RFStage]:
        return list(self._stages)

    @property
    def n_stages(self) -> int:
        return len(self._stages)

    @property
    def tx_power_w(self) -> float:
        return self._tx_power_w

    # ---- Gain ----

    def total_gain_db(self) -> float:
        """Total cascaded gain in dB (sum of all stage gains)."""
        return sum(s.gain_db for s in self._stages)

    def total_gain_lin(self) -> float:
        """Total cascaded gain as a linear ratio."""
        return db10_to_lin(self.total_gain_db())

    # ---- Noise figure (Friis cascade) ----

    def cascaded_nf_db(self) -> float:
        """Cascaded noise figure in dB using Friis formula.

        F_total = F_1 + (F_2 - 1)/G_1 + (F_3 - 1)/(G_1 * G_2) + ...
        """
        return lin_to_db10(self._cascaded_nf_lin())

    def _cascaded_nf_lin(self) -> float:
        """Cascaded noise factor (linear)."""
        f_total = db10_to_lin(self._stages[0].nf_db)
        cumulative_gain = db10_to_lin(self._stages[0].gain_db)
        for stage in self._stages[1:]:
            f_stage = db10_to_lin(stage.nf_db)
            f_total += (f_stage - 1.0) / cumulative_gain
            cumulative_gain *= db10_to_lin(stage.gain_db)
        return f_total

    def cascaded_noise_temp_k(self) -> float:
        """Equivalent input noise temperature from cascaded NF.

        T_e = T_ref * (F - 1)  where T_ref = 290 K.
        """
        return T_REF_K * (self._cascaded_nf_lin() - 1.0)

    # ---- IIP3 cascade ----

    def cascaded_iip3_dbm(self) -> float | None:
        """Cascaded input-referred IIP3 in dBm.

        1/IIP3_total = 1/IIP3_1 + G_1/IIP3_2 + G_1*G_2/IIP3_3 + ...

        Returns None if no stage has an IIP3 spec.
        """
        # Collect stages with IIP3
        has_iip3 = any(s.iip3_dbm is not None for s in self._stages)
        if not has_iip3:
            return None

        inv_iip3_total = 0.0
        cumulative_gain = 1.0
        for i, stage in enumerate(self._stages):
            if stage.iip3_dbm is not None:
                iip3_lin = db10_to_lin(stage.iip3_dbm / 10.0 * 10.0)  # dBm to mW
                inv_iip3_total += cumulative_gain / iip3_lin
            cumulative_gain *= db10_to_lin(stage.gain_db)

        if inv_iip3_total == 0.0:
            return None
        return lin_to_db10(1.0 / inv_iip3_total)

    # ---- TX chain helpers ----

    def tx_losses_db(self) -> float:
        """Total TX loss (negative of total gain when gain < 0).

        For a TX chain where stages represent post-PA losses (feed, cable,
        filter), this returns the magnitude of loss in dB (positive number).
        """
        total = self.total_gain_db()
        return -total if total < 0 else 0.0

    # ---- Backward compatibility ----

    def to_simple_rf_chain(self) -> RFChainModel:
        """Convert to the simple RFChainModel for backward compatibility.

        Maps cascaded noise temp → rx_noise_temp_k, cascaded losses → tx_losses_db.
        """
        return RFChainModel(
            tx_power_w=self._tx_power_w,
            tx_losses_db=self.tx_losses_db(),
            rx_noise_temp_k=self.cascaded_noise_temp_k(),
        )

    def __repr__(self) -> str:
        stages_str = ", ".join(s.name for s in self._stages)
        return (
            f"CascadedRFChain(stages=[{stages_str}], "
            f"NF={self.cascaded_nf_db():.2f} dB, "
            f"T_e={self.cascaded_noise_temp_k():.1f} K)"
        )
