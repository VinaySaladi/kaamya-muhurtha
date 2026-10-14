"""
Reference values from published panchangams (Drik-ganita, Lahiri) for Hyderabad.
Tolerance: 2 minutes (published panchangams round to the minute).
"""
from datetime import date, datetime, timezone

import pytest

from app.astro import ephemeris as E
from app.astro.panchang import Place, day_panchang, to_dict

HYD = Place(17.385, 78.4867, "Asia/Kolkata", "Hyderabad")


def _end(spans, name, tz="Asia/Kolkata"):
    for s in spans:
        if s["name"] == name:
            return s["to"]
    raise AssertionError(f"{name} not found in {spans}")


def _close(a: str, b: str, minutes=2):
    fa = datetime.strptime(a, "%Y-%m-%d %H:%M")
    fb = datetime.strptime(b, "%Y-%m-%d %H:%M")
    assert abs((fa - fb).total_seconds()) <= minutes * 60, f"{a} vs {b}"


def test_lahiri_ayanamsa_j2000():
    ut = E.dt_to_ut(datetime(2000, 1, 1, tzinfo=timezone.utc))
    assert abs(E.true_ayanamsa(ut) - (23 + 51 / 60 + 11 / 3600)) < 0.003


@pytest.mark.parametrize("d,kind,name,expected", [
    # 13 Oct 2026 (published: hindu-blog / drik values, IST)
    (date(2026, 10, 13), "nakshatra", "Vishakha", "2026-10-14 01:43"),
    (date(2026, 10, 13), "yoga", "Priti", "2026-10-13 20:23"),
    (date(2026, 10, 13), "karana", "Taitila", "2026-10-13 10:47"),
    (date(2026, 10, 13), "karana", "Gara", "2026-10-13 23:28"),
    # 20 Oct 2026
    (date(2026, 10, 20), "nakshatra", "Shravana", "2026-10-20 18:02"),
    (date(2026, 10, 20), "nakshatra", "Dhanishta", "2026-10-21 19:48"),
    (date(2026, 10, 20), "yoga", "Shoola", "2026-10-21 00:49"),
    (date(2026, 10, 20), "karana", "Kaulava", "2026-10-20 12:51"),
    # Akshaya Tritiya 2025: Tritiya ends 14:12, Rohini star
    (date(2025, 4, 30), "tithi", "Shukla Paksha Tritiya", "2025-04-30 14:12"),
    # Deepavali 2024: Amavasya ends 18:16
    (date(2024, 11, 1), "tithi", "Krishna Paksha Amavasya", "2024-11-01 18:16"),
])
def test_published_end_times(d, kind, name, expected):
    p = to_dict(day_panchang(d, HYD))
    _close(_end(p[kind], name), expected)


def test_varjyam_and_amrita_published():
    p = to_dict(day_panchang(date(2026, 10, 13), HYD))
    _close(p["varjyam"][0][0], "2026-10-13 05:54")
    _close(p["varjyam"][0][1], "2026-10-13 07:37")
    p = to_dict(day_panchang(date(2026, 10, 20), HYD))
    _close(p["varjyam"][0][0], "2026-10-20 22:19")
    _close(p["amrita_kalam"][0][0], "2026-10-20 06:36")
    _close(p["amrita_kalam"][0][1], "2026-10-20 08:21")


def test_month_and_samvatsara():
    p = to_dict(day_panchang(date(2026, 10, 13), HYD))
    assert p["masa"] == "Ashwayuja" and p["samvatsara"] == "Parabhava"
    assert to_dict(day_panchang(date(2025, 4, 30), HYD))["samvatsara"] == "Vishvavasu"
    assert to_dict(day_panchang(date(2024, 11, 1), HYD))["samvatsara"] == "Krodhi"


def test_visible_eclipses_india():
    a = E.dt_to_ut(datetime(2024, 1, 1, tzinfo=timezone.utc))
    b = E.dt_to_ut(datetime(2028, 1, 1, tzinfo=timezone.utc))
    got = [(k, E.ut_to_dt(u).date().isoformat()) for k, u in E.eclipses_between(round(a, 2), round(b, 2), 17.385, 78.4867)]
    assert got == [("lunar", "2025-09-07"), ("lunar", "2026-03-03"), ("solar", "2027-08-02")]


def test_rahu_kalam_tuesday_is_7th_part():
    p = day_panchang(date(2026, 10, 13), HYD)  # Tuesday
    part = (p.sunset - p.sunrise) / 8
    assert abs(p.rahu[0] - (p.sunrise + 6 * part)) < 1e-9
