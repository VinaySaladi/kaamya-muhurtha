"""
Daily panchang for a place: the five limbs (tithi, vara, nakshatra, yoga, karana),
lunar month (amanta, with adhika masa), samvatsara, sunrise/sunset, lagna spans,
and the inauspicious periods every pandit checks (Rahu Kalam, Yamagandam, Gulika,
Durmuhurtham, Varjyam) plus Abhijit.

A Hindu day runs sunrise -> next sunrise; `day_panchang(date)` returns the day that
begins at sunrise on that Gregorian date.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date as Date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from . import ephemeris as E

TITHI_SPAN = 12.0
KARANA_SPAN = 6.0
NAK = E.NAK_SPAN

# ---------------------------------------------------------------- data classes


@dataclass(frozen=True)
class Place:
    lat: float
    lon: float
    tz: str = "Asia/Kolkata"
    name: str = ""

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


@dataclass
class Span:
    index: int          # element index (0-based)
    start: float        # ut
    end: float          # ut

    def overlaps(self, a: float, b: float) -> bool:
        return self.start < b and self.end > a


@dataclass
class DayPanchang:
    date: Date
    place: Place
    sunrise: float
    sunset: float
    next_sunrise: float
    vara: int                        # 0 = Sunday
    tithis: list[Span]               # index 0..29 (0-14 shukla, 15-29 krishna; 29 = amavasya)
    nakshatras: list[Span]           # 0..26
    yogas: list[Span]                # 0..26
    karanas: list[Span]              # 0..10 (named karana index)
    lagnas: list[Span]               # 0..11 sidereal sign rising
    masa: int                        # 0 = Chaitra (amanta)
    adhika: bool
    samvatsara: int                  # 0..59
    sun_rashi: int
    moon_rashis: list[Span]
    rahu: tuple[float, float]
    yamaganda: tuple[float, float]
    gulika: tuple[float, float]
    durmuhurtas: list[tuple[float, float]]
    varjyams: list[tuple[float, float]]
    amritas: list[tuple[float, float]]
    abhijit: tuple[float, float]
    guru_moudhyam: bool
    shukra_moudhyam: bool
    eclipse: str | None = None
    extras: dict = field(default_factory=dict)

    # convenience -------------------------------------------------
    def at(self, spans: list[Span], ut: float) -> int:
        for s in spans:
            if s.start <= ut < s.end:
                return s.index
        return spans[-1].index if ut >= spans[-1].start else spans[0].index


# ---------------------------------------------------------------- element angles

def _elong(ut: float) -> float:
    return E.norm(E.moon(ut) - E.sun(ut))


def _yoga_angle(ut: float) -> float:
    return E.norm(E.moon(ut) + E.sun(ut))


ELEMENTS = {
    # name: (angle function, span degrees, mean rate deg/day)
    "tithi": (_elong, TITHI_SPAN, 12.19),
    "nakshatra": (E.moon, NAK, 13.18),
    "yoga": (_yoga_angle, NAK, 14.17),
    "karana": (_elong, KARANA_SPAN, 12.19),
    "moon_rashi": (E.moon, 30.0, 13.18),
}


def _crossing(fn, ut0: float, target: float, rate: float) -> float:
    """First time >= ut0 when increasing angle fn reaches target (secant with local rate)."""
    ut = ut0
    for _ in range(40):
        diff = (target - fn(ut)) % 360.0
        if diff > 300.0:          # we are just past target (numerical overshoot)
            diff -= 360.0
        if abs(diff) < 2e-5:      # ~ 0.15 s of moon motion
            return ut
        h = 0.02
        local_rate = ((fn(ut + h) - fn(ut)) % 360.0) / h or rate
        ut += diff / local_rate
    return ut


def element_spans(kind: str, ut_a: float, ut_b: float) -> list[Span]:
    fn, size, rate = ELEMENTS[kind]
    spans: list[Span] = []
    ang = fn(ut_a)
    idx = int(ang // size)
    # start of current element
    back = (ang - idx * size) / rate
    start = _crossing(fn, ut_a - back - 0.08, (idx * size) % 360.0, rate)
    if start > ut_a:  # guess landed after; search from further back
        start = _crossing(fn, ut_a - back - 0.6, (idx * size) % 360.0, rate)
    cur_start = start
    n = int(round(360.0 / size))
    while True:
        nxt = (idx + 1) % n
        end = _crossing(fn, cur_start + 0.01, (nxt * size) % 360.0, rate)
        spans.append(Span(idx, cur_start, end))
        if end >= ut_b:
            break
        idx, cur_start = nxt, end
    return spans


def karana_name_index(half: int) -> int:
    """half-tithi number 0..59 -> karana name index (see i18n.KARANA_EN)."""
    if half == 0:
        return 0
    if 1 <= half <= 56:
        return 1 + (half - 1) % 7
    return {57: 8, 58: 9, 59: 10}[half]


# ---------------------------------------------------------------- lunar month

@lru_cache(maxsize=512)
def _masa_for_newmoon(nm0_key: float) -> tuple[int, bool, float]:
    nm0 = nm0_key
    nm1 = E.next_new_moon(nm0 + 1.0)
    s0 = int(E.sun(nm0) // 30)
    s1 = int(E.sun(nm1) // 30)
    masa = (s0 + 1) % 12
    adhika = (s0 == s1)
    return masa, adhika, nm1


def lunar_month(ut: float) -> tuple[int, bool, float, float]:
    """(masa index 0=Chaitra, adhika?, month start ut, month end ut) - amanta."""
    nm0 = E.previous_new_moon(ut)
    masa, adhika, nm1 = _masa_for_newmoon(round(nm0, 4))
    return masa, adhika, nm0, nm1


def samvatsara_index(d: Date, masa: int, adhika: bool) -> int:
    shaka = d.year - 78
    if d.month <= 4 and (masa >= 9 or (masa == 0 and adhika)):
        shaka -= 1
    return (shaka + 11) % 60


# ---------------------------------------------------------------- day periods

RAHU_PART = [8, 2, 7, 5, 6, 4, 3]       # 1-based eighth of daytime, Sun..Sat
YAMA_PART = [5, 4, 3, 2, 1, 7, 6]
GULIKA_PART = [7, 6, 5, 4, 3, 2, 1]
DURMUHURTA_DAY = [[14], [9, 12], [4], [8], [6, 12], [4, 9], [1, 2]]   # 1-based of 15
DURMUHURTA_NIGHT = [[], [], [7], [], [], [], []]

# Varjyam (tyajya) starting ghati within each nakshatra (of 60), lasting 4 ghatis.
VARJYAM_GHATI = [50, 24, 30, 40, 14, 11, 30, 20, 32, 30, 20, 18, 22, 20, 14, 14, 10, 14,
                 20, 24, 20, 10, 10, 18, 16, 24, 30]


# Amrita kalam starting ghati within each nakshatra (of 60), lasting 4 ghatis.
AMRITA_GHATI = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 42, 45, 44, 38, 38, 34, 38,
                44, 48, 44, 34, 34, 42, 40, 48, 54]


def _part(sr: float, ss: float, n: int, k: int) -> tuple[float, float]:
    step = (ss - sr) / n
    return sr + (k - 1) * step, sr + k * step


def lagna_spans(ut_a: float, ut_b: float, lat: float, lon: float) -> list[Span]:
    step = 4.0 / 1440.0
    spans: list[Span] = []
    cur = int(E.ascendant(ut_a, lat, lon) // 30)
    start = ut_a
    t = ut_a
    while t < ut_b:
        t2 = min(t + step, ut_b)
        s2 = int(E.ascendant(t2, lat, lon) // 30)
        if s2 != cur:
            lo, hi = t, t2
            for _ in range(20):
                mid = (lo + hi) / 2
                if int(E.ascendant(mid, lat, lon) // 30) == cur:
                    lo = mid
                else:
                    hi = mid
            spans.append(Span(cur, start, hi))
            cur, start = s2, hi
        t = t2
    spans.append(Span(cur, start, ut_b))
    return spans


def moudhyam(ut: float) -> tuple[bool, bool]:
    s = E.sun(ut)
    guru = E.angular_sep(E.sidereal_lon("Jupiter", ut), s) < 11.0
    v_lim = 8.0 if E.is_retrograde("Venus", ut) else 10.0
    shukra = E.angular_sep(E.sidereal_lon("Venus", ut), s) < v_lim
    return guru, shukra


# ---------------------------------------------------------------- main entry

@lru_cache(maxsize=4096)
def day_panchang(d: Date, place: Place) -> DayPanchang:
    zone = place.zone
    midnight = datetime.combine(d, time(0, 0), tzinfo=zone)
    ut0 = E.dt_to_ut(midnight)
    sr = E.next_sunrise(ut0, place.lat, place.lon)
    ss = E.next_sunset(sr, place.lat, place.lon)
    nsr = E.next_sunrise(ss, place.lat, place.lon)

    tithis = element_spans("tithi", sr, nsr)
    naks = element_spans("nakshatra", sr, nsr)
    yogas = element_spans("yoga", sr, nsr)
    halves = element_spans("karana", sr, nsr)
    karanas = [Span(karana_name_index(h.index), h.start, h.end) for h in halves]
    mrashis = element_spans("moon_rashi", sr, nsr)
    lagnas = lagna_spans(sr, nsr, place.lat, place.lon)

    masa, adhika, _, _ = lunar_month(sr)
    vara = (d.isoweekday()) % 7  # Sunday = 0

    rahu = _part(sr, ss, 8, RAHU_PART[vara])
    yama = _part(sr, ss, 8, YAMA_PART[vara])
    gul = _part(sr, ss, 8, GULIKA_PART[vara])
    durs = [_part(sr, ss, 15, k) for k in DURMUHURTA_DAY[vara]]
    durs += [_part(ss, nsr, 15, k) for k in DURMUHURTA_NIGHT[vara]]
    abhijit = _part(sr, ss, 15, 8)

    # varjyam: need full spans of the nakshatras touching the day
    varj, amr = [], []
    for sp in element_spans("nakshatra", sr - 1.1, nsr + 0.1):
        dur = sp.end - sp.start
        for table, out in ((VARJYAM_GHATI, varj), (AMRITA_GHATI, amr)):
            vs = sp.start + dur * table[sp.index] / 60.0
            ve = vs + dur * 4.0 / 60.0
            if vs < nsr and ve > sr:
                out.append((vs, ve))

    guru_m, shukra_m = moudhyam(sr)

    return DayPanchang(
        date=d, place=place, sunrise=sr, sunset=ss, next_sunrise=nsr, vara=vara,
        tithis=tithis, nakshatras=naks, yogas=yogas, karanas=karanas, lagnas=lagnas,
        masa=masa, adhika=adhika, samvatsara=samvatsara_index(d, masa, adhika),
        sun_rashi=int(E.sun(sr) // 30), moon_rashis=mrashis,
        rahu=rahu, yamaganda=yama, gulika=gul, durmuhurtas=durs, varjyams=varj, amritas=amr,
        abhijit=abhijit, guru_moudhyam=guru_m, shukra_moudhyam=shukra_m,
    )


# ---------------------------------------------------------------- janma (birth) details

@dataclass
class Janma:
    nakshatra: int
    pada: int            # 1..4
    rashi: int
    certain: bool = True
    note: str = ""


def janma_from_birth(dob: Date, tob: time | None, place: Place) -> Janma:
    zone = place.zone
    if tob is not None:
        ut = E.dt_to_ut(datetime.combine(dob, tob, tzinfo=zone))
        m = E.moon(ut)
        return Janma(int(m // NAK), int((m % NAK) // (NAK / 4)) + 1, int(m // 30))
    # no birth time: check whether the star is the same all day
    a = E.moon(E.dt_to_ut(datetime.combine(dob, time(0, 0), tzinfo=zone)))
    b = E.moon(E.dt_to_ut(datetime.combine(dob, time(23, 59), tzinfo=zone)))
    m = E.moon(E.dt_to_ut(datetime.combine(dob, time(12, 0), tzinfo=zone)))
    same_nak = int(a // NAK) == int(b // NAK)
    same_rashi = int(a // 30) == int(b // 30)
    note = ""
    if not same_nak:
        note = "Birth star changed during the day of birth; birth time or known nakshatra needed."
    return Janma(int(m // NAK), int((m % NAK) // (NAK / 4)) + 1, int(m // 30),
                 certain=same_nak and same_rashi, note=note)


# ---------------------------------------------------------------- serialisation

def fmt(ut: float, place: Place) -> str:
    return E.ut_to_dt(ut, place.zone).strftime("%Y-%m-%d %H:%M")


def hm(ut: float, place: Place) -> str:
    return E.ut_to_dt(ut, place.zone).strftime("%H:%M")


def to_dict(p: DayPanchang, lang: str = "en") -> dict:
    from .. import i18n as L
    pl = p.place

    def tithi_label(i: int) -> str:
        paksha = 0 if i < 15 else 1
        n = i if i < 15 else i - 15
        if i == 29:
            n = 15
        return f"{L.name(L.PAKSHA, paksha, lang)} {L.name(L.TITHI, n, lang)}"

    def spans(lst, labeller):
        return [{"name": labeller(s.index), "index": s.index,
                 "from": fmt(s.start, pl), "to": fmt(s.end, pl)} for s in lst]

    masa = L.name(L.MASA, p.masa, lang)
    if p.adhika:
        masa = f"{L.ADHIKA.get(lang, 'Adhika')} {masa}"
    return {
        "date": p.date.isoformat(),
        "place": {"name": pl.name, "lat": pl.lat, "lon": pl.lon, "tz": pl.tz},
        "samvatsara": L.SAMVATSARA_EN[p.samvatsara],
        "masa": masa,
        "masa_index": p.masa,
        "adhika_masa": p.adhika,
        "vara": L.name(L.VARA, p.vara, lang),
        "sunrise": hm(p.sunrise, pl),
        "sunset": hm(p.sunset, pl),
        "tithi": spans(p.tithis, tithi_label),
        "nakshatra": spans(p.nakshatras, lambda i: L.name(L.NAKSHATRA, i, lang)),
        "yoga": spans(p.yogas, lambda i: L.YOGA_EN[i]),
        "karana": spans(p.karanas, lambda i: L.KARANA_EN[i]),
        "moon_rashi": spans(p.moon_rashis, lambda i: L.name(L.RASHI, i, lang)),
        "sun_rashi": L.name(L.RASHI, p.sun_rashi, lang),
        "lagna": spans(p.lagnas, lambda i: L.name(L.RASHI, i, lang)),
        "rahu_kalam": [hm(p.rahu[0], pl), hm(p.rahu[1], pl)],
        "yamagandam": [hm(p.yamaganda[0], pl), hm(p.yamaganda[1], pl)],
        "gulika_kalam": [hm(p.gulika[0], pl), hm(p.gulika[1], pl)],
        "durmuhurtham": [[fmt(a, pl), fmt(b, pl)] for a, b in p.durmuhurtas],
        "varjyam": [[fmt(a, pl), fmt(b, pl)] for a, b in p.varjyams],
        "amrita_kalam": [[fmt(a, pl), fmt(b, pl)] for a, b in p.amritas],
        "abhijit": [hm(p.abhijit[0], pl), hm(p.abhijit[1], pl)],
        "guru_moudhyam": p.guru_moudhyam,
        "shukra_moudhyam": p.shukra_moudhyam,
    }
