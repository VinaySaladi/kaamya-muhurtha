"""
Kaamya Muhurtha API.

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8080
Docs: /docs (Swagger) once running.

Auth
  X-API-Key   : KAAMYA_API_KEY   - the Kaamya app backend (never ship this key in the mobile/web client)
  X-Admin-Key : KAAMYA_ADMIN_KEY - admin console / pandit review screens
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query as Q
from pydantic import BaseModel, Field

from . import review, service, store
from .acharya import agent
from .acharya.prompt import GREETING
from .config import settings
from .rules.engine import ENGINE_VERSION

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Kaamya Muhurtha API", version=ENGINE_VERSION,
              description="Muhurtham engine + Kaamya Acharya for the Kaamya app (Vaidikya Technologies Pvt Ltd).")


# ---------------------------------------------------------------- auth

def app_auth(x_api_key: str | None = Header(default=None)):
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(401, "invalid API key")


def admin_auth(x_admin_key: str | None = Header(default=None)):
    if not settings.admin_key or x_admin_key != settings.admin_key:
        raise HTTPException(401, "invalid admin key")


def _bad(e: Exception):
    raise HTTPException(422, str(e))


LANG = "^(en|te|hi|mr)$"

# ---------------------------------------------------------------- public-ish

@app.get("/health")
def health():
    return {"ok": True, "engine_version": ENGINE_VERSION, "review_mode": not settings.auto_approve}


@app.get("/v1/events", dependencies=[Depends(app_auth)])
def events(lang: str = Q("en", pattern=LANG)):
    return {"events": service.event_catalogue(lang)}


@app.get("/v1/panchang", dependencies=[Depends(app_auth)])
def panchang(date: str, city: str | None = None, lat: float | None = None, lon: float | None = None,
             lang: str = Q("en", pattern=LANG)):
    venue = {"name": city, "lat": lat, "lon": lon} if lat is not None else (city or settings.default_city)
    try:
        return service.panchang(date, venue, lang)
    except service.InputError as e:
        _bad(e)


# ---------------------------------------------------------------- direct engine (structured forms)

class PersonIn(BaseModel):
    role: str = Field(..., description="kartha | bride | groom | child | father | wife | husband")
    name: str = ""
    dob: str | None = None
    tob: str | None = None
    birthplace: str | None = None
    nakshatra: str | None = None
    rashi: str | None = None
    pada: int | None = None
    gender: str | None = None


class SearchIn(BaseModel):
    event: str
    from_date: str
    to_date: str
    venue: str | dict
    persons: list[PersonIn] = []
    time_pref: str = "any"
    weekdays: list[str] | None = None
    avoid_dates: list[str] | None = None
    direction: str | None = None
    tradition: str | None = None
    options: int = 3
    lang: str = Field("en", pattern=LANG)
    submit_for_review: bool = Field(False, description="Create a pandit-review request from the result")
    customer_ref: str | None = None


@app.post("/v1/muhurtha/search", dependencies=[Depends(app_auth)])
def muhurtha_search(body: SearchIn):
    try:
        res = service.find_muhurtham(
            event=body.event, from_date=body.from_date, to_date=body.to_date, venue=body.venue,
            persons=[p.model_dump(exclude_none=True) for p in body.persons], time_pref=body.time_pref,
            weekdays=body.weekdays, avoid_dates=body.avoid_dates, direction=body.direction,
            tradition=body.tradition, options=body.options, lang=body.lang,
            max_window_days=settings.max_window_days)
    except service.InputError as e:
        _bad(e)
    if not body.submit_for_review:
        return res
    if not res["options"]:
        return {**res, "request_id": None, "status": "NO_OPTIONS"}
    pseudo = {"id": None, "customer_ref": body.customer_ref}
    draft = {"option_ids": [o["option_id"] for o in res["options"]], "explanations": {},
             "message_to_family": "", "note_for_pandit": "Submitted from structured form (no Acharya chat)."}
    req = store.create_request(pseudo, res["event"]["code"], body.lang, res, draft,
                               {"people": [p.model_dump(exclude_none=True) for p in body.persons],
                                "search_args": body.model_dump(exclude={"persons"})})
    if settings.auto_approve:
        req = review.approve(req["id"], "auto")
    return {"request_id": req["id"], "status": req["status"]}


# ---------------------------------------------------------------- Acharya conversation

class StartIn(BaseModel):
    lang: str = Field("en", pattern=LANG)
    customer_ref: str | None = Field(None, description="Your booking / order id (after Rs 199 payment)")
    city: str | None = None
    customer_first_name: str | None = None
    event_hint: str | None = Field(None, description="If the user tapped a specific event in the app")


class MessageIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


def _public_session(s: dict) -> dict:
    return {"session_id": s["id"], "state": s["state"], "lang": s["lang"], "request_id": s.get("request_id")}


@app.post("/v1/acharya/sessions", dependencies=[Depends(app_auth)])
def start_session(body: StartIn):
    store.purge_expired()
    s = store.create_session(body.lang, body.customer_ref,
                             {"city": body.city or settings.default_city, "first_name": body.customer_first_name})
    opener = f"(App context: the customer {body.customer_first_name or ''} opened the Muhurtham service"
    opener += f" for: {body.event_hint}." if body.event_hint else "."
    opener += " Greet them and ask what occasion they need a muhurtham for.)"
    try:
        out = agent.respond(s, opener)
    except Exception as e:
        store.delete_session(s["id"])
        raise HTTPException(503, f"Acharya unavailable: {e}")
    store.save_session(s)
    return {**_public_session(s), **out}


@app.post("/v1/acharya/sessions/{sid}/messages", dependencies=[Depends(app_auth)])
def send_message(sid: str, body: MessageIn):
    s = store.get_session(sid)
    if not s:
        raise HTTPException(404, "session not found or already completed")
    try:
        out = agent.respond(s, body.text)
    except Exception as e:
        raise HTTPException(503, f"Acharya unavailable: {e}")
    store.save_session(s)
    return {**_public_session(s), **out}


@app.get("/v1/acharya/sessions/{sid}", dependencies=[Depends(app_auth)])
def get_session(sid: str):
    s = store.get_session(sid)
    if not s:
        raise HTTPException(404, "session not found")
    msgs = [{"role": m["role"], "text": m["content"] if isinstance(m["content"], str)
             else " ".join(b.get("text", "") for b in m["content"] if b.get("type") == "text")}
            for m in s["messages"]]
    msgs = [m for m in msgs[1:] if m["text"].strip()]  # hide the app opener
    return {**_public_session(s), "messages": msgs}


@app.delete("/v1/acharya/sessions/{sid}", dependencies=[Depends(app_auth)])
def cancel_session(sid: str):
    s = store.get_session(sid)
    if s and s.get("request_id"):
        r = store.get_request(s["request_id"])
        if r and r["status"] == "PENDING_REVIEW":
            store.update_request(r["id"], status="CANCELLED")
            store.purge_personal_data(r["id"])
    store.delete_session(sid)
    return {"deleted": True}


# ---------------------------------------------------------------- results for the app

STATUS_FOR_APP = {  # maps to the existing Kaamya Muhurth statuses
    "PENDING_REVIEW": "Pandit Calculating", "APPROVED": "Muhurth Ready", "DELIVERED": "Muhurth Ready",
    "NEEDS_MANUAL": "Awaiting Pandit", "CANCELLED": "Cancelled", "CLOSED": "Cancelled",
}


@app.get("/v1/requests/{rid}", dependencies=[Depends(app_auth)])
def get_request(rid: str):
    r = store.get_request(rid)
    if not r:
        raise HTTPException(404, "not found")
    out = {"request_id": r["id"], "status": r["status"], "app_status": STATUS_FOR_APP.get(r["status"]),
           "customer_ref": r.get("customer_ref"), "event": r["event"], "lang": r["lang"]}
    if r["status"] in ("APPROVED", "DELIVERED"):
        out["result"] = r["final"]
        if r["status"] == "APPROVED":
            store.update_request(rid, status="DELIVERED", delivered_at=store.now())
            out["status"] = "DELIVERED"
    return out


# ---------------------------------------------------------------- pandit review (admin console)

class ApproveIn(BaseModel):
    reviewer: str
    option_ids: list[str] | None = None
    explanation_edits: dict[str, str] | None = None
    option_notes: dict[str, str] | None = None
    note: str | None = None


class CustomOption(BaseModel):
    start: str = Field(..., description="YYYY-MM-DDTHH:MM local time at venue")
    end: str
    explanation: str = ""
    pandit_note: str = ""


class ReplaceIn(BaseModel):
    reviewer: str
    options: list[CustomOption] = Field(..., min_length=1, max_length=3)
    note: str | None = None


class RejectIn(BaseModel):
    reviewer: str
    reason: str


class CheckIn(BaseModel):
    venue: str | dict
    start: str
    end: str
    lang: str = Field("en", pattern=LANG)


@app.get("/v1/review/requests", dependencies=[Depends(admin_auth)])
def review_queue(status: str = "PENDING_REVIEW", limit: int = 50):
    return {"requests": [{"request_id": r["id"], "created": r["created"], "event": r["event"], "lang": r["lang"],
                          "customer_ref": r.get("customer_ref"), "status": r["status"],
                          "options": len((r.get("engine") or {}).get("options", []))}
                         for r in store.list_requests(status, limit)]}


@app.get("/v1/review/requests/{rid}", dependencies=[Depends(admin_auth)])
def review_detail(rid: str):
    r = store.get_request(rid)
    if not r:
        raise HTTPException(404, "not found")
    return r  # full engine output, AI draft, and the birth details the pandit needs to verify


@app.post("/v1/review/requests/{rid}/approve", dependencies=[Depends(admin_auth)])
def review_approve(rid: str, body: ApproveIn):
    try:
        r = review.approve(rid, body.reviewer, body.option_ids, body.explanation_edits, body.option_notes, body.note)
    except service.InputError as e:
        _bad(e)
    return {"request_id": rid, "status": r["status"], "result": r["final"]}


@app.post("/v1/review/requests/{rid}/replace", dependencies=[Depends(admin_auth)])
def review_replace(rid: str, body: ReplaceIn):
    try:
        r = review.replace(rid, body.reviewer, [o.model_dump() for o in body.options], body.note)
    except service.InputError as e:
        _bad(e)
    return {"request_id": rid, "status": r["status"], "result": r["final"]}


@app.post("/v1/review/requests/{rid}/reject", dependencies=[Depends(admin_auth)])
def review_reject(rid: str, body: RejectIn):
    try:
        r = review.reject(rid, body.reviewer, body.reason)
    except service.InputError as e:
        _bad(e)
    return {"request_id": rid, "status": r["status"]}


@app.post("/v1/review/requests/{rid}/close", dependencies=[Depends(admin_auth)])
def review_close(rid: str):
    return {"request_id": rid, "status": review.close_manual(rid)["status"]}


@app.post("/v1/review/check-time", dependencies=[Depends(admin_auth)])
def review_check_time(body: CheckIn):
    try:
        return review.check_custom_time(body.venue, body.start, body.end, body.lang)
    except service.InputError as e:
        _bad(e)


@app.get("/v1/review/accuracy", dependencies=[Depends(admin_auth)])
def accuracy():
    return {"by_event": store.accuracy_stats()}


# ---------------------------------------------------------------- internal demo screen

import os as _os
from pathlib import Path as _Path

from fastapi.responses import HTMLResponse as _HTML


@app.get("/demo", include_in_schema=False)
def demo():
    if _os.getenv("KAAMYA_ENABLE_DEMO", "false").lower() not in ("1", "true", "yes"):
        raise HTTPException(404)
    return _HTML((_Path(__file__).parent / "static" / "demo.html").read_text(encoding="utf-8"))
