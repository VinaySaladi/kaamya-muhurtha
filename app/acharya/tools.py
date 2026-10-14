"""Tools the Acharya can call. Each tool is a thin wrapper over the deterministic service layer."""
from __future__ import annotations

import json
import re

from .. import service, store
from ..config import settings
from ..rules.events import EVENTS

TOOLS = [
    {
        "name": "get_event_requirements",
        "description": "Get the list of details needed to fix a muhurtham for an event, and whose birth stars are checked. "
                       "Call this as soon as you know the event.",
        "input_schema": {"type": "object", "properties": {
            "event": {"type": "string", "description": "Event code (e.g. vivaha, griha_pravesh) or the family's words"}},
            "required": ["event"]},
    },
    {
        "name": "lookup_place",
        "description": "Resolve a city / town name to coordinates and time zone. Use for venues and birthplaces when unsure.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
    {
        "name": "compute_birth_star",
        "description": "Compute and remember a person's janma nakshatra, pada and rashi from date, time and place of birth.",
        "input_schema": {"type": "object", "properties": {
            "role": {"type": "string", "description": "kartha | bride | groom | child | father | wife | husband"},
            "name": {"type": "string"},
            "dob": {"type": "string", "description": "YYYY-MM-DD"},
            "tob": {"type": "string", "description": "HH:MM 24h, or omit if unknown"},
            "birthplace": {"type": "string"},
            "gender": {"type": "string", "description": "male | female (needed for child events)"}},
            "required": ["role", "name", "dob", "birthplace"]},
    },
    {
        "name": "set_known_star",
        "description": "Remember a person's janma nakshatra (and rashi / pada if known) when the family knows it but not the birth time.",
        "input_schema": {"type": "object", "properties": {
            "role": {"type": "string"}, "name": {"type": "string"},
            "nakshatra": {"type": "string"}, "rashi": {"type": "string"}, "pada": {"type": "integer"},
            "gender": {"type": "string"}, "dob": {"type": "string", "description": "YYYY-MM-DD if known"}},
            "required": ["role", "name", "nakshatra"]},
    },
    {
        "name": "find_muhurtham",
        "description": "Search the panchang for the best muhurthams. Uses the people remembered via compute_birth_star / set_known_star.",
        "input_schema": {"type": "object", "properties": {
            "event": {"type": "string", "enum": list(EVENTS.keys())},
            "from_date": {"type": "string", "description": "YYYY-MM-DD"},
            "to_date": {"type": "string", "description": "YYYY-MM-DD"},
            "venue": {"type": "string", "description": "City where the event happens"},
            "time_pref": {"type": "string", "enum": ["any", "morning", "afternoon", "evening", "night", "predawn", "daytime"]},
            "weekdays": {"type": "array", "items": {"type": "string"},
                         "description": "Only these civil weekdays, e.g. ['Saturday','Sunday'] if family needs weekends"},
            "avoid_dates": {"type": "array", "items": {"type": "string"}},
            "direction": {"type": "string", "description": "For travel: north | south | east | west"},
            "tradition": {"type": "string", "enum": ["telugu", "marathi", "north"],
                          "description": "Only if the family's tradition differs from the venue's region"},
            "options": {"type": "integer", "description": "How many options (2-3)", "default": 3}},
            "required": ["event", "from_date", "to_date", "venue"]},
    },
    {
        "name": "get_panchang",
        "description": "Daily panchang (tithi, nakshatra, Rahu Kalam, etc.) for a date and place.",
        "input_schema": {"type": "object", "properties": {
            "date": {"type": "string"}, "place": {"type": "string"}}, "required": ["date", "place"]},
    },
    {
        "name": "submit_for_review",
        "description": "Send the chosen options (from the latest find_muhurtham result) for the senior pandit's verification.",
        "input_schema": {"type": "object", "properties": {
            "option_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3},
            "explanations": {"type": "object", "additionalProperties": {"type": "string"},
                             "description": "option_id -> 2-4 sentence explanation in the family's language"},
            "message_to_family": {"type": "string", "description": "Short closing message in the family's language"},
            "note_for_pandit": {"type": "string", "description": "English: anything the pandit should double-check"},
            "family_request": {"type": "string",
                               "description": "What the family added or asked when you asked if there was anything else, "
                                              "in their own words; empty if nothing"}},
            "required": ["option_ids", "explanations", "note_for_pandit"]},
    },
    {
        "name": "add_family_note",
        "description": "After submit_for_review: pass something the family added (detail, preference or question) "
                       "to the reviewing pandit, in the family's own words.",
        "input_schema": {"type": "object", "properties": {
            "text": {"type": "string", "description": "The family's words"}}, "required": ["text"]},
    },
    {
        "name": "show_inputs",
        "description": "Tell the app which input widgets to show for your current question.",
        "input_schema": {"type": "object", "properties": {
            "fields": {"type": "array", "items": {"type": "object", "properties": {
                "key": {"type": "string"},
                "type": {"type": "string", "enum": ["date", "time", "date_range", "place", "choice", "text"]},
                "label": {"type": "string"},
                "choices": {"type": "array", "items": {"type": "string"}}},
                "required": ["key", "type", "label"]}}},
            "required": ["fields"]},
    },
]


def run_tool(name: str, args: dict, session: dict) -> dict:
    data = session["data"]
    lang = session["lang"]
    try:
        if name == "get_event_requirements":
            r = service.event_requirements(args["event"])
            data["event"] = r["code"]
            return r
        if name == "lookup_place":
            c = service.place_candidates(args["query"])
            return {"candidates": c} if c else {"error": "Not found - ask for the nearest big city"}
        if name in ("compute_birth_star", "set_known_star"):
            spec = {k: v for k, v in args.items() if v not in (None, "")}
            person = service.person_from(spec)
            people = [p for p in data.setdefault("people", []) if p.get("role") != spec["role"]]
            people.append(spec)
            data["people"] = people
            return service.janma_summary(person, lang)
        if name == "find_muhurtham":
            res = service.find_muhurtham(
                event=args["event"], from_date=args["from_date"], to_date=args["to_date"],
                venue=args["venue"], persons=data.get("people", []), time_pref=args.get("time_pref", "any"),
                weekdays=args.get("weekdays"), avoid_dates=args.get("avoid_dates"),
                direction=args.get("direction"), tradition=args.get("tradition"),
                options=args.get("options", 3), lang=lang, max_window_days=settings.max_window_days)
            data["event"] = args["event"]
            data["last_search"] = res
            data["search_args"] = args
            return res if settings.auto_approve else redact_for_review(res)
        if name == "get_panchang":
            p = service.panchang(args["date"], args["place"], lang)
            data.setdefault("panchang_seen", []).append(p["date"])
            return p
        if name == "submit_for_review":
            return _submit(args, session)
        if name == "add_family_note":
            return _add_family_note(args, session)
        if name == "show_inputs":
            data["ui_fields"] = args.get("fields", [])
            return {"ok": True}
        return {"error": f"unknown tool {name}"}
    except service.InputError as e:
        return {"error": str(e)}
    except Exception as e:  # never crash the conversation
        return {"error": f"internal error: {type(e).__name__}: {e}"}


def _add_family_note(args: dict, session: dict) -> dict:
    text = (args.get("text") or "").strip()[:1000]
    if not text:
        return {"error": "Empty note"}
    req = store.get_request(session["request_id"]) if session.get("request_id") else None
    if not req:
        return {"error": "Nothing submitted yet - include it in family_request when you call submit_for_review"}
    if req["status"] != "PENDING_REVIEW":
        return {"error": f"The pandit has already finished ({req['status']}); the family can see the result in the app"}
    draft = req.get("draft") or {}
    notes = draft.setdefault("family_notes", [])
    if len(notes) >= 20:
        return {"error": "Too many notes already - ask the family to wait for the pandit"}
    notes.append(text)
    store.update_request(req["id"], draft=draft)
    return {"ok": True, "message": "The reviewing pandit will see this note"}


def _submit(args: dict, session: dict) -> dict:
    data = session["data"]
    res = data.get("last_search")
    if not res or not res.get("options"):
        return {"error": "No search result to submit - call find_muhurtham first"}
    by_id = {o["option_id"]: o for o in res["options"]}
    bad = [i for i in args["option_ids"] if i not in by_id]
    if bad:
        return {"error": f"Unknown option ids {bad}. Use ids from the latest find_muhurtham result."}
    if session.get("request_id"):
        existing = store.get_request(session["request_id"])
        if existing and existing["status"] in ("PENDING_REVIEW", "APPROVED", "DELIVERED"):
            return {"error": "Already submitted", "request_id": existing["id"], "status": existing["status"]}
    draft = {
        "option_ids": args["option_ids"],
        "explanations": args.get("explanations", {}),
        "message_to_family": args.get("message_to_family", ""),
        "note_for_pandit": args.get("note_for_pandit", ""),
        "explanation_warnings": _check_explanations(args.get("explanations", {}), by_id),
        # What the family added or asked in their own words (shown to the reviewing pandit)
        "family_notes": [n for n in [(args.get("family_request") or "").strip()[:1000]] if n],
    }
    review_input = {"people": data.get("people", []), "search_args": data.get("search_args", {})}
    req = store.create_request(session, data.get("event", "general"), session["lang"], res, draft, review_input)
    session["request_id"] = req["id"]
    session["state"] = "SUBMITTED"
    if settings.auto_approve:
        from ..review import approve
        req = approve(req["id"], reviewer="auto", option_ids=args["option_ids"])
        return {"request_id": req["id"], "status": req["status"], "final": req["final"]}
    return {"request_id": req["id"], "status": "PENDING_REVIEW",
            "promise_hours": settings.review_promise_hours}


def redact_for_review(res: dict) -> dict:
    """In pandit-review mode the Acharya never sees option dates/times, so it cannot reveal them early."""
    out = {k: v for k, v in res.items() if k not in ("options", "rejected_days_sample")}
    out["options"] = [{
        "option_id": o["option_id"], "quality": o["quality"], "score": o["score"],
        "masa": o["panchang"]["masa"], "nakshatra": o["panchang"]["nakshatra"], "tithi": o["panchang"]["tithi"],
        "paksha": o["panchang"]["paksha"], "lagna": o["panchang"]["lagna"], "lagna_type": o["panchang"]["lagna_type"],
        "duration_minutes": o["duration_minutes"], "why_good": o["why_good"], "cautions": o["cautions"],
    } for o in res.get("options", [])]
    out["note"] = ("Dates and times are hidden until the senior pandit approves. Write explanations from "
                   "why_good / cautions only; do not mention any date or time.")
    out["rejected_reasons_summary"] = sorted(set(res.get("rejected_days_sample", {}).values()))[:6]
    return out


_TIME = re.compile(r"\b([01]?\d|2[0-3])[:.][0-5]\d\b")


def _check_explanations(expl: dict, by_id: dict) -> list[str]:
    """Flag any clock time in an explanation that is not the option's own start/end time."""
    warns = []
    for oid, text in expl.items():
        o = by_id.get(oid)
        if not o:
            warns.append(f"{oid}: explanation for unknown option")
            continue
        allowed = {o["start"][-5:], o["end"][-5:], o["start_time"][:5], o["end_time"][:5]}
        allowed |= {x.lstrip("0") for x in allowed}
        for m in _TIME.finditer(text or ""):
            if m.group(0).replace(".", ":") not in allowed and m.group(0).replace(".", ":").lstrip("0") not in allowed:
                warns.append(f"{oid}: mentions time {m.group(0)} not in the option")
    return warns


def tool_result_text(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, default=str)
