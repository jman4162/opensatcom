"""Polarization mismatch loss computation."""

from __future__ import annotations

# Standard polarization types
_CIRCULAR = {"RHCP", "LHCP"}
_LINEAR = {"H", "V"}


def polarization_loss_db(
    tx_pol: str,
    rx_pol: str,
    cross_pol_db: float = 25.0,
) -> float:
    """Compute polarization mismatch loss between TX and RX polarizations.

    Parameters
    ----------
    tx_pol : str
        Transmit polarization: ``"RHCP"``, ``"LHCP"``, ``"H"``, or ``"V"``.
    rx_pol : str
        Receive polarization: ``"RHCP"``, ``"LHCP"``, ``"H"``, or ``"V"``.
    cross_pol_db : float
        Cross-polarization isolation in dB (default 25.0). Applied when
        TX and RX use opposite-sense circular polarizations.

    Returns
    -------
    float
        Polarization mismatch loss in dB (positive value, 0.0 for co-pol).
    """
    tx = tx_pol.upper().strip()
    rx = rx_pol.upper().strip()

    # Co-polarized: same polarization type
    if tx == rx:
        return 0.0

    # Circular-to-circular cross-pol (RHCP ↔ LHCP)
    if tx in _CIRCULAR and rx in _CIRCULAR:
        return cross_pol_db

    # Linear-to-linear cross-pol (H ↔ V)
    if tx in _LINEAR and rx in _LINEAR:
        return cross_pol_db

    # Circular-to-linear or linear-to-circular: 3 dB loss
    if (tx in _CIRCULAR and rx in _LINEAR) or (tx in _LINEAR and rx in _CIRCULAR):
        return 3.0

    # Unknown polarization types — assume no loss with warning
    return 0.0
