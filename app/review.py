"""
Pandit review workflow (beta = option C: AI drafts, pandit approves).

PENDING_REVIEW --approve--> APPROVED --(app fetches)--> DELIVERED
               --replace--> APPROVED   (pandit supplies own times; engine checks them)
               --reject---> NEEDS_MANUAL (handled in the existing manual Muhurth flow)
Personal data is purged at APPROVED.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime

import httpx

from . import store
from .astro import ephemeris as E
from .astro.panchang import day_panchang, to_dict
from .config import settings
from .service import InputError, place_from

log = logging.getLogger("kaamya.review")


def _notify(req: dict) -> None:
    if not settings.webhook_url:
        return
    body = json.dumps({"type": "muhurtha.status", "request_id": req["id"], "status": req["status"],
                       "customer_ref": req.get("customer_ref")}, ensure_ascii=False).encode()
    headers = {"Content-Type": "application/json"}
    if settings.webhook_secret:
        headers["X-Kaamya-Signature"] = hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    try:
        httpx.post(settings.webhook_url, content=body, headers=headers, timeout=8.0)
    except Exception as e:  # webhook failures must not break review
        log.warning("webhook failed: %s", e)


def _final(req: dict, options: list[dict], reviewer: str, note: str | None, changed: bool) -> dict:
    draft = req.get("draft") or {}
    return {
        "request_id": req["id"],
        "event": (req.get("engine") or {}).get("event"),
        "lang": req["lang"],
        "place": (req.get("engine") or {}).get("place"),
        "verified_by": reviewer,
        "verified_at": store.now(),
        "pandit_adjusted": changed,
        "options": options,
        "message_to_family": draft.get("message_to_family", ""),
        "pandit_note": note or "",
    }


def approve(rid: str, reviewer: str, option_ids: list[str] | None = None,
            explanation_edits: dict[str, str] | None = None, option_notes: dict[str, str] | None = None,
            note: str | None = None) -> dict:
    req = store.get_request(rid)
    if not req:
        raise InputError("request not found")
    if req["status"] != "PENDING_REVIEW":
        raise InputError(f"request is {req['status']}")
    engine, draft = req["engine"], req.get("draft") or {}
    by_id = {o["option_id"]: o for o in engine.get("options", [])}
    ids = option_ids or draft.get("option_ids") or list(by_id)
    if any(i not in by_id for i in ids):
        raise InputError("unknown option id")
    expl = dict(draft.get("explanations", {}))
    expl.update(explanation_edits or {})
    options = []
    for i in ids:
        o = dict(by_id[i])
        o["explanation"] = expl.get(i, "")
        o["pandit_note"] = (option_notes or {}).get(i, "")
        options.append(o)
    changed = ids != draft.get("option_ids") or bool(explanation_edits)
    final = _final(req, options, reviewer, note, changed)
    req = store.update_request(rid, status="APPROVED", final=final, reviewer=reviewer, note=note)
    store.audit(rid, req["event"], "approved", engine, changed)
    store.purge_personal_data(rid)
    req = store.get_request(rid)
    _notify(req)
    return req


def check_custom_time(venue, start: str, end: str, lang: str = "en") -> dict:
    """Engine check of a pandit-supplied time: panchang at that moment + inauspicious overlaps."""
    place, _ = place_from(venue)
    s = datetime.fromisoformat(start).replace(tzinfo=place.zone)
    e = datetime.fromisoformat(end).replace(tzinfo=place.zone)
    us, ue = E.dt_to_ut(s), E.dt_to_ut(e)
    d = s.date()
    p = day_panchang(d, place)
    if us < p.sunrise:  # before sunrise -> previous Hindu day
        from datetime import timedelta
        p = day_panchang(d - timedelta(days=1), place)
    pd = to_dict(p, lang)
    warn = []
    for label, (a, b) in (("Rahu Kalam", p.rahu), ("Yamagandam", p.yamaganda), ("Gulika Kalam", p.gulika)):
        if us < b and ue > a:
            warn.append(f"overlaps {label}")
    for a, b in p.durmuhurtas:
        if us < b and ue > a:
            warn.append("overlaps Durmuhurtham")
    for a, b in p.varjyams:
        if us < b and ue > a:
            warn.append("overlaps Varjyam")
    at = lambda lst: next((x for x in lst if x["from"] <= s.strftime("%Y-%m-%d %H:%M") < x["to"]), lst[0])
    return {"panchang": {"tithi": at(pd["tithi"])["name"], "nakshatra": at(pd["nakshatra"])["name"],
                         "yoga": at(pd["yoga"])["name"], "karana": at(pd["karana"])["name"],
                         "lagna": at(pd["lagna"])["name"], "masa": pd["masa"], "vara": pd["vara"]},
            "warnings": warn}


def replace(rid: str, reviewer: str, options: list[dict], note: str | None = None) -> dict:
    """options: [{date?, start: 'YYYY-MM-DDTHH:MM', end: ..., explanation, pandit_note}]"""
    req = store.get_request(rid)
    if not req or req["status"] != "PENDING_REVIEW":
        raise InputError("request not pending review")
    venue = (req.get("engine") or {}).get("place") or {}
    out = []
    for n, o in enumerate(options, 1):
        chk = check_custom_time(venue, o["start"], o["end"], req["lang"])
        s = datetime.fromisoformat(o["start"])
        e = datetime.fromisoformat(o["end"])
        out.append({
            "option_id": f"pandit-{n}", "date": s.date().isoformat(), "weekday": chk["panchang"]["vara"],
            "start": s.strftime("%Y-%m-%d %H:%M"), "end": e.strftime("%Y-%m-%d %H:%M"),
            "start_time": s.strftime("%I:%M %p"), "end_time": e.strftime("%I:%M %p"),
            "quality": "pandit_selected", "panchang": chk["panchang"],
            "explanation": o.get("explanation", ""), "pandit_note": o.get("pandit_note", ""),
            "engine_warnings": chk["warnings"],
        })
    final = _final(req, out, reviewer, note, True)
    req = store.update_request(rid, status="APPROVED", final=final, reviewer=reviewer, note=note)
    store.audit(rid, req["event"], "approved", req["engine"], True)
    store.purge_personal_data(rid)
    req = store.get_request(rid)
    _notify(req)
    return req


def reject(rid: str, reviewer: str, reason: str) -> dict:
    req = store.get_request(rid)
    if not req or req["status"] != "PENDING_REVIEW":
        raise InputError("request not pending review")
    req = store.update_request(rid, status="NEEDS_MANUAL", reviewer=reviewer, note=reason)
    store.audit(rid, req["event"], "rejected", req["engine"], True)
    _notify(req)
    return req


def close_manual(rid: str) -> dict:
    """Manual flow finished elsewhere - delete personal data."""
    store.update_request(rid, status="CLOSED")
    store.purge_personal_data(rid)
    return store.get_request(rid)
