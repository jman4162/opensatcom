"""SGP4/TLE trajectory provider for real orbital mechanics."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

from opensatcom.core.constants import EARTH_RADIUS_M
from opensatcom.core.models import StateECEF, Terminal
from opensatcom.geometry.doppler import doppler_shift_hz
from opensatcom.world.providers import PrecomputedTrajectory


def _ecef_to_enu(
    sat_ecef: np.ndarray,
    station_lat_rad: float,
    station_lon_rad: float,
    station_ecef: np.ndarray,
) -> np.ndarray:
    """Convert ECEF vector to ENU relative to a ground station.

    Parameters
    ----------
    sat_ecef : numpy.ndarray
        Satellite ECEF position (3,) in metres.
    station_lat_rad : float
        Station geodetic latitude in radians.
    station_lon_rad : float
        Station geodetic longitude in radians.
    station_ecef : numpy.ndarray
        Station ECEF position (3,) in metres.

    Returns
    -------
    numpy.ndarray
        ENU vector (3,) in metres.
    """
    dx = sat_ecef - station_ecef
    sin_lat = math.sin(station_lat_rad)
    cos_lat = math.cos(station_lat_rad)
    sin_lon = math.sin(station_lon_rad)
    cos_lon = math.cos(station_lon_rad)

    e = -sin_lon * dx[0] + cos_lon * dx[1]
    n = -sin_lat * cos_lon * dx[0] - sin_lat * sin_lon * dx[1] + cos_lat * dx[2]
    u = cos_lat * cos_lon * dx[0] + cos_lat * sin_lon * dx[1] + sin_lat * dx[2]
    return np.array([e, n, u])


def _geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
    """Convert geodetic coordinates to ECEF (spherical Earth).

    Parameters
    ----------
    lat_deg : float
        Latitude in degrees.
    lon_deg : float
        Longitude in degrees.
    alt_m : float
        Altitude above sea level in metres.

    Returns
    -------
    numpy.ndarray
        ECEF position (3,) in metres.
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    r = EARTH_RADIUS_M + alt_m
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.cos(lat_rad) * math.sin(lon_rad)
    z = r * math.sin(lat_rad)
    return np.array([x, y, z])


