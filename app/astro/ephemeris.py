"""
Low-level astronomy for Kaamya Muhurtha.

Built on `astronomy-engine` (MIT licence, pure Python, no data files).
All longitudes returned here are SIDEREAL (nirayana), Lahiri / Chitrapaksha
ayanamsa, geocentric, true-of-date positions - the same convention used by
Drik-ganita panchangams in Telangana, Andhra Pradesh and Maharashtra.

Time convention inside this module: `ut` = days since J2000.0 (2000-01-01 12:00 UTC),
a plain float, so values can be cached and searched cheaply.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import astronomy as A
from astronomy import astronomy as _A  # internal module (nutation helper)

J2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
NAK_SPAN = 360.0 / 27.0  # 13 deg 20 min

# ---------------------------------------------------------------- time helpers

def dt_to_ut(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return (dt.astimezone(timezone.utc) - J2000).total_seconds() / 86400.0


def ut_to_dt(ut: float, tz=timezone.utc) -> datetime:
    return (J2000 + timedelta(days=ut)).astimezone(tz)


def _t(ut: float) -> A.Time:
    return A.Time(ut)


def norm(x: float) -> float:
    return x % 360.0


# ---------------------------------------------------------------- ayanamsa

# Lahiri (Chitrapaksha) mean ayanamsa at J2000.0 = 23 deg 51' 25.53"
# (Swiss Ephemeris / Indian Astronomical Ephemeris value), advanced by the
# IAU 2006 general precession in longitude.
_LAHIRI_J2000 = 23.857092


def mean_ayanamsa(ut: float) -> float:
    T = ut / 36525.0
    p = 5028.796195 * T + 1.1054348 * T * T + 0.00007964 * T ** 3
    return _LAHIRI_J2000 + p / 3600.0


def _nutation_lon_deg(ut: float) -> float:
    return _A._e_tilt(_t(ut)).dpsi / 3600.0


def true_ayanamsa(ut: float) -> float:
    """Ayanamsa including nutation in longitude (to pair with true-of-date positions)."""
    return mean_ayanamsa(ut) + _nutation_lon_deg(ut)


def true_obliquity(ut: float) -> float:
    return _A._e_tilt(_t(ut)).tobl


# ---------------------------------------------------------------- positions

PLANETS = {
    "Sun": A.Body.Sun,
    "Moon": A.Body.Moon,
    "Mars": A.Body.Mars,
    "Mercury": A.Body.Mercury,
    "Jupiter": A.Body.Jupiter,
    "Venus": A.Body.Venus,
    "Saturn": A.Body.Saturn,
}


def _tropical(body: str, ut: float) -> float:
    t = _t(ut)
    if body == "Sun":
        return A.SunPosition(t).elon
    if body == "Moon":
        return A.EclipticGeoMoon(t).lon
    vec = A.GeoVector(PLANETS[body], t, True)
    return A.Ecliptic(vec).elon


def _mean_node_tropical(ut: float) -> float:
    T = ut / 36525.0
    return norm(125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T ** 3 / 467441.0)


@lru_cache(maxsize=200_000)
def _sid_cached(body: str, ut_key: float) -> float:
    ut = ut_key
    if body == "Rahu":
        trop = _mean_node_tropical(ut) + _nutation_lon_deg(ut)
    elif body == "Ketu":
        trop = _mean_node_tropical(ut) + _nutation_lon_deg(ut) + 180.0
    else:
        trop = _tropical(body, ut)
    return norm(trop - true_ayanamsa(ut))


def sidereal_lon(body: str, ut: float) -> float:
    # cache key rounded to ~0.86 s (1e-5 day) - far finer than any panchang need
    return _sid_cached(body, round(ut, 5))


def sun(ut: float) -> float:
    return sidereal_lon("Sun", ut)


def moon(ut: float) -> float:
    return sidereal_lon("Moon", ut)


def all_planets(ut: float) -> dict[str, float]:
    names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    return {n: sidereal_lon(n, ut) for n in names}


def is_retrograde(body: str, ut: float) -> bool:
    if body in ("Sun", "Moon", "Rahu", "Ketu"):
        return body in ("Rahu", "Ketu")
    a = sidereal_lon(body, ut - 0.5)
    b = sidereal_lon(body, ut + 0.5)
    d = (b - a + 540.0) % 360.0 - 180.0
    return d < 0


def angular_sep(a: float, b: float) -> float:
    d = abs(norm(a) - norm(b)) % 360.0
    return min(d, 360.0 - d)


# ---------------------------------------------------------------- ascendant (lagna)

def ascendant(ut: float, lat: float, lon: float) -> float:
    """Sidereal ascendant longitude for a place (lat/lon in degrees, east +)."""
    t = _t(ut)
    gast = A.SiderealTime(t)  # hours
    ramc = math.radians(norm(gast * 15.0 + lon))
    eps = math.radians(true_obliquity(ut))
    phi = math.radians(lat)
    asc = math.degrees(math.atan2(math.cos(ramc),
                                  -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps))))
    return norm(asc - true_ayanamsa(ut))


# ---------------------------------------------------------------- sunrise / sunset

@lru_cache(maxsize=20_000)
def _rise_set(kind: str, ut_start_key: float, lat: float, lon: float) -> float | None:
    obs = A.Observer(lat, lon, 0.0)
    direction = A.Direction.Rise if kind == "rise" else A.Direction.Set
    res = A.SearchRiseSet(A.Body.Sun, obs, direction, _t(ut_start_key), 2.0)
    return None if res is None else res.ut


def next_sunrise(ut: float, lat: float, lon: float) -> float | None:
    return _rise_set("rise", round(ut, 5), round(lat, 4), round(lon, 4))


def next_sunset(ut: float, lat: float, lon: float) -> float | None:
    return _rise_set("set", round(ut, 5), round(lat, 4), round(lon, 4))


# ---------------------------------------------------------------- new moons & eclipses

def previous_new_moon(ut: float) -> float:
    res = A.SearchMoonPhase(0.0, _t(ut - 31.0), 31.0)
    last = res.ut
    # walk forward to the latest new moon <= ut
    while True:
        nxt = A.SearchMoonPhase(0.0, _t(last + 1.0), 31.0)
        if nxt is None or nxt.ut > ut:
            return last
        last = nxt.ut


def next_new_moon(ut: float) -> float:
    return A.SearchMoonPhase(0.0, _t(ut), 32.0).ut


@lru_cache(maxsize=256)
def eclipses_between(ut0_key: float, ut1_key: float, lat: float = 17.385, lon: float = 78.4867) -> tuple[tuple[str, float], ...]:
    """
    Eclipses VISIBLE from the place (as Telugu / Marathi panchangams treat them):
    lunar (partial/total) with the Moon above the horizon at peak; solar seen locally.
    Returns (kind, peak_ut).
    """
    obs = A.Observer(lat, lon, 0.0)
    out: list[tuple[str, float]] = []
    e = A.SearchLunarEclipse(_t(ut0_key))
    while e.peak.ut <= ut1_key:
        if e.kind != A.EclipseKind.Penumbral:
            half = e.sd_partial / 1440.0
            for k in range(9):  # any part of the umbral phase above the horizon
                tt = e.peak.AddDays(-half + k * half / 4)
                eq = A.Equator(A.Body.Moon, tt, obs, True, True)
                if A.Horizon(tt, obs, eq.ra, eq.dec, A.Refraction.Normal).altitude > 0:
                    out.append(("lunar", e.peak.ut))
                    break
        e = A.NextLunarEclipse(e.peak)
    s = A.SearchLocalSolarEclipse(_t(ut0_key), obs)
    while s.peak.time.ut <= ut1_key:
        if max(s.partial_begin.altitude, s.peak.altitude, s.partial_end.altitude) > 0:
            out.append(("solar", s.peak.time.ut))
        s = A.NextLocalSolarEclipse(s.peak.time, obs)
    return tuple(sorted(out, key=lambda x: x[1]))


# ---------------------------------------------------------------- generic crossing search

def find_crossing(fn, ut0: float, target: float, rate_deg_per_day: float, tol_days: float = 1.0 / 86400 * 5) -> float:
    """
    Find the first time >= ut0 when angle fn(ut) (monotonically increasing, mod 360)
    reaches `target`. Uses rate-based secant steps; converges in a few iterations.
    """
    ut = ut0
    for _ in range(60):
        diff = (target - fn(ut)) % 360.0
        if diff > 359.9:  # just passed numerically
            diff -= 360.0
        if abs(diff) < 1e-7:
            return ut
        step = diff / rate_deg_per_day
        ut_new = ut + step
        if abs(ut_new - ut) < tol_days:
            return ut_new
        ut = ut_new
    return ut
