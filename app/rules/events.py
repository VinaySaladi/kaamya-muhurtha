"""
Muhurtha rule book - one entry per event.

Sources: Muhurta Chintamani, Kalaprakashika and common Telugu / Marathi
panchangam practice. Every rule here is DATA so that a senior pandit can
review and adjust it without touching the engine (see docs/RULEBOOK.md).

Indices
  nakshatra 0..26 (0 Ashwini ... 26 Revati) - use names via N[...]
  tithi     paksha-tithi 1..15 (15 = Purnima in shukla, Amavasya in krishna)
  vara      0 Sunday ... 6 Saturday
  masa      0 Chaitra ... 11 Phalguna (amanta)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..i18n import NAKSHATRA

_N = {n.lower(): i for i, n in enumerate(NAKSHATRA["en"])}


def N(*names: str) -> frozenset[int]:
    return frozenset(_N[n.lower()] for n in names)


SUN, MON, TUE, WED, THU, FRI, SAT = range(7)
CHAITRA, VAISHAKHA, JYESHTHA, ASHADHA, SHRAVANA, BHADRAPADA, ASHWAYUJA, KARTIKA, \
    MARGASHIRA, PUSHYA, MAGHA, PHALGUNA = range(12)

# Common sets ---------------------------------------------------------------

DHRUVA = N("Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada")           # fixed
MRIDU = N("Mrigashira", "Chitra", "Anuradha", "Revati")                                    # soft
KSHIPRA = N("Ashwini", "Pushya", "Hasta")                                                  # swift
CHARA_NAK = N("Punarvasu", "Swati", "Shravana", "Dhanishta", "Shatabhisha")               # movable

GOOD_TITHI_SHUKLA = frozenset({2, 3, 5, 7, 10, 11, 13})
OK_TITHI_SHUKLA = frozenset({1, 6, 12, 15})
GOOD_TITHI_KRISHNA = frozenset({1, 2, 3, 5})
OK_TITHI_KRISHNA = frozenset({6, 7, 10, 11, 12, 13})
# never for auspicious beginnings: Rikta (4, 9, 14), Ashtami (8), Amavasya (krishna 15)

BAD_YOGAS = frozenset({0, 5, 8, 9, 12, 14, 16, 18, 26})   # Vishkambha, Atiganda, Shoola, Ganda,
#                                                           Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti
WORST_YOGAS = frozenset({16, 26})                         # Vyatipata, Vaidhriti - never

# Sarvartha Siddhi yoga (weekday + nakshatra) - a strong bonus
SARVARTHA_SIDDHI = {
    SUN: N("Ashwini", "Pushya", "Hasta", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Moola"),
    MON: N("Rohini", "Mrigashira", "Pushya", "Anuradha", "Shravana"),
    TUE: N("Ashwini", "Krittika", "Ashlesha", "Uttara Bhadrapada"),
    WED: N("Rohini", "Anuradha", "Hasta", "Krittika", "Mrigashira"),
    THU: N("Ashwini", "Punarvasu", "Pushya", "Anuradha", "Revati"),
    FRI: N("Ashwini", "Punarvasu", "Anuradha", "Shravana", "Revati"),
    SAT: N("Rohini", "Swati", "Shravana"),
}

# Swayam-siddha days (Sade-teen muhurta): (masa, paksha 0/1, tithi)
SWAYAM_SIDDHA = {
    (CHAITRA, 0, 1): "Ugadi / Gudi Padwa",
    (VAISHAKHA, 0, 3): "Akshaya Tritiya",
    (ASHWAYUJA, 0, 10): "Vijayadashami",
    (KARTIKA, 0, 1): "Bali Pratipada",
    (MAGHA, 0, 5): "Vasant Panchami",
}


@dataclass(frozen=True)
class Requirement:
    key: str
    label: str
    required: bool = True
    hint: str = ""


@dataclass(frozen=True)
class EventRule:
    code: str
    name: str
    aliases: tuple[str, ...]
    nakshatras: frozenset[int]                        # allowed
    best_nakshatras: frozenset[int] = frozenset()
    varas: frozenset[int] = frozenset({MON, WED, THU, FRI})
    ok_varas: frozenset[int] = frozenset()           # allowed with a small penalty
    tithi_good_s: frozenset[int] = GOOD_TITHI_SHUKLA
    tithi_ok_s: frozenset[int] = OK_TITHI_SHUKLA
    tithi_good_k: frozenset[int] = GOOD_TITHI_KRISHNA
    tithi_ok_k: frozenset[int] = OK_TITHI_KRISHNA
    period: str = "day"                               # day | any | morning
    lagna_pref: str = "any"                           # sthira | chara | dvi | sthira_dvi | any
    lagna_strict: bool = False                        # full lagna-shuddhi (7th & 8th clean)
    moudhyam: bool = False                            # Guru / Shukra combustion forbids
    no_adhika: bool = True
    months: dict[str, frozenset[int]] | None = None  # region -> allowed months (None = all)
    ok_months: dict[str, frozenset[int]] | None = None
    avoid_dhanurmasa: bool = False                   # Sun in Dhanu (and Meena in north)
    avoid_chaturmasa: dict[str, bool] | None = None
    avoid_pitru_paksha: bool = True
    avoid_bad_yoga: bool = True
    avoid_vishti: bool = True
    personal_roles: tuple[str, ...] = ("kartha",)    # whose stars to check
    swayam_siddha_override: bool = False             # allow on Ugadi/Akshaya Tritiya even if star not listed
    min_minutes: int = 24
    requirements: tuple[Requirement, ...] = ()
    notes: tuple[str, ...] = ()


def _person(role: str, label: str, required: bool = True) -> tuple[Requirement, ...]:
    return (
        Requirement(f"{role}.name", f"{label} - full name", required),
        Requirement(f"{role}.dob", f"{label} - date of birth", required),
        Requirement(f"{role}.tob", f"{label} - time of birth", False,
                    "If not known, ask for janma nakshatra / rashi instead"),
        Requirement(f"{role}.birthplace", f"{label} - place of birth", required),
    )


COMMON = (
    Requirement("window", "Preferred date range (from - to)", True, "Ideally 1-6 months"),
    Requirement("venue_city", "City / place where the event will happen", True),
    Requirement("time_pref", "Preferred time of day (morning / afternoon / evening / night / any)", False),
    Requirement("avoid_dates", "Dates that are NOT possible for the family", False),
)

ALL_REGIONS = ("telugu", "marathi", "north")


def _all(months: set[int]) -> dict[str, frozenset[int]]:
    return {r: frozenset(months) for r in ALL_REGIONS}


EVENTS: dict[str, EventRule] = {}


def _add(e: EventRule) -> None:
    EVENTS[e.code] = e


# ---------------------------------------------------------------- marriage & engagement

_VIVAHA_NAK = N("Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha",
                "Moola", "Uttara Ashadha", "Uttara Bhadrapada", "Revati")
_add(EventRule(
    code="vivaha", name="Vivaha (Marriage)",
    aliases=("marriage", "wedding", "pelli", "shaadi", "lagna", "vivah", "kalyanam", "lagnam"),
    nakshatras=_VIVAHA_NAK, best_nakshatras=N("Rohini", "Uttara Phalguni", "Uttara Ashadha",
                                               "Uttara Bhadrapada", "Revati", "Mrigashira", "Hasta"),
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN}),
    tithi_good_s=frozenset({2, 3, 5, 7, 10, 11, 13}), tithi_ok_s=frozenset({1, 12, 15}),
    tithi_good_k=frozenset({1, 2, 3, 5}), tithi_ok_k=frozenset({7, 10}),
    period="any", lagna_pref="any", lagna_strict=True, moudhyam=True,
    months={
        "telugu": frozenset({CHAITRA, VAISHAKHA, JYESHTHA, SHRAVANA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA}),
        "marathi": frozenset({KARTIKA, MARGASHIRA, PUSHYA, MAGHA, PHALGUNA, CHAITRA, VAISHAKHA, JYESHTHA}),
        "north": frozenset({KARTIKA, MARGASHIRA, MAGHA, PHALGUNA, VAISHAKHA, JYESHTHA, ASHADHA}),
    },
    avoid_dhanurmasa=True, avoid_chaturmasa={"marathi": True, "north": True, "telugu": False},
    personal_roles=("bride", "groom"), min_minutes=30,
    requirements=_person("bride", "Bride") + _person("groom", "Groom") + COMMON + (
        Requirement("first_child", "Is either of them the eldest child? (Jyeshtha masa check)", False),
    ),
    notes=("Guru bala for the bride and Surya bala for the groom are scored, not enforced; "
           "pandit may prescribe shanti where weak.",
           "Telugu custom avoids Jyeshtha masa when the bride or groom is the eldest child."),
))

_add(EventRule(
    code="nischitartham", name="Nischitartham / Sagai (Engagement)",
    aliases=("engagement", "sagai", "nischitartham", "roka", "ring ceremony", "sakharpuda", "tilak"),
    nakshatras=_VIVAHA_NAK | N("Pushya", "Shravana", "Dhanishta", "Chitra", "Punarvasu"),
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN}),
    period="day", lagna_pref="sthira_dvi", moudhyam=True, avoid_chaturmasa={"north": True},
    personal_roles=("bride", "groom"),
    requirements=_person("bride", "Bride") + _person("groom", "Groom") + COMMON,
))

# ---------------------------------------------------------------- home & property

_add(EventRule(
    code="griha_pravesh", name="Griha Pravesh (House warming)",
    aliases=("griha pravesh", "gruhapravesam", "housewarming", "house warming", "new house",
             "grihapravesh", "vastu shanti", "graha pravesam"),
    nakshatras=DHRUVA | MRIDU | N("Dhanishta", "Shatabhisha", "Pushya", "Shravana"),
    best_nakshatras=DHRUVA | MRIDU,
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SAT}),
    tithi_good_s=frozenset({2, 3, 5, 7, 10, 11, 13}), tithi_ok_s=frozenset({12, 15}),
    tithi_good_k=frozenset({2, 3, 5}), tithi_ok_k=frozenset({7, 10, 11}),
    period="day", lagna_pref="sthira", lagna_strict=False, moudhyam=True,
    months={"telugu": frozenset({VAISHAKHA, JYESHTHA, SHRAVANA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA}),
            "marathi": frozenset({VAISHAKHA, JYESHTHA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA}),
            "north": frozenset({VAISHAKHA, JYESHTHA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA})},
    ok_months={"telugu": frozenset({SHRAVANA, KARTIKA, MARGASHIRA}),
               "marathi": frozenset({KARTIKA, MARGASHIRA}), "north": frozenset({KARTIKA, MARGASHIRA})},
    avoid_dhanurmasa=True, avoid_chaturmasa={"marathi": True, "north": True},
    requirements=_person("kartha", "Head of the family (owner)") + COMMON + (
        Requirement("house_facing", "Main door facing direction (optional)", False),
    ),
    notes=("Sthira lagna is preferred so the family stays settled in the home.",),
))

_add(EventRule(
    code="bhoomi_puja", name="Bhoomi Puja / Shankusthapana (Foundation)",
    aliases=("bhoomi puja", "bhumi pujan", "shankusthapana", "foundation", "construction start",
             "bhoomi pooja", "slab", "groundbreaking"),
    nakshatras=N("Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
                 "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
                 "Uttara Bhadrapada", "Revati"),
    best_nakshatras=DHRUVA | MRIDU,
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SAT}),
    period="day", lagna_pref="sthira", moudhyam=True,
    months=_all({VAISHAKHA, SHRAVANA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA}),
    avoid_dhanurmasa=False,
    requirements=_person("kartha", "Owner of the land") + COMMON + (
        Requirement("plot_facing", "Plot facing direction (optional)", False),
    ),
))

_add(EventRule(
    code="property_purchase", name="Property / Land Purchase or Registration",
    aliases=("property", "land purchase", "registration", "flat purchase", "plot", "house purchase",
             "registry", "agreement"),
    nakshatras=N("Rohini", "Mrigashira", "Punarvasu", "Pushya", "Magha", "Uttara Phalguni", "Hasta",
                 "Vishakha", "Anuradha", "Moola", "Uttara Ashadha", "Shravana", "Uttara Bhadrapada",
                 "Revati"),
    best_nakshatras=DHRUVA | N("Mrigashira", "Pushya", "Revati"),
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN, SAT}),
    period="day", lagna_pref="sthira", swayam_siddha_override=True, no_adhika=False,
    requirements=_person("kartha", "Buyer") + COMMON,
))

# ---------------------------------------------------------------- purchases & work

_add(EventRule(
    code="vehicle_purchase", name="Vahana (Vehicle purchase / delivery)",
    aliases=("vehicle", "car", "bike", "vahana", "vahan", "two wheeler", "scooter", "car delivery"),
    nakshatras=N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati",
                 "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Revati", "Rohini",
                 "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada"),
    best_nakshatras=KSHIPRA | CHARA_NAK | N("Revati"),
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN}),
    period="day", lagna_pref="chara", swayam_siddha_override=True, no_adhika=False,
    avoid_pitru_paksha=True,
    requirements=_person("kartha", "Owner / buyer") + COMMON,
))

_add(EventRule(
    code="vyapara", name="Vyapara Arambha (Business / shop / office opening)",
    aliases=("business", "shop opening", "office opening", "new business", "startup launch",
             "dukan", "udghatan", "inauguration", "company launch", "showroom", "factory"),
    nakshatras=N("Ashwini", "Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra",
                 "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Uttara Bhadrapada", "Revati"),
    best_nakshatras=KSHIPRA | DHRUVA | N("Revati"),
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN}),
    period="day", lagna_pref="sthira", swayam_siddha_override=True, no_adhika=True,
    requirements=_person("kartha", "Owner / main partner") + COMMON + (
        Requirement("business_type", "Type of business (optional)", False),
    ),
))

_add(EventRule(
    code="job_joining", name="Joining a new job / starting a new role",
    aliases=("job", "joining", "new job", "naukri", "office joining", "new role"),
    nakshatras=N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta",
                 "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
                 "Uttara Bhadrapada", "Revati"),
    varas=frozenset({SUN, MON, WED, THU, FRI}),
    period="day", lagna_pref="sthira_dvi", no_adhika=False, avoid_pitru_paksha=False,
    requirements=_person("kartha", "Person joining") + COMMON,
))

_add(EventRule(
    code="jewellery_purchase", name="Gold / Jewellery purchase",
    aliases=("gold", "jewellery", "jewelry", "silver", "ornaments", "sona", "bangaram"),
    nakshatras=N("Ashwini", "Rohini", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra",
                 "Swati", "Anuradha", "Shravana", "Dhanishta", "Uttara Ashadha",
                 "Uttara Bhadrapada", "Revati"),
    best_nakshatras=N("Pushya", "Rohini", "Revati", "Ashwini"),
    varas=frozenset({SUN, MON, WED, THU, FRI}),
    period="day", lagna_pref="sthira", swayam_siddha_override=True, no_adhika=False,
    requirements=_person("kartha", "Buyer", required=False) + COMMON,
))

_add(EventRule(
    code="yatra", name="Yatra (Travel / pilgrimage start)",
    aliases=("travel", "journey", "trip", "pilgrimage", "yatra", "teerth", "relocation", "moving abroad"),
    nakshatras=N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Anuradha", "Shravana",
                 "Dhanishta", "Revati"),
    varas=frozenset(range(7)),
    period="day", lagna_pref="chara", no_adhika=False, avoid_pitru_paksha=False,
    requirements=_person("kartha", "Main traveller") + COMMON + (
        Requirement("direction", "Direction of travel from home (north/south/east/west)", True),
    ),
    notes=("Disha-shoola (weekday vs direction) is enforced.",),
))

# ---------------------------------------------------------------- samskaras for children

_CHILD = _person("child", "Child") + _person("father", "Father", required=False)

_add(EventRule(
    code="namakarana", name="Namakarana (Naming ceremony)",
    aliases=("naming", "naming ceremony", "namakaran", "barasala", "naamkaran", "baarse", "cradle"),
    nakshatras=N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta",
                 "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
                 "Shatabhisha", "Uttara Bhadrapada", "Revati"),
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN}),
    period="day", lagna_pref="sthira_dvi", no_adhika=False, avoid_pitru_paksha=False,
    personal_roles=("child",),
    requirements=_CHILD + COMMON + (Requirement("child.gender", "Child's gender", True),),
    notes=("Traditionally on the 11th, 12th or 16th day after birth, or any good day later.",),
))

_add(EventRule(
    code="annaprashana", name="Annaprashana (First rice feeding)",
    aliases=("annaprashana", "annaprasana", "first rice", "first food", "mukhe bhaat", "annaprasan"),
    nakshatras=N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta",
                 "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
                 "Shatabhisha", "Uttara Bhadrapada", "Revati"),
    varas=frozenset({MON, WED, THU, FRI}),
    period="morning", lagna_pref="sthira_dvi", personal_roles=("child",),
    requirements=_CHILD + COMMON + (Requirement("child.gender", "Child's gender", True),),
    notes=("Boys in even months (6th, 8th), girls in odd months (5th, 7th) of age - engine checks this.",),
))

_add(EventRule(
    code="chudakarana", name="Chudakarana / Mundan (First haircut)",
    aliases=("mundan", "chudakarana", "first haircut", "tonsure", "puttu ventrukalu", "javal", "choula"),
    nakshatras=N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Jyeshtha",
                 "Shravana", "Dhanishta", "Shatabhisha", "Revati"),
    varas=frozenset({MON, WED, THU, FRI}),
    period="morning", lagna_pref="any", personal_roles=("child",), avoid_chaturmasa={"north": True},
    requirements=_CHILD + COMMON + (Requirement("child.gender", "Child's gender", False),),
    notes=("Usually in the 1st, 3rd or 5th year (odd years).",),
))

_add(EventRule(
    code="karnavedha", name="Karnavedha (Ear piercing)",
    aliases=("ear piercing", "karnavedha", "karna vedha", "chevulu kuttadam", "karnchhedan"),
    nakshatras=N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Anuradha",
                 "Shravana", "Dhanishta", "Revati"),
    varas=frozenset({MON, WED, THU, FRI}),
    period="morning", lagna_pref="any", personal_roles=("child",),
    requirements=_CHILD + COMMON,
))

_add(EventRule(
    code="aksharabhyasam", name="Aksharabhyasam / Vidyarambha (Start of learning)",
    aliases=("aksharabhyasam", "vidyarambha", "vidyarambham", "start of education", "akshar abhyas",
             "school start", "patti pooja", "hate khori"),
    nakshatras=N("Ashwini", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Shravana", "Dhanishta",
                 "Shatabhisha", "Revati", "Mrigashira", "Ardra", "Moola", "Purva Phalguni",
                 "Purva Ashadha", "Purva Bhadrapada", "Anuradha"),
    best_nakshatras=N("Shravana", "Pushya", "Punarvasu", "Hasta", "Revati", "Ashwini"),
    varas=frozenset({SUN, WED, THU, FRI}), ok_varas=frozenset({MON}),
    tithi_good_s=frozenset({2, 3, 5, 6, 10, 11, 12}), tithi_ok_s=frozenset({7, 13, 15}),
    period="morning", lagna_pref="dvi", moudhyam=True, personal_roles=("child",),
    swayam_siddha_override=True,
    requirements=_CHILD + COMMON,
    notes=("Vasant Panchami and Vijayadashami are especially auspicious.",),
))

_add(EventRule(
    code="upanayana", name="Upanayana (Sacred thread ceremony)",
    aliases=("upanayanam", "upanayana", "thread ceremony", "janeu", "munj", "vratabandha", "odugu"),
    nakshatras=N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta",
                 "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
                 "Shatabhisha", "Uttara Bhadrapada", "Revati", "Purva Phalguni", "Purva Ashadha",
                 "Purva Bhadrapada"),
    varas=frozenset({SUN, MON, WED, THU, FRI}), ok_varas=frozenset(),
    tithi_good_s=frozenset({2, 3, 5, 10, 11, 12}), tithi_ok_s=frozenset({7, 13}),
    tithi_good_k=frozenset({2, 3, 5}), tithi_ok_k=frozenset(),
    period="morning", lagna_pref="any", lagna_strict=True, moudhyam=True,
    months=_all({MAGHA, PHALGUNA, CHAITRA, VAISHAKHA, JYESHTHA}),
    avoid_dhanurmasa=True, personal_roles=("child",),
    requirements=_CHILD + COMMON,
    notes=("Uttarayana and Shukla paksha are strongly preferred.",),
))

_add(EventRule(
    code="seemantham", name="Seemantham / Godh Bharai (Baby shower)",
    aliases=("seemantham", "baby shower", "godh bharai", "valaikappu", "dohale jevan", "srimantham",
             "pumsavana"),
    nakshatras=N("Rohini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Moola", "Shravana",
                 "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Revati", "Anuradha"),
    varas=frozenset({SUN, TUE, THU}), ok_varas=frozenset({MON, WED, FRI}),
    period="morning", lagna_pref="any", personal_roles=("wife",),
    requirements=_person("wife", "Mother-to-be") + _person("husband", "Husband", required=False)
    + COMMON + (Requirement("pregnancy_month", "Current month of pregnancy", True),),
    notes=("Usually done in the 5th, 7th or 9th month of pregnancy (family custom varies).",),
))

# ---------------------------------------------------------------- worship

_add(EventRule(
    code="pooja", name="Pooja / Homa / Vratam (Satyanarayana, Ganapati homa, etc.)",
    aliases=("pooja", "puja", "homa", "havan", "satyanarayana", "vratam", "abhishekam",
             "rudrabhishekam", "navagraha", "ganapati homam", "lakshmi pooja", "katha"),
    nakshatras=frozenset(range(27)),
    best_nakshatras=DHRUVA | MRIDU | KSHIPRA,
    varas=frozenset(range(7)),
    tithi_good_s=frozenset({2, 3, 5, 7, 10, 11, 13, 15}), tithi_ok_s=frozenset({1, 4, 6, 8, 9, 12, 14}),
    tithi_good_k=frozenset({1, 2, 3, 5, 11}), tithi_ok_k=frozenset({4, 6, 7, 8, 9, 10, 12, 13, 14, 15}),
    period="day", lagna_pref="any", no_adhika=False, avoid_pitru_paksha=False,
    avoid_bad_yoga=False, avoid_vishti=False,
    requirements=_person("kartha", "Yajamana (person performing)", required=False) + COMMON + (
        Requirement("deity", "Which pooja / deity", True),
    ),
    notes=("Satyanarayana vratam is best on Purnima, Ekadashi or Sankranti; "
           "Shiva poojas suit Pradosha and Masa-shivaratri - the Acharya should mention these.",),
))

_add(EventRule(
    code="pratishtha", name="Devata Pratishtha (Idol installation)",
    aliases=("pratishtha", "idol installation", "murti sthapana", "prana pratishtha", "temple"),
    nakshatras=N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta",
                 "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
                 "Shatabhisha", "Uttara Bhadrapada", "Revati"),
    best_nakshatras=DHRUVA | MRIDU | N("Pushya", "Shravana"),
    varas=frozenset({MON, WED, THU, FRI}),
    period="day", lagna_pref="sthira", lagna_strict=True, moudhyam=True,
    months=_all({CHAITRA, VAISHAKHA, JYESHTHA, MAGHA, PHALGUNA}),
    avoid_dhanurmasa=True,
    requirements=_person("kartha", "Yajamana / trustee", required=False) + COMMON + (
        Requirement("deity", "Which deity", True),
    ),
))

GENERAL = EventRule(
    code="general", name="General auspicious beginning",
    aliases=("auspicious", "good time", "shubh muhurat", "general"),
    nakshatras=DHRUVA | MRIDU | KSHIPRA | CHARA_NAK,
    varas=frozenset({MON, WED, THU, FRI}), ok_varas=frozenset({SUN}),
    period="day", lagna_pref="sthira_dvi",
    requirements=_person("kartha", "Main person", required=False) + COMMON + (
        Requirement("purpose", "What is being started", True),
    ),
)
_add(GENERAL)


def find_event(text: str) -> EventRule:
    t = (text or "").strip().lower()
    if t in EVENTS:
        return EVENTS[t]
    for e in EVENTS.values():
        if t == e.name.lower() or any(a == t for a in e.aliases):
            return e
    for e in EVENTS.values():
        if any(a in t for a in e.aliases) or t in e.name.lower():
            return e
    return GENERAL
