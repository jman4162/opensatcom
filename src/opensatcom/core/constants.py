"""Physical constants used throughout OpenSatCom.

All constants are in SI units.

.. list-table:: Constants
   :header-rows: 1

   * - Name
     - Value
     - Unit
   * - ``SPEED_OF_LIGHT_MPS``
     - 299 792 458
     - m/s
   * - ``BOLTZMANN_DBW_PER_K_HZ``
     - -228.6
     - dBW/(K Hz)
   * - ``EARTH_RADIUS_M``
     - 6 371 000
     - m
"""

from __future__ import annotations

SPEED_OF_LIGHT_MPS: float = 299_792_458.0
"""Speed of light in vacuum (m/s)."""

BOLTZMANN_DBW_PER_K_HZ: float = -228.6
"""Boltzmann constant in dBW/(K*Hz)."""

EARTH_RADIUS_M: float = 6_371_000.0
"""Mean Earth radius (m)."""
