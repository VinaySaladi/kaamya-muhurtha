"""Generate docs/RULEBOOK.md from app/rules/events.py (run after any rule change)."""
from app import i18n as L
from app.rules.events import EVENTS, BAD_YOGAS, WORST_YOGAS, SARVARTHA_SIDDHI, SWAYAM_SIDDHA
from app.astro.panchang import VARJYAM_GHATI, AMRITA_GHATI, DURMUHURTA_DAY, RAHU_PART, YAMA_PART, GULIKA_PART

V, N, M = L.VARA["en"], L.NAKSHATRA["en"], L.MASA["en"]
def names(idx, table): return ", ".join(table[i] for i in sorted(idx)) or "-"
def tithis(s): return ", ".join(str(x) for x in sorted(s)) or "-"
LAGNA = {"any": "any (lagna shuddhi still applies)", "sthira": "Sthira (fixed) preferred", "chara": "Chara (movable) preferred",
         "dvi": "Dvisvabhava (dual) preferred", "sthira_dvi": "Sthira or Dvisvabhava preferred"}
PERIOD = {"day": "sunrise to sunset", "any": "any time of day or night", "morning": "sunrise to about 1:30 pm"}

out = ["# Kaamya Muhurtha - Rule Book (for senior pandit review)", "",
       "Generated from the engine's own rule tables. Every line is a rule the engine applies.",
       "Please mark changes in the margin; Vinay/Claude will update `app/rules/events.py` and regenerate.", "",
       "## 1. Calculation standard", "",
       "- Drik-ganita (modern astronomical) positions, geocentric, true-of-date.",
       "- Ayanamsa: Lahiri (Chitrapaksha). Verified against published panchangams to within 1 minute.",
       "- Months: amanta (Telugu & Marathi). North (Hindi) tradition shows purnimanta month names.",
       "- Hindu day (vara) runs sunrise to next sunrise. A 4:30 am muhurtham on Friday belongs to Thursday's vara.",
       "- Sunrise/sunset: upper limb of the Sun with standard refraction, at the venue.", "",
       "## 2. Rules applied to every auspicious event", "",
       "| Check | Rule |", "|---|---|",
       f"| Rahu Kalam | never (day divided in 8; part by weekday Sun..Sat = {RAHU_PART}) |",
       f"| Yamagandam | never in Telugu tradition; small penalty elsewhere (parts {YAMA_PART}) |",
       f"| Gulika Kalam | small penalty (parts {GULIKA_PART}) |",
       f"| Durmuhurtham | never (day muhurtas of 15 by weekday {DURMUHURTA_DAY}; Tuesday also night 7th) |",
       "| Varjyam (Thyajyam) | never - 4 ghatis starting at the nakshatra's tyajya ghati (table below) |",
       "| Amrita Kalam | bonus |", "| Abhijit muhurtham | bonus (not on Wednesday) |",
       f"| Bad yogas | avoided: {', '.join(L.YOGA_EN[i] for i in sorted(BAD_YOGAS))}; {', '.join(L.YOGA_EN[i] for i in sorted(WORST_YOGAS))} never |",
       "| Vishti (Bhadra) karana | avoided |",
       "| Pitru Paksha (Bhadrapada Krishna) | no new beginnings (except pooja, travel, job, naming) |",
       "| Eclipse day (visible at the venue) | avoided (except pooja) |",
       "| Holashtak (North only) | Phalguna Shukla 8 to Purnima avoided for marriage, griha pravesh, engagement, business |",
       "| Tarabalam | count from janma nakshatra; 3 Vipat, 5 Pratyak, 7 Naidhana are bad |",
       "| Chandrabalam | Moon's rashi 4th, 8th, 12th from janma rashi is bad |",
       "| Which governs | **Shukla paksha: chandrabalam is enforced, tarabalam scored. Krishna paksha: tarabalam enforced, chandrabalam scored.** |",
       "| Janma nakshatra day | not allowed for marriage, engagement, upanayana; small penalty for others |",
       "| Lagna | not 8th from janma rashi (janma-ashtama); 12th is a small penalty |",
       "| Lagna shuddhi (all) | no malefic (Sun, Mars, Saturn, Rahu, Ketu) in 8th; Moon not in 8th |",
       "| Lagna shuddhi (strict events) | also 7th free of malefics, Moon not in 6/8/12; for marriage Venus not in 6th |",
       "| Benefics | Jupiter/Venus/Mercury in kendra, Jupiter in trikona: bonus |",
       "| Moudhyam | Guru within 11 deg of Sun; Shukra within 10 deg (8 deg if retrograde) - forbids marked events |",
       "| Dhanurmasa | Sun in Dhanu: marked events avoided (North also Meena - Kharmas) |",
       "| Chaturmasa | Ashadha Shukla 11 to Kartika Shukla 11 - marked events/regions |", "",
       "Special bonuses: Sarvartha Siddhi yoga (weekday + star), Guru/Ravi Pushya for purchases, swayam-siddha days: "
       + ", ".join(f"{v} ({M[k[0]]} {'Shukla' if k[1]==0 else 'Krishna'} {k[2]})" for k, v in SWAYAM_SIDDHA.items()) + ".", "",
       "### Sarvartha Siddhi yoga table", "", "| Weekday | Nakshatras |", "|---|---|"]
