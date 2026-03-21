"""Unit tests for geometry/slant.py — slant range and elevation calculations."""

from __future__ import annotations

import pytest

from opensatcom.geometry.slant import elevation_deg, slant_range_m


class TestSlantRange:
    def test_geo_nadir(self) -> None:
        """GEO satellite at 90° elevation (nadir) — slant range equals altitude."""
        geo_alt_m = 35_786_000.0
        d = slant_range_m(terminal_alt_m=0.0, sat_alt_m=geo_alt_m, elev_deg=90.0)
        assert d == pytest.approx(geo_alt_m, rel=1e-6)

    def test_geo_low_elevation(self) -> None:
        """GEO at 10° elevation — range should be larger than altitude."""
        geo_alt_m = 35_786_000.0
        d = slant_range_m(terminal_alt_m=0.0, sat_alt_m=geo_alt_m, elev_deg=10.0)
        assert d > geo_alt_m
        # Known approximate value: ~40,586 km at 10° for GEO
        assert d == pytest.approx(40_586_000, rel=0.02)

    def test_leo_moderate_elevation(self) -> None:
        """LEO at 550 km, 45° elevation — sanity check."""
        leo_alt_m = 550_000.0
        d = slant_range_m(terminal_alt_m=0.0, sat_alt_m=leo_alt_m, elev_deg=45.0)
        # Must be between altitude and Earth's limb distance
        assert leo_alt_m < d < 2 * leo_alt_m

    def test_terminal_with_altitude(self) -> None:
        """Terminal at altitude should reduce slant range slightly vs sea level."""
        sat_alt_m = 550_000.0
        d_sea = slant_range_m(terminal_alt_m=0.0, sat_alt_m=sat_alt_m, elev_deg=30.0)
        d_alt = slant_range_m(terminal_alt_m=2000.0, sat_alt_m=sat_alt_m, elev_deg=30.0)
        assert d_alt < d_sea


class TestElevation:
    def test_round_trip(self) -> None:
        """slant_range_m -> elevation_deg should recover the original elevation."""
        for elev in [5.0, 15.0, 30.0, 60.0, 90.0]:
            d = slant_range_m(terminal_alt_m=0.0, sat_alt_m=550_000.0, elev_deg=elev)
            recovered = elevation_deg(terminal_alt_m=0.0, sat_alt_m=550_000.0, range_m=d)
            assert recovered == pytest.approx(elev, abs=1e-9)

    def test_geo_nadir_elevation(self) -> None:
        """At nadir (range == altitude), elevation should be 90°."""
        geo_alt_m = 35_786_000.0
        elev = elevation_deg(terminal_alt_m=0.0, sat_alt_m=geo_alt_m, range_m=geo_alt_m)
        assert elev == pytest.approx(90.0, abs=1e-6)
