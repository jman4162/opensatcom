"""Tests for SGP4/TLE trajectory provider."""


import numpy as np
import pytest

from opensatcom.core.models import Terminal
from opensatcom.geometry.sgp4_provider import (
    _ecef_to_enu,
    _geodetic_to_ecef,
)


class TestGeodeticToECEF:
    """Tests for geodetic to ECEF conversion."""

    def test_equator_prime_meridian(self) -> None:
        ecef = _geodetic_to_ecef(0.0, 0.0, 0.0)
        from opensatcom.core.constants import EARTH_RADIUS_M

        assert ecef[0] == pytest.approx(EARTH_RADIUS_M, rel=1e-6)
        assert ecef[1] == pytest.approx(0.0, abs=1.0)
        assert ecef[2] == pytest.approx(0.0, abs=1.0)

    def test_north_pole(self) -> None:
        ecef = _geodetic_to_ecef(90.0, 0.0, 0.0)
        from opensatcom.core.constants import EARTH_RADIUS_M

        assert ecef[0] == pytest.approx(0.0, abs=1.0)
        assert ecef[1] == pytest.approx(0.0, abs=1.0)
        assert ecef[2] == pytest.approx(EARTH_RADIUS_M, rel=1e-6)

    def test_altitude(self) -> None:
        ecef = _geodetic_to_ecef(0.0, 0.0, 1000.0)
        from opensatcom.core.constants import EARTH_RADIUS_M

        assert ecef[0] == pytest.approx(EARTH_RADIUS_M + 1000.0, rel=1e-6)


class TestECEFtoENU:
    """Tests for ECEF to ENU conversion."""

    def test_directly_above(self) -> None:
        # Satellite directly above station at equator/prime meridian

        station_ecef = _geodetic_to_ecef(0.0, 0.0, 0.0)
        sat_ecef = _geodetic_to_ecef(0.0, 0.0, 400_000.0)

        enu = _ecef_to_enu(sat_ecef, 0.0, 0.0, station_ecef)

        # Should be purely "Up"
        assert enu[0] == pytest.approx(0.0, abs=100.0)  # East
        assert enu[1] == pytest.approx(0.0, abs=100.0)  # North
        assert enu[2] == pytest.approx(400_000.0, rel=0.01)  # Up


def _sgp4_available() -> bool:
    try:
        import sgp4  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _sgp4_available(), reason="sgp4 not installed")
class TestSGP4Provider:
    """Tests for SGP4TrajectoryProvider (requires sgp4 package)."""

    # ISS TLE (example, epoch-specific)
    ISS_TLE_LINE1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9006"
    ISS_TLE_LINE2 = "2 25544  51.6400 208.9163 0006703  30.4680 329.6720 15.49560927999999"

    def test_compute_pass_returns_trajectory(self) -> None:
        from opensatcom.geometry.sgp4_provider import SGP4TrajectoryProvider

        gs = Terminal(name="Test", lat_deg=38.0, lon_deg=-77.0, alt_m=0.0)
        provider = SGP4TrajectoryProvider(
            self.ISS_TLE_LINE1, self.ISS_TLE_LINE2, gs,
        )

        traj, doppler = provider.compute_pass(0.0, 600.0, 10.0, f_hz=12e9)

        assert len(traj.pass_data.times_s) == 60
        assert len(traj.pass_data.elev_deg) == 60
        assert len(doppler) == 60

    def test_states_ecef(self) -> None:
        from opensatcom.geometry.sgp4_provider import SGP4TrajectoryProvider

        gs = Terminal(name="Test", lat_deg=0.0, lon_deg=0.0, alt_m=0.0)
        provider = SGP4TrajectoryProvider(
            self.ISS_TLE_LINE1, self.ISS_TLE_LINE2, gs,
        )

        states = provider.states_ecef(0.0, 100.0, 10.0)
        assert len(states) == 10
        # ISS orbit radius ~6778 km
        r = np.linalg.norm(states[0].r_m)
        assert 6_000_000 < r < 7_000_000

    def test_doppler_physically_plausible(self) -> None:
        from opensatcom.geometry.sgp4_provider import SGP4TrajectoryProvider

        gs = Terminal(name="Test", lat_deg=38.0, lon_deg=-77.0, alt_m=0.0)
        provider = SGP4TrajectoryProvider(
            self.ISS_TLE_LINE1, self.ISS_TLE_LINE2, gs,
        )

        _, doppler = provider.compute_pass(0.0, 600.0, 1.0, f_hz=20e9)

        # Max Doppler at Ku-band for LEO should be < 600 kHz
        assert np.max(np.abs(doppler)) < 600_000
