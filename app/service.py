"""
Service layer shared by the REST API and the Acharya's tools.
Turns loose input (strings, dicts) into engine objects and back.
"""
from __future__ import annotations

from datetime import date as Date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import i18n as L
from .astro.panchang import Janma, Place, day_panchang, janma_from_birth, to_dict
from .places import resolve
from .rules.engine import Person, Query, search
from .rules.events import EVENTS, find_event


class InputError(ValueError):
    pass


# ---------------------------------------------------------------- parsing

def parse_date(s: str) -> Date:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise InputError(f"Could not read the date '{s}'. Use YYYY-MM-DD.")


def parse_time(s: str | None) -> time | None:
    if not s:
        return None
    s = s.strip().upper().replace(".", ":")
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I %p"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            pass
    raise InputError(f"Could not read the time '{s}'. Use HH:MM (24h) or 10:30 AM.")


def place_from(spec) -> tuple[Place, str]:
    """spec: 'Hyderabad' | {'name':..} | {'lat':..,'lon':..,'tz':..}. Returns (Place, region)."""
    if isinstance(spec, dict):
        if spec.get("lat") is not None and spec.get("lon") is not None:
            r = resolve(spec.get("name"), float(spec["lat"]), float(spec["lon"]), spec.get("tz"))
        else:
            r = resolve(spec.get("name") or spec.get("city") or "")
    else:
        r = resolve(str(spec or ""))
    if not r:
        raise InputError(f"Place '{spec}' not found. Give the nearest big city or coordinates.")
    return r[0].place, r[0].region


def place_candidates(query: str) -> list[dict]:
    return [{"name": c.display, "lat": c.place.lat, "lon": c.place.lon, "tz": c.place.tz,
             "region": c.region, "source": c.source} for c in resolve(query)]


def person_from(d: dict) -> Person:
    role = (d.get("role") or "kartha").lower()
    name = d.get("name") or ""
    gender = d.get("gender")
    dob = parse_date(d["dob"]) if d.get("dob") else None
    janma: Janma | None = None
    if d.get("nakshatra") or d.get("rashi"):
        ni = L.nak_index_from_name(d.get("nakshatra")) if d.get("nakshatra") else None
        ri = L.rashi_index_from_name(d.get("rashi")) if d.get("rashi") else None
        if ni is None:
            raise InputError(f"Janma nakshatra needed (could not read '{d.get('nakshatra')}')")
        if d.get("rashi") and ri is None:
            raise InputError(f"Unknown rashi '{d.get('rashi')}'")
        pada = int(d.get("pada") or 0)
        if ri is None:
            if pada:
                ri = int(((ni * 4 + pada - 1) * (40.0 / 12.0)) // 30)
            else:
                # without pada a star may span two rashis; take the rashi where it starts
                ri = int((ni * (40.0 / 3.0) + 0.01) // 30)
        janma = Janma(ni, pada or 1, ri, certain=bool(d.get("rashi") or pada),
                      note="" if (d.get("rashi") or pada) else "Rashi inferred from nakshatra; confirm with family")
    elif dob:
        bp = d.get("birthplace") or d.get("birth_place")
        if not bp:
            raise InputError(f"Birth place needed for {name or role}")
        place, _ = place_from(bp)
        janma = janma_from_birth(dob, parse_time(d.get("tob") or d.get("birth_time")), place)
    return Person(role=role, name=name, janma=janma, gender=gender, dob=dob)


def janma_summary(p: Person, lang: str = "en") -> dict:
    if not p.janma:
        return {"role": p.role, "name": p.name, "available": False}
    j = p.janma
    return {
        "role": p.role, "name": p.name, "available": True,
        "nakshatra": L.name(L.NAKSHATRA, j.nakshatra, lang), "pada": j.pada,
        "rashi": L.name(L.RASHI, j.rashi, lang),
        "nakshatra_en": L.NAKSHATRA["en"][j.nakshatra], "rashi_en": L.RASHI["en"][j.rashi],
        "certain": j.certain, "note": j.note,
    }


# ---------------------------------------------------------------- operations

def event_catalogue(lang: str = "en") -> list[dict]:
    return [{
        "code": e.code, "name": e.name, "aliases": list(e.aliases[:6]),
        "requirements": [{"key": r.key, "label": r.label, "required": r.required, "hint": r.hint}
                         for r in e.requirements],
        "notes": list(e.notes),
    } for e in EVENTS.values()]


def event_requirements(event: str) -> dict:
    e = find_event(event)
    return {
        "code": e.code, "name": e.name,
        "whose_stars_are_checked": list(e.personal_roles),
        "requirements": [{"key": r.key, "label": r.label, "required": r.required, "hint": r.hint}
                         for r in e.requirements],
        "notes": list(e.notes),
        "matched": e.code != "general" or event.lower().strip() in ("general", "auspicious"),
    }


def find_muhurtham(*, event: str, from_date: str, to_date: str, venue, persons: list[Person] | list[dict],
                   time_pref: str = "any", weekdays: list[str] | None = None, avoid_dates: list[str] | None = None,
                   direction: str | None = None, tradition: str | None = None, options: int = 3,
                   lang: str = "en", max_window_days: int = 366) -> dict:
    start, end = parse_date(from_date), parse_date(to_date)
    if start < Date.today() - timedelta(days=1):
        raise InputError("The start date is in the past")
    if (end - start).days > max_window_days:
        raise InputError(f"Please keep the date range within {max_window_days} days")
    place, region = place_from(venue)
    if tradition:
        region = {"telugu": "telugu", "marathi": "marathi", "north": "north", "hindi": "north",
                  "south": "telugu"}.get(tradition.lower(), region)
    ppl = [p if isinstance(p, Person) else person_from(p) for p in persons]
    wd = None
    if weekdays:
        names = [v.lower() for v in L.VARA["en"]]
        wd = {names.index(w.lower()) for w in weekdays if w.lower() in names} or None
    q = Query(event=event, start=start, end=end, place=place, region=region, persons=ppl,
              time_pref=(time_pref or "any").lower(), weekdays=wd,
              avoid_dates={parse_date(x) for x in (avoid_dates or [])},
              direction=direction, options=max(1, min(int(options or 3), 5)), lang=lang)
    res = search(q)
    res["people"] = [janma_summary(p, lang) for p in ppl]
    return res


def panchang(date_str: str, venue, lang: str = "en") -> dict:
    place, _ = place_from(venue)
    return to_dict(day_panchang(parse_date(date_str), place), lang)


def today_in(tz: str = "Asia/Kolkata") -> Date:
    return datetime.now(ZoneInfo(tz)).date()
