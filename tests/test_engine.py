"""Rule invariants: whatever the engine returns must satisfy the hard rules."""
from datetime import date, time, timedelta

import pytest

from app.astro import ephemeris as E
from app.astro.panchang import Place, day_panchang, janma_from_birth
from app.rules.engine import Person, Query, search, _tara, _house
from app.rules.events import EVENTS

HYD = Place(17.385, 78.4867, "Asia/Kolkata", "Hyderabad")
MUM = Place(19.0760, 72.8777, "Asia/Kolkata", "Mumbai")
START = date.today() + timedelta(days=7)

KARTHA = Person("kartha", "Ravi", janma_from_birth(date(1990, 6, 15), time(7, 30), HYD))
BRIDE = Person("bride", "Lakshmi", janma_from_birth(date(1998, 3, 14), time(9, 20), HYD))
GROOM = Person("groom", "Arjun", janma_from_birth(date(1994, 1, 5), time(22, 10), HYD))
CHILD = Person("child", "Baby", janma_from_birth(START - timedelta(days=170), time(4, 0), HYD), gender="male",
               dob=START - timedelta(days=170))


def persons_for(code):
    roles = EVENTS[code].personal_roles
    return [p for p in (KARTHA, BRIDE, GROOM, CHILD) if p.role in roles]


def _inside(a, b, iv):
    return a < iv[1] and b > iv[0]


@pytest.mark.parametrize("code", sorted(EVENTS))
@pytest.mark.parametrize("place,region", [(HYD, "telugu"), (MUM, "marathi")])
def test_hard_rules_hold(code, place, region):
    rule = EVENTS[code]
    q = Query(code, START, START + timedelta(days=150), place, region, persons_for(code))
    res = search(q)
    for o in res["options"]:
        hd = date.fromisoformat(o["option_id"].split("-", 1)[1][:10])
        p = day_panchang(hd, place)
        s = E.dt_to_ut(__import__("datetime").datetime.strptime(o["start"], "%Y-%m-%d %H:%M").replace(tzinfo=place.zone))
        e = E.dt_to_ut(__import__("datetime").datetime.strptime(o["end"], "%Y-%m-%d %H:%M").replace(tzinfo=place.zone))
        s += 61 / 86400; e -= 61 / 86400  # minute rounding of displayed times
        for iv in [p.rahu, *([p.yamaganda] if region == "telugu" else []), *p.durmuhurtas, *p.varjyams]:
            assert not _inside(s, e, iv), f"{code} {o['start']} overlaps a forbidden period"
        mid = (s + e) / 2
        nak = int(E.moon(mid) // E.NAK_SPAN)
        assert nak in rule.nakshatras or rule.swayam_siddha_override
        if rule.months:
            assert p.masa in rule.months[region if region in rule.months else "telugu"]
        if rule.moudhyam:
            assert not p.guru_moudhyam and not p.shukra_moudhyam
        for person in q.persons:
            if person.role in rule.personal_roles and person.janma:
                shukla = o["panchang"]["paksha"] == "Shukla Paksha"
                if shukla:
                    assert _house(person.janma.rashi, int(E.moon(mid) // 30)) not in (4, 8, 12)
                else:
                    assert _tara(person.janma.nakshatra, nak) not in (3, 5, 7)
        assert o["duration_minutes"] >= rule.min_minutes - 1
        assert 0 <= o["score"] <= 100


def test_marriage_never_in_dhanurmasa_or_ashadha():
    res = search(Query("vivaha", START, START + timedelta(days=360), HYD, "telugu", [BRIDE, GROOM], options=5))
    for o in res["options"]:
        assert o["panchang"]["masa"] not in ("Ashadha", "Bhadrapada", "Ashwayuja", "Pushya")


def test_deterministic():
    q = Query("griha_pravesh", START, START + timedelta(days=90), HYD, "telugu", [KARTHA])
    assert search(q)["options"] == search(q)["options"]


def test_yatra_disha_shoola():
    res = search(Query("yatra", START, START + timedelta(days=60), HYD, "telugu", [KARTHA], direction="east"))
    for o in res["options"]:
        assert o["hindu_vara"] not in ("Monday", "Saturday")