out += [f"| {V[d]} | {names(s, N)} |" for d, s in SARVARTHA_SIDDHI.items()]
out += ["", "### Varjyam and Amrita starting ghati (of 60) per nakshatra", "", "| Nakshatra | Varjyam | Amrita |", "|---|---|---|"]
out += [f"| {N[i]} | {VARJYAM_GHATI[i]} | {AMRITA_GHATI[i]} |" for i in range(27)]
out += ["", "## 3. Event rules", ""]
for e in EVENTS.values():
    out += [f"### {e.name}  (`{e.code}`)", "",
            f"- **Nakshatras allowed:** {names(e.nakshatras, N) if len(e.nakshatras) < 27 else 'all'}",
            f"- **Best nakshatras (bonus):** {names(e.best_nakshatras, N)}",
            f"- **Weekdays:** {names(e.varas, V)}" + (f"; acceptable with penalty: {names(e.ok_varas, V)}" if e.ok_varas else ""),
            f"- **Tithis - Shukla good:** {tithis(e.tithi_good_s)}; acceptable: {tithis(e.tithi_ok_s)}",
            f"- **Tithis - Krishna good:** {tithis(e.tithi_good_k)}; acceptable: {tithis(e.tithi_ok_k)} (15 = Purnima in Shukla / Amavasya in Krishna)",
            f"- **Time of day:** {PERIOD.get(e.period, e.period)}" + (" (+ pre-dawn up to 2.5 h before sunrise)" if e.code == "griha_pravesh" else "")
            + (" (Marathi: daytime and godhuli only)" if e.code == "vivaha" else ""),
            f"- **Lagna:** {LAGNA[e.lagna_pref]}; strict lagna shuddhi: {'yes' if e.lagna_strict else 'no'}",
            f"- **Moudhyam forbids:** {'yes' if e.moudhyam else 'no'}; **Adhika masa forbids:** {'yes' if e.no_adhika else 'no'}; "
            f"**Dhanurmasa forbids:** {'yes' if e.avoid_dhanurmasa else 'no'}; **Pitru paksha forbids:** {'yes' if e.avoid_pitru_paksha else 'no'}",
            f"- **Chaturmasa forbids in:** {', '.join(k for k, v in (e.avoid_chaturmasa or {}).items() if v) or '-'}",
            f"- **Whose stars are checked:** {', '.join(e.personal_roles)}"]
    if e.months:
        out += [f"- **Months allowed - {r}:** {names(m, M)}" for r, m in e.months.items()]
    if e.ok_months:
        out += [f"- **Months acceptable (penalty) - {r}:** {names(m, M)}" for r, m in e.ok_months.items() if m]
    if e.swayam_siddha_override:
        out.append("- Swayam-siddha days override the nakshatra/tithi list.")
    for n in e.notes:
        out.append(f"- Note: {n}")
    out.append("")
out += ["## 4. Scoring and quality labels", "",
        "Start 50. Bonuses for best nakshatra (+8), good tithi (+6), good weekday (+5), favourable tara/chandra (+3 each per person),",
        "preferred lagna (+5 to +8), benefics in kendra (+2/+3), Abhijit (+4), Amrita (+5), Sarvartha Siddhi (+6), swayam-siddha (+8),",
        "comfortable window length (up to +4). Penalties for acceptable-but-not-ideal factors. Capped at 100.", "",
        "| Score | Label shown |", "|---|---|", "| 85+ | Uttama (excellent) |", "| 72-84 | Shubha (good) |",
        "| 60-71 | Madhyama (acceptable) |", "| below 60 | Adhama - only shown if nothing better exists |", ""]
open("docs/RULEBOOK.md", "w", encoding="utf-8").write("\n".join(out))
print("docs/RULEBOOK.md written", len(out), "lines")
