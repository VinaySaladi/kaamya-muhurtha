"""
Accuracy harness: compare the engine with muhurthams fixed by Kaamya's pandits.

Usage:
    python -m validation.validate validation/pandit_muhurthams.csv  [--out validation/report.csv]

CSV columns (one row per muhurtham the pandit actually gave a family) - see template.csv:
    case_id, event, venue_city, tradition, pandit_start, pandit_end,
    p1_role, p1_name, p1_dob, p1_tob, p1_birthplace, p1_nakshatra, p1_rashi,
    p2_role, p2_name, p2_dob, p2_tob, p2_birthplace, p2_nakshatra, p2_rashi,
    window_days (optional, default 60: the search window centred on the pandit's date)

Three agreement measures (reported per event and overall):
  RULE   - the engine's rule book accepts the pandit's exact time        (target >= 95%)
  DAY    - the pandit's date is among the engine's candidate days        (target >= 95%)
  TOP3   - the pandit's date is in the engine's top-3 for that window    (informational)
Disagreements are listed with the rule that blocked them so the rule book can be tuned.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from app import service
from app.astro import ephemeris as E
from app.rules.engine import Query, evaluate_interval, search
from app.rules.events import find_event


def _persons(row):
    out = []
    for k in ("p1", "p2"):
        if not (row.get(f"{k}_role") or "").strip():
            continue
        d = {"role": row[f"{k}_role"].strip(), "name": row.get(f"{k}_name", "")}
        for f in ("dob", "tob", "birthplace", "nakshatra", "rashi"):
            v = (row.get(f"{k}_{f}") or "").strip()
            if v:
                d[f] = v
        out.append(service.person_from(d))
    return out


def run(path: str, out: str | None):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    stats = defaultdict(lambda: {"n": 0, "rule": 0, "day": 0, "top3": 0})
    report = []
    for row in rows:
        try:
            place, region = service.place_from(row["venue_city"])
            if row.get("tradition"):
                region = row["tradition"].strip().lower()
            ev = find_event(row["event"])
            s = datetime.fromisoformat(row["pandit_start"]).replace(tzinfo=place.zone)
            e = datetime.fromisoformat(row["pandit_end"]).replace(tzinfo=place.zone) if row.get("pandit_end") \
                else s + timedelta(minutes=30)
            persons = _persons(row)
            half = int(row.get("window_days") or 60) // 2
            q = Query(ev.code, s.date() - timedelta(days=half), s.date() + timedelta(days=half), place, region,
                      persons, options=3)
            chk = evaluate_interval(q, E.dt_to_ut(s), E.dt_to_ut(e))
            res = search(q)
            # all candidate days: rerun with a large option count
            q.options = 400
            def days_of(opts):  # Hindu day and civil date of each option (pre-dawn times differ)
                return {o["option_id"].split("-", 1)[1][:10] for o in opts} | {o["date"] for o in opts}
            all_days = days_of(search(q)["options"])
            top3 = days_of(res["options"])
            hd = {chk["hindu_day"], s.date().isoformat()}
            r = {"case_id": row.get("case_id"), "event": ev.code, "pandit_start": row["pandit_start"],
                 "rule_ok": chk["pass"], "day_ok": bool(hd & all_days), "top3": bool(hd & top3),
                 "engine_reasons": "; ".join(chk.get("reasons", [])),
                 "engine_top3": " | ".join(f"{o['start']} ({o['quality']})" for o in res["options"])}
        except Exception as ex:  # bad row
            r = {"case_id": row.get("case_id"), "event": row.get("event"), "pandit_start": row.get("pandit_start"),
                 "rule_ok": False, "day_ok": False, "top3": False, "engine_reasons": f"ROW ERROR: {ex}",
                 "engine_top3": ""}
        report.append(r)
        for key in (r["event"], "ALL"):
            st = stats[key]
            st["n"] += 1
            st["rule"] += r["rule_ok"]
            st["day"] += r["day_ok"]
            st["top3"] += r["top3"]

    print(f"{'event':22} {'cases':>5} {'RULE':>7} {'DAY':>7} {'TOP3':>7}")
    for k, st in sorted(stats.items(), key=lambda x: (x[0] == "ALL", x[0])):
        n = st["n"]
        print(f"{k:22} {n:5d} {st['rule']/n:7.1%} {st['day']/n:7.1%} {st['top3']/n:7.1%}")
    bad = [r for r in report if not r["rule_ok"]]
    if bad:
        print("\nDisagreements (engine rule that blocked the pandit's time):")
        for r in bad[:40]:
            print(f"  {r['case_id']:>6} {r['event']:18} {r['pandit_start']}  ->  {r['engine_reasons']}")
    if out:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(report[0].keys()))
            w.writeheader()
            w.writerows(report)
        print(f"\nDetailed report written to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out")
    a = ap.parse_args()
    run(a.csv, a.out)
