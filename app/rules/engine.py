"""
Muhurtha search engine.

Builds one continuous timeline across the requested window, splits it wherever ANY
factor changes (tithi, nakshatra, yoga, karana, lagna, Rahu Kalam, Varjyam, ...),
evaluates every slice against the event's rule book, merges passing slices into
lagna windows, scores them and returns the best 2-3 options with full reasoning.

No AI is involved here. Results are deterministic and reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as Date, datetime, time, timedelta

from ..astro import ephemeris as E
from ..astro.panchang import DayPanchang, Janma, Place, day_panchang, fmt
from .. import i18n as L
from .events import (BAD_YOGAS, EVENTS, SARVARTHA_SIDDHI, SWAYAM_SIDDHA, WORST_YOGAS, EventRule,
                     ASHADHA, SHRAVANA, BHADRAPADA, ASHWAYUJA, KARTIKA, PHALGUNA, find_event)

RULE_PROFILE = {"telugu": "telugu", "marathi": "marathi", "north": "north",
                "south_other": "telugu", "intl": "telugu"}

MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
BENEFICS = ("Jupiter", "Venus", "Mercury")
CHARA, STHIRA, DVI = 0, 1, 2
DISHA_SHOOLA = {"east": {1, 6}, "west": {0, 5}, "north": {2, 3}, "south": {4}}

ENGINE_VERSION = "1.0.0"


def lagna_type(sign: int) -> int:
    return sign % 3  # Mesha chara, Vrishabha sthira, Mithuna dvi, ...


# ------------------------------------------------------------------------- inputs

@dataclass
class Person:
    role: str
    name: str = ""
    janma: Janma | None = None
    gender: str | None = None
    dob: Date | None = None


@dataclass
class Query:
    event: str
    start: Date
    end: Date
    place: Place
    region: str = "telugu"
    persons: list[Person] = field(default_factory=list)
    time_pref: str = "any"            # any | morning | afternoon | evening | night | predawn
    weekdays: set[int] | None = None  # civil weekdays the family can do (0=Sun)
    avoid_dates: set[Date] = field(default_factory=set)
    direction: str | None = None      # for yatra
    options: int = 3
    lang: str = "en"


# ------------------------------------------------------------------------- outputs

@dataclass
class Window:
    start: float
    end: float
    score: float
    hindu_day: Date
    lagna: int
    tithi: int
    nakshatra: int
    yoga: int
    karana: int
    vara: int
    good: list[str]
    caution: list[str]


# ------------------------------------------------------------------------- helpers

def _paksha_tithi(t: int) -> tuple[int, int]:
    """tithi index 0..29 -> (paksha 0/1, tithi number 1..15)."""
    return (0, t + 1) if t < 15 else (1, t - 14)


def _tara(janma_nak: int, day_nak: int) -> int:
    return ((day_nak - janma_nak) % 27) % 9 + 1   # 1..9


def _house(from_sign: int, to_sign: int) -> int:
    return (to_sign - from_sign) % 12 + 1


def _in_any(t: float, intervals) -> bool:
    return any(a <= t < b for a, b in intervals)


def _span_at(spans, t):
    for s in spans:
        if s.start <= t < s.end:
            return s.index
    return spans[-1].index


def _period_bounds(rule: EventRule, p: DayPanchang, profile: str = "telugu") -> list[tuple[float, float]]:
    sr, ss, nsr = p.sunrise, p.sunset, p.next_sunrise
    if rule.code == "vivaha" and profile == "marathi":
        # Maharashtrian weddings: daytime and godhuli (dusk), not late night
        return [(sr, ss + 2.0 / 24)]
    if rule.period == "any":
        return [(sr, nsr)]
    if rule.period == "morning":
        noon = sr + (ss - sr) / 2
        return [(sr, noon + 1.5 / 24)]
    if rule.code == "griha_pravesh":
        # Telugu custom: early-morning (pre-dawn) gruhapravesam is very common.
        return [(sr, ss), (nsr - 2.5 / 24, nsr)]
    return [(sr, ss)]


def _pref_bounds(pref: str, p: DayPanchang) -> list[tuple[float, float]] | None:
    if not pref or pref == "any":
        return None
    zone = p.place.zone

    def at(day: Date, h: float) -> float:
        hh, mm = int(h), int(round((h - int(h)) * 60))
        return E.dt_to_ut(datetime.combine(day, time(hh, mm), tzinfo=zone))

    d, d1 = p.date, p.date + timedelta(days=1)
    return {
        "predawn": [(at(d1, 3.0), p.next_sunrise)],
        "morning": [(p.sunrise, at(d, 12.0))],
        "afternoon": [(at(d, 12.0), at(d, 16.0))],
        "evening": [(at(d, 16.0), at(d, 20.5))],
        "night": [(at(d, 19.0), at(d1, 5.0))],
        "daytime": [(p.sunrise, p.sunset)],
    }.get(pref)


def _intersect(a: list[tuple[float, float]], b: list[tuple[float, float]] | None):
    if b is None:
        return a
    out = []
    for x0, x1 in a:
        for y0, y1 in b:
            lo, hi = max(x0, y0), min(x1, y1)
            if hi > lo:
                out.append((lo, hi))
    return out


# ------------------------------------------------------------------------- day checks

def _day_checks(rule: EventRule, p: DayPanchang, profile: str, q: Query, eclipses) -> tuple[bool, list[str], list[str], float]:
    """Return (allowed, good_notes, cautions, score_delta) for the whole Hindu day."""
    good, caut, delta = [], [], 0.0
    masa = p.masa
    t_sr = p.at(p.tithis, p.sunrise)
    paksha, tnum = _paksha_tithi(t_sr)
    mname = L.MASA["en"][masa]

    if rule.no_adhika and p.adhika:
        return False, [], [f"Adhika {mname} masa - not used for this event"], 0
    if rule.months:
        allowed = rule.months.get(profile, rule.months.get("telugu"))
        if masa not in allowed:
            return False, [], [f"{mname} masa is not used for {rule.name} in this tradition"], 0
        if rule.ok_months and masa in rule.ok_months.get(profile, frozenset()):
            delta -= 5
            caut.append(f"{mname} masa is acceptable, not the best month")
        else:
            good.append(f"{mname} masa is favourable")
    if rule.avoid_dhanurmasa:
        if p.sun_rashi == 8:
            return False, [], ["Dhanurmasa (Sun in Dhanu) - auspicious ceremonies are avoided"], 0
        if profile == "north" and p.sun_rashi == 11:
            return False, [], ["Kharmas (Sun in Meena) - auspicious ceremonies are avoided"], 0
    if rule.avoid_chaturmasa and rule.avoid_chaturmasa.get(profile):
        ti = t_sr
        in_chat = ((masa == ASHADHA and ti >= 10) or masa in (SHRAVANA, BHADRAPADA, ASHWAYUJA)
                   or (masa == KARTIKA and ti < 10))
        if in_chat:
            return False, [], ["Chaturmasa - weddings and similar ceremonies are avoided"], 0
    if rule.avoid_pitru_paksha and masa == BHADRAPADA and t_sr >= 15:
        return False, [], ["Pitru Paksha (Mahalaya) - new beginnings are avoided"], 0
    if profile == "north" and rule.code in ("vivaha", "griha_pravesh", "nischitartham", "vyapara") \
            and masa == PHALGUNA and 7 <= t_sr <= 14:
        return False, [], ["Holashtak - auspicious ceremonies are avoided"], 0
    if rule.moudhyam:
        if p.guru_moudhyam:
            return False, [], ["Guru moudhyam (Jupiter combust) - this event is not performed"], 0
        if p.shukra_moudhyam:
            return False, [], ["Shukra moudhyam (Venus combust) - this event is not performed"], 0
        good.append("Guru and Shukra are both strong (no moudhyam)")
    if rule.code != "pooja":
        for kind, peak in eclipses:
            if p.sunrise - 0.5 <= peak <= p.next_sunrise:
                return False, [], [f"{kind.title()} eclipse day - avoided"], 0

    ss = SWAYAM_SIDDHA.get((masa, paksha, tnum))
    if ss:
        delta += 8
        good.append(f"{ss} - a swayam-siddha (self-auspicious) day")

    # child-age rule for annaprashana
    if rule.code == "annaprashana":
        child = next((x for x in q.persons if x.role == "child" and x.dob), None)
        if child:
            months = (p.date.year - child.dob.year) * 12 + (p.date.month - child.dob.month) \
                - (1 if p.date.day < child.dob.day else 0)
            g = (child.gender or "").lower()[:1]
            if months < 5:
                return False, [], ["Child is younger than 5 months"], 0
            if g == "m" and months % 2 == 1:
                delta -= 10
                caut.append(f"Child will be {months} months - boys usually in even months (6, 8)")
            elif g == "f" and months % 2 == 0:
                delta -= 10
                caut.append(f"Child will be {months} months - girls usually in odd months (5, 7)")
            else:
                good.append(f"Child's age ({months} months) suits annaprashana")

    # marriage: Guru bala (bride) & Surya bala (groom)
    if rule.code == "vivaha":
        jup = int(E.sidereal_lon("Jupiter", p.sunrise) // 30)
        bride = next((x for x in q.persons if x.role == "bride" and x.janma), None)
        groom = next((x for x in q.persons if x.role == "groom" and x.janma), None)
        if bride:
            h = _house(bride.janma.rashi, jup)
            if h in (2, 5, 7, 9, 11):
                delta += 4; good.append("Guru bala for the bride is strong")
            elif h in (4, 8, 12):
                delta -= 6; caut.append("Guru bala for the bride is weak - pandit may advise Guru shanti")
        if groom:
            h = _house(groom.janma.rashi, p.sun_rashi)
            if h in (3, 6, 10, 11):
                delta += 3; good.append("Surya bala for the groom is strong")
            elif h in (4, 8, 12):
                delta -= 4; caut.append("Surya bala for the groom is weak")
    return True, good, caut, delta


# ------------------------------------------------------------------------- slice evaluation

def _eval_slice(rule: EventRule, p: DayPanchang, t: float, profile: str, q: Query,
                swayam: bool, timeline) -> tuple[bool, float, list[str], list[str], dict]:
    good, caut = [], []
    score = 50.0
    tithi = _span_at(timeline["tithi"], t)
    nak = _span_at(timeline["nakshatra"], t)
    yoga = _span_at(timeline["yoga"], t)
    kar = _span_at(timeline["karana"], t)
    lag = _span_at(timeline["lagna"], t)
    vara = p.vara
    info = dict(tithi=tithi, nakshatra=nak, yoga=yoga, karana=kar, lagna=lag, vara=vara)
    paksha, tnum = _paksha_tithi(tithi)
    nak_name = L.NAKSHATRA["en"][nak]

    # inauspicious periods (hard)
    if t < p.sunset:
        if p.rahu[0] <= t < p.rahu[1]:
            return False, 0, [], ["Rahu Kalam"], info
        if p.yamaganda[0] <= t < p.yamaganda[1]:
            if profile == "telugu":
                return False, 0, [], ["Yamagandam"], info
            score -= 5
            caut.append("Overlaps Yamagandam (not strictly observed in this tradition)")
        if p.gulika[0] <= t < p.gulika[1] and rule.code != "pooja":
            score -= 4
            caut.append("Overlaps Gulika Kalam - minor")
    if _in_any(t, p.durmuhurtas):
        return False, 0, [], ["Durmuhurtham"], info
    if _in_any(t, timeline["varjyam"]):
        return False, 0, [], ["Varjyam"], info

    # vara
    if vara in rule.varas:
        score += 5
    elif vara in rule.ok_varas:
        score -= 6
        caut.append(f"{L.VARA['en'][vara]} is acceptable but not ideal")
    else:
        return False, 0, [], [f"{L.VARA['en'][vara]} not used for this event"], info

    # nakshatra
    if nak in rule.nakshatras:
        if nak in rule.best_nakshatras:
            score += 8
            good.append(f"{nak_name} nakshatra - among the best for {rule.name}")
        else:
            good.append(f"{nak_name} nakshatra is suitable")
    elif swayam and rule.swayam_siddha_override:
        caut.append(f"{nak_name} nakshatra accepted because the day itself is swayam-siddha")
    else:
        return False, 0, [], [f"{nak_name} nakshatra not suitable"], info

    # tithi
    good_set, ok_set = (rule.tithi_good_s, rule.tithi_ok_s) if paksha == 0 else (rule.tithi_good_k, rule.tithi_ok_k)
    tname = f"{L.PAKSHA['en'][paksha]} {L.TITHI['en'][tnum - 1 if tnum < 15 else (14 if paksha == 0 else 15)]}"
    if tnum in good_set:
        score += 6
        good.append(f"{tname} is a good tithi")
    elif tnum in ok_set:
        if paksha == 1 and tnum >= 7:
            score -= 3
            caut.append(f"{tname} - waning moon, acceptable")
    elif swayam and rule.swayam_siddha_override:
        pass
    else:
        return False, 0, [], [f"{tname} not suitable"], info

    # yoga & karana
    if yoga in WORST_YOGAS and rule.code != "pooja":
        return False, 0, [], [f"{L.YOGA_EN[yoga]} yoga"], info
    if yoga in BAD_YOGAS:
        if rule.avoid_bad_yoga:
            return False, 0, [], [f"{L.YOGA_EN[yoga]} yoga"], info
        score -= 4
    else:
        score += 2
    if kar == 7:  # Vishti / Bhadra
        if rule.avoid_vishti:
            return False, 0, [], ["Vishti (Bhadra) karana"], info
        score -= 5
        caut.append("Vishti karana - minor")

    # special yogas
    if nak in SARVARTHA_SIDDHI.get(vara, ()):
        score += 6
        good.append("Sarvartha Siddhi yoga (weekday + star combination)")
    if nak == 7 and vara in (0, 4) and rule.code in ("jewellery_purchase", "vehicle_purchase",
                                                     "property_purchase", "vyapara", "aksharabhyasam", "pooja"):
        score += 6
        good.append("Guru Pushya / Ravi Pushya yoga")

    # yatra: disha shoola & panchaka
    if rule.code == "yatra" and q.direction:
        dirn = q.direction.lower().strip()
        if vara in DISHA_SHOOLA.get(dirn, set()):
            return False, 0, [], [f"Disha shoola - {dirn} travel avoided on {L.VARA['en'][vara]}"], info
        if dirn == "south" and E.moon(t) >= 300.0:
            return False, 0, [], ["Panchaka - southward travel avoided"], info
    if rule.code in ("bhoomi_puja",) and E.moon(t) >= 300.0:
        score -= 6
        caut.append("Panchaka period - minor caution for construction")

    # personal: tarabalam & chandrabalam
    # Classical rule (Muhurta Chintamani): chandrabalam governs in Shukla paksha,
    # tarabalam governs in Krishna paksha; the other one is scored, not enforced.
    moon_rashi = int(E.moon(t) // 30)
    for person in q.persons:
        if person.role not in rule.personal_roles or person.janma is None:
            continue
        who = person.name or person.role
        count = (nak - person.janma.nakshatra) % 27 + 1      # 1..27
        tara = (count - 1) % 9 + 1
        if count == 1 and rule.code in ("vivaha", "upanayana", "nischitartham"):
            return False, 0, [], [f"Janma nakshatra of {who} - own birth-star day is avoided"], info
        if tara in (3, 5, 7):
            if paksha == 1:
                return False, 0, [], [f"Tarabalam unfavourable for {who} ({L.TARA_EN[tara - 1]} tara)"], info
            score -= 5
            caut.append(f"Tarabalam weak for {who} ({L.TARA_EN[tara - 1]} tara) - chandrabalam governs in Shukla paksha")
        elif tara == 1:
            score -= 4
            caut.append(f"Janma-group tara for {who}")
        else:
            score += 3
            good.append(f"Tarabalam good for {who} ({L.TARA_EN[tara - 1]} tara)")
        ch = _house(person.janma.rashi, moon_rashi)
        if ch in (4, 8, 12):
            if paksha == 0:
                return False, 0, [], [f"Chandrabalam unfavourable for {who} (Moon {ch}th from janma rashi)"], info
            score -= 5
            caut.append(f"Chandrabalam weak for {who} - tarabalam governs in Krishna paksha")
        elif ch in (1, 3, 6, 7, 10, 11):
            score += 3
            good.append(f"Chandrabalam good for {who}")
        elif paksha == 1:
            score -= 2
        # janma-ashtama lagna (8th from janma rashi) is avoided
        lh = _house(person.janma.rashi, lag)
        if lh == 8:
            return False, 0, [], [f"Lagna is 8th from {who}'s janma rashi (janma-ashtama)"], info
        if lh == 12:
            score -= 3
        if person.janma and not person.janma.certain:
            caut.append(f"{who}'s birth star is uncertain (birth time not given)")

    # lagna
    lt = lagna_type(lag)
    pref = rule.lagna_pref
    lname = L.RASHI["en"][lag]
    if pref == "sthira":
        if lt == STHIRA:
            score += 8; good.append(f"{lname} lagna - sthira (fixed), ideal for permanence")
        elif lt == DVI:
            score += 2
        else:
            score -= 12; caut.append(f"{lname} lagna is chara (movable); sthira is preferred")
    elif pref == "chara":
        if lt == CHARA:
            score += 8; good.append(f"{lname} lagna - chara (movable), ideal for vehicles and travel")
        elif lt == DVI:
            score += 3
    elif pref == "dvi":
        if lt == DVI:
            score += 6; good.append(f"{lname} lagna - dvisvabhava, ideal for learning")
    elif pref == "sthira_dvi":
        if lt in (STHIRA, DVI):
            score += 5; good.append(f"{lname} lagna is steady")

    planets = E.all_planets(t)
    houses = {pl: _house(lag, int(lon // 30)) for pl, lon in planets.items()}
    bad_8 = [pl for pl in MALEFICS if houses[pl] == 8]
    if bad_8:
        return False, 0, [], [f"Lagna shuddhi: {', '.join(bad_8)} in the 8th house"], info
    if houses["Moon"] in ((6, 8, 12) if rule.lagna_strict else (8,)):
        return False, 0, [], [f"Lagna shuddhi: Moon in the {houses['Moon']}th house"], info
    if rule.lagna_strict:
        bad_7 = [pl for pl in MALEFICS if houses[pl] == 7]
        if bad_7:
            return False, 0, [], [f"Lagna shuddhi: {', '.join(bad_7)} in the 7th house"], info
        if rule.code == "vivaha" and houses["Venus"] == 6:
            return False, 0, [], ["Lagna shuddhi: Venus in the 6th house"], info
        good.append("Lagna shuddhi is clean (7th and 8th houses free of malefics)")
    else:
        good.append("8th house from lagna is clean")
    for b in BENEFICS:
        if houses[b] in (1, 4, 7, 10):
            score += 3 if b == "Jupiter" else 2
            good.append(f"{b} in a kendra from lagna")
        elif houses[b] in (5, 9) and b == "Jupiter":
            score += 2
            good.append("Jupiter in a trikona from lagna")

    # bonuses: abhijit & amrita
    if p.abhijit[0] <= t < p.abhijit[1] and vara != 3:
        score += 4
        good.append("Abhijit muhurtham")
    if _in_any(t, timeline["amrita"]):
        score += 5
        good.append("Amrita kalam")
    return True, score, good, caut, info


# ------------------------------------------------------------------------- search

def _timeline(days: list[DayPanchang]):
    def merge(attr):
        out, seen = [], set()
        for p in days:
            for s in getattr(p, attr):
                k = (s.index, round(s.start, 4))
                if k not in seen:
                    seen.add(k)
                    out.append(s)
        return sorted(out, key=lambda s: s.start)

    def merge_iv(attr):
        out = set()
        for p in days:
            for a, b in getattr(p, attr):
                out.add((round(a, 6), round(b, 6)))
        return sorted(out)

    return {
        "tithi": merge("tithis"), "nakshatra": merge("nakshatras"), "yoga": merge("yogas"),
        "karana": merge("karanas"), "lagna": merge("lagnas"),
        "varjyam": merge_iv("varjyams"), "amrita": merge_iv("amritas"),
    }


def search(q: Query) -> dict:
    rule = find_event(q.event)
    profile = RULE_PROFILE.get(q.region, "telugu")
    if (q.end - q.start).days > 400:
        raise ValueError("Date window too long - please keep it within about a year")
    if q.end < q.start:
        raise ValueError("End date is before start date")

    dates = [q.start + timedelta(days=i) for i in range(-1, (q.end - q.start).days + 1)]
    days = [day_panchang(d, q.place) for d in dates]
    tl = _timeline(days)
    eclipses = E.eclipses_between(round(days[0].sunrise, 2), round(days[-1].next_sunrise + 1, 2),
                                  round(q.place.lat, 3), round(q.place.lon, 3))

    windows: list[Window] = []
    rejected_days: dict[str, str] = {}
    for p in days[1:]:
        if p.date in q.avoid_dates:
            rejected_days[p.date.isoformat()] = "Family not available"
            continue
        ok, dgood, dcaut, ddelta = _day_checks(rule, p, profile, q, eclipses)
        if not ok:
            rejected_days[p.date.isoformat()] = dcaut[0] if dcaut else "Not suitable"
            continue
        t_sr = p.at(p.tithis, p.sunrise)
        swayam = (p.masa, *_paksha_tithi(t_sr)) in SWAYAM_SIDDHA
        bounds = _intersect(_period_bounds(rule, p, profile), _pref_bounds(q.time_pref, p))
        for b0, b1 in bounds:
            cuts = {b0, b1}
            for key in ("tithi", "nakshatra", "yoga", "karana", "lagna"):
                for s in tl[key]:
                    for x in (s.start, s.end):
                        if b0 < x < b1:
                            cuts.add(x)
            for a, b in [p.rahu, p.yamaganda, p.gulika, p.abhijit, *p.durmuhurtas] + tl["varjyam"] + tl["amrita"]:
                for x in (a, b):
                    if b0 < x < b1:
                        cuts.add(x)
            cuts = sorted(cuts)
            cur: Window | None = None
            for a, b in zip(cuts, cuts[1:]):
                if b - a < 30 / 86400:
                    continue
                mid = (a + b) / 2
                # weekday filter is on civil date of the slice
                civil = E.ut_to_dt(mid, q.place.zone)
                if q.weekdays is not None and (civil.isoweekday() % 7) not in q.weekdays:
                    passed = False
                elif civil.date() in q.avoid_dates:
                    passed = False
                else:
                    passed, sc, g, c, info = _eval_slice(rule, p, mid, profile, q, swayam, tl)
                if passed:
                    sc += ddelta
                    if cur and abs(cur.end - a) < 60 / 86400 and cur.lagna == info["lagna"]:
                        cur.end = b
                        if sc < cur.score:
                            cur.score = sc
                        cur.good = list(dict.fromkeys(cur.good + g))
                        cur.caution = list(dict.fromkeys(cur.caution + c))
                    else:
                        if cur:
                            windows.append(cur)
                        cur = Window(a, b, sc, p.date, info["lagna"], info["tithi"], info["nakshatra"],
                                     info["yoga"], info["karana"], info["vara"],
                                     list(dict.fromkeys(dgood + g)), list(dict.fromkeys(dcaut + c)))
                else:
                    if cur:
                        windows.append(cur)
                    cur = None
            if cur:
                windows.append(cur)

    windows = [w for w in windows if (w.end - w.start) * 1440 >= rule.min_minutes]
    for w in windows:
        minutes = (w.end - w.start) * 1440
        w.score += min(4.0, max(0.0, (minutes - 30) / 15))   # comfortable window length
        w.score = max(0.0, min(100.0, w.score))

    # best window per Hindu day, then the top N days
    best_per_day: dict[Date, Window] = {}
    for w in windows:
        cur = best_per_day.get(w.hindu_day)
        if cur is None or (w.score, w.end - w.start) > (cur.score, cur.end - cur.start):
            best_per_day[w.hindu_day] = w
    ranked = sorted(best_per_day.values(), key=lambda w: (-w.score, w.start))
    chosen = ranked[: max(1, q.options)]
    chosen.sort(key=lambda w: w.start)

    return {
        "engine_version": ENGINE_VERSION,
        "event": {"code": rule.code, "name": rule.name},
        "tradition": profile,
        "place": {"name": q.place.name, "lat": q.place.lat, "lon": q.place.lon, "tz": q.place.tz},
        "window": {"from": q.start.isoformat(), "to": q.end.isoformat()},
        "personalised": any(x.janma for x in q.persons if x.role in rule.personal_roles),
        "options": [window_to_dict(w, q, i + 1, rule) for i, w in enumerate(chosen)],
        "candidate_days": len(best_per_day),
        "rejected_days_sample": dict(list(rejected_days.items())[:15]),
        "rule_notes": list(rule.notes),
    }


def quality(score: float) -> str:
    if score >= 85:
        return "uttama"     # excellent
    if score >= 72:
        return "shubha"     # good
    if score >= 60:
        return "madhyama"   # acceptable
    return "adhama"         # weak - only shown when nothing better exists


def window_to_dict(w: Window, q: Query, n: int, rule: EventRule) -> dict:
    pl, lang = q.place, q.lang
    s_dt, e_dt = E.ut_to_dt(w.start, pl.zone), E.ut_to_dt(w.end, pl.zone)
    p = day_panchang(w.hindu_day, pl)
    paksha, tnum = _paksha_tithi(w.tithi)
    tidx = tnum - 1 if tnum < 15 else (14 if paksha == 0 else 15)
    masa_idx = p.masa
    if RULE_PROFILE.get(q.region) == "north" and paksha == 1:
        masa_idx = (masa_idx + 1) % 12   # purnimanta naming
    oid = f"opt-{w.hindu_day.isoformat()}-{s_dt.strftime('%H%M')}"
    civil_vara = s_dt.isoweekday() % 7
    return {
        "option_id": oid,
        "rank_in_window": n,
        "date": s_dt.date().isoformat(),
        "weekday": L.name(L.VARA, civil_vara, lang),
        "hindu_vara": L.name(L.VARA, w.vara, lang),
        "start": s_dt.strftime("%Y-%m-%d %H:%M"),
        "end": e_dt.strftime("%Y-%m-%d %H:%M"),
        "start_time": s_dt.strftime("%I:%M %p"),
        "end_time": e_dt.strftime("%I:%M %p"),
        "duration_minutes": int(round((w.end - w.start) * 1440)),
        "score": round(w.score, 1),
        "quality": quality(w.score),
        "panchang": {
            "samvatsara": L.SAMVATSARA_EN[p.samvatsara],
            "masa": ("Adhika " if p.adhika else "") + L.name(L.MASA, masa_idx, lang),
            "paksha": L.name(L.PAKSHA, paksha, lang),
            "tithi": L.name(L.TITHI, tidx, lang),
            "nakshatra": L.name(L.NAKSHATRA, w.nakshatra, lang),
            "yoga": L.YOGA_EN[w.yoga],
            "karana": L.KARANA_EN[w.karana],
            "lagna": L.name(L.RASHI, w.lagna, lang),
            "lagna_type": L.LAGNA_TYPE_EN[lagna_type(w.lagna)],
            "sunrise": E.ut_to_dt(p.sunrise, pl.zone).strftime("%H:%M"),
            "sunset": E.ut_to_dt(p.sunset, pl.zone).strftime("%H:%M"),
            "rahu_kalam": [E.ut_to_dt(x, pl.zone).strftime("%H:%M") for x in p.rahu],
        },
        "why_good": w.good[:10],
        "cautions": w.caution[:6],
    }


# ------------------------------------------------------------------------- check a given time

def evaluate_interval(q: Query, start_ut: float, end_ut: float) -> dict:
    """
    Would the rule book accept this exact time? Used to compare with a pandit's choice
    (validation harness) and to check pandit-supplied times. Returns pass/fail with reasons.
    """
    rule = find_event(q.event)
    profile = RULE_PROFILE.get(q.region, "telugu")
    d0 = E.ut_to_dt(start_ut, q.place.zone).date()
    days = [day_panchang(d0 + timedelta(days=k), q.place) for k in (-2, -1, 0, 1)]
    p = next(x for x in days if x.sunrise <= start_ut < x.next_sunrise)
    tl = _timeline(days)
    eclipses = E.eclipses_between(round(days[0].sunrise, 2), round(days[-1].next_sunrise + 1, 2),
                                  round(q.place.lat, 3), round(q.place.lon, 3))
    ok, dgood, dcaut, ddelta = _day_checks(rule, p, profile, q, eclipses)
    if not ok:
        return {"pass": False, "level": "day", "reasons": dcaut, "hindu_day": p.date.isoformat()}
    t_sr = p.at(p.tithis, p.sunrise)
    swayam = (p.masa, *_paksha_tithi(t_sr)) in SWAYAM_SIDDHA
    # sample the interval every 2 minutes; the time passes if most of it passes
    n = max(1, int((end_ut - start_ut) * 720))
    fails, scores, reasons = 0, [], []
    for k in range(n):
        t = start_ut + (k + 0.5) * (end_ut - start_ut) / n
        passed, sc, g, c, info = _eval_slice(rule, p, t, profile, q, swayam, tl)
        if passed:
            scores.append(sc + ddelta)
        else:
            fails += 1
            reasons.extend(c)
    frac = 1 - fails / n
    return {"pass": frac >= 0.5, "fraction_ok": round(frac, 2), "level": "slice",
            "score": round(max(scores), 1) if scores else None,
            "reasons": list(dict.fromkeys(reasons))[:6], "hindu_day": p.date.isoformat()}