class SGP4TrajectoryProvider:
    """Trajectory provider using SGP4/TLE orbital propagation.

    Computes satellite position and velocity from a two-line element (TLE)
    set, then converts to topocentric az/el/range relative to a ground
    station.

    Parameters
    ----------
    tle_line1 : str
        First line of the TLE.
    tle_line2 : str
        Second line of the TLE.
    ground_station : Terminal
        Ground station terminal with lat/lon/alt.
    epoch : datetime or None
        Reference epoch for t=0 in the simulation. If None, uses the
        TLE epoch.

    Raises
    ------
    ImportError
        If the ``sgp4`` package is not installed.
    """

    def __init__(
        self,
        tle_line1: str,
        tle_line2: str,
        ground_station: Terminal,
        epoch: datetime | None = None,
    ) -> None:
        try:
            from sgp4.api import WGS72, Satrec
        except ImportError:
            raise ImportError(
                "sgp4 package required for TLE trajectory provider. "
                "Install with: pip install 'opensatcom[orbit]'"
            )

        self._satellite = Satrec.twoline2rv(tle_line1, tle_line2, WGS72)
        self._gs = ground_station
        self._gs_lat_rad = math.radians(ground_station.lat_deg)
        self._gs_lon_rad = math.radians(ground_station.lon_deg)
        self._gs_ecef = _geodetic_to_ecef(
            ground_station.lat_deg, ground_station.lon_deg, ground_station.alt_m
        )

        if epoch is not None:
            self._epoch = epoch
        else:
            # Use TLE epoch

            yr = self._satellite.epochyr
            if yr < 57:
                yr += 2000
            else:
                yr += 1900
            # Convert day-of-year to datetime
            epoch_dt = datetime(yr, 1, 1, tzinfo=timezone.utc) + \
                timedelta(days=self._satellite.epochdays - 1)
            self._epoch = epoch_dt

    def compute_pass(
        self,
        t0_s: float,
        t1_s: float,
        dt_s: float,
        f_hz: float = 0.0,
    ) -> tuple[PrecomputedTrajectory, np.ndarray]:
        """Compute satellite pass geometry and Doppler shift.

        Parameters
        ----------
        t0_s : float
            Start time in seconds from epoch.
        t1_s : float
            End time in seconds from epoch.
        dt_s : float
            Time step in seconds.
        f_hz : float
            Carrier frequency for Doppler computation. Set to 0 to skip.

        Returns
        -------
        tuple of (PrecomputedTrajectory, numpy.ndarray)
            Trajectory with az/el/range and Doppler shift array in Hz.
        """
        from sgp4.api import jday

        times = np.arange(t0_s, t1_s, dt_s)
        n = len(times)

        elev_arr = np.zeros(n)
        az_arr = np.zeros(n)
        range_arr = np.zeros(n)
        doppler_arr = np.zeros(n)

        for i, t in enumerate(times):
            dt = self._epoch + timedelta(seconds=float(t))
            jd, fr = jday(
                dt.year, dt.month, dt.day,
                dt.hour, dt.minute, dt.second + dt.microsecond / 1e6,
            )

            e, r_teme, v_teme = self._satellite.sgp4(jd, fr)
            if e != 0:
                elev_arr[i] = -90.0
                continue

            # SGP4 outputs are in km and km/s — convert to m and m/s
            r_ecef = np.array(r_teme) * 1000.0
            v_ecef = np.array(v_teme) * 1000.0

            # Convert to ENU
            enu = _ecef_to_enu(r_ecef, self._gs_lat_rad, self._gs_lon_rad, self._gs_ecef)

            # Az/El/Range
            horiz_range = math.sqrt(enu[0] ** 2 + enu[1] ** 2)
            slant_range = math.sqrt(enu[0] ** 2 + enu[1] ** 2 + enu[2] ** 2)
            elev = math.degrees(math.atan2(enu[2], horiz_range))
            az = math.degrees(math.atan2(enu[0], enu[1])) % 360.0

            elev_arr[i] = elev
            az_arr[i] = az
            range_arr[i] = slant_range

            # Doppler: radial velocity = (range_unit_vec · velocity)
            if f_hz > 0 and slant_range > 0:
                range_unit = enu / slant_range
                v_enu = _ecef_to_enu(
                    self._gs_ecef + v_ecef,
                    self._gs_lat_rad, self._gs_lon_rad, self._gs_ecef,
                )
                v_radial = float(np.dot(range_unit, v_enu))
                doppler_arr[i] = doppler_shift_hz(f_hz, v_radial)

        traj = PrecomputedTrajectory.from_arrays(times, elev_arr, az_arr, range_arr)
        return traj, doppler_arr

    def states_ecef(
        self, t0_s: float, t1_s: float, dt_s: float
    ) -> list[StateECEF]:
        """Generate satellite ECEF states over a time window.

        Parameters
        ----------
        t0_s : float
            Start time in seconds from epoch.
        t1_s : float
            End time in seconds from epoch.
        dt_s : float
            Time step in seconds.

        Returns
        -------
        list of StateECEF
            Satellite states at each time step.
        """
        from sgp4.api import jday

        times = np.arange(t0_s, t1_s, dt_s)
        states: list[StateECEF] = []

        for t in times:
            dt = self._epoch + timedelta(seconds=float(t))
            jd, fr = jday(
                dt.year, dt.month, dt.day,
                dt.hour, dt.minute, dt.second + dt.microsecond / 1e6,
            )
            e, r, v = self._satellite.sgp4(jd, fr)
            if e != 0:
                states.append(StateECEF(t_s=float(t), r_m=np.zeros(3)))
                continue

            states.append(StateECEF(
                t_s=float(t),
                r_m=np.array(r) * 1000.0,
                v_mps=np.array(v) * 1000.0,
            ))

        return states
