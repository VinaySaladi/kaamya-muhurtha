"""
The Acharya conversation loop (Claude tool use).

The model talks to the family and calls deterministic tools for every fact.
Guardrails on top of the prompt:
  * in review mode, a reply that leaks an option's date/time before approval is regenerated;
  * any clock time in a reply must appear in a tool result of this session;
  * tool-use iterations are capped.
"""
from __future__ import annotations

import json
import logging
import re

import anthropic

from .. import store
from ..config import settings
from ..service import today_in
from .prompt import system_prompt
from .tools import TOOLS, run_tool, tool_result_text

log = logging.getLogger("kaamya.acharya")
MAX_STEPS = 10
_client: anthropic.Anthropic | None = None
_TIME = re.compile(r"\b(?:[01]?\d|2[0-3])[:.][0-5]\d\b")


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _tools_cached():
    tools = [dict(t) for t in TOOLS]
    tools[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}
    return tools


def _blocks_to_dicts(content) -> list[dict]:
    out = []
    for b in content:
        d = b.model_dump(exclude_none=True) if hasattr(b, "model_dump") else dict(b)
        # keep only fields the API accepts back
        if d.get("type") == "text":
            out.append({"type": "text", "text": d["text"]})
        elif d.get("type") == "tool_use":
            out.append({"type": "tool_use", "id": d["id"], "name": d["name"], "input": d["input"]})
    return out


def _seen_text(session: dict) -> str:
    """Everything tools returned this session (for checking times quoted by the model)."""
    parts = []
    for m in session["messages"]:
        if m["role"] == "user" and isinstance(m["content"], str):
            parts.append(m["content"])
        if m["role"] == "user" and isinstance(m["content"], list):
            for b in m["content"]:
                if b.get("type") == "tool_result":
                    parts.append(str(b.get("content")))
    return "\n".join(parts)


def _leaks(reply: str, session: dict) -> list[str]:
    problems = []
    seen = _seen_text(session)
    for m in _TIME.finditer(reply):
        t = m.group(0).replace(".", ":")
        if t not in seen and t.zfill(5) not in seen:
            problems.append(f"time {t} not from any tool")
    if not settings.auto_approve and session.get("state") == "SUBMITTED":
        req = store.get_request(session.get("request_id") or "")
        if req and req["status"] == "PENDING_REVIEW":
            for o in (req.get("engine") or {}).get("options", []):
                from datetime import date as _d
                dd = _d.fromisoformat(o["date"])
                mon = dd.strftime("%B")
                for token in (o["start"][-5:], o["start_time"], o["date"], f"{dd.day} {mon}",
                              f"{mon} {dd.day}", dd.strftime("%d/%m"), f"{dd.day}/{dd.month}"):
                    if token and token in reply:
                        problems.append("revealed an option before pandit approval")
                        break
    return problems


def _call(session: dict, extra_system: str = ""):
    data = session["data"]
    review_mode = not settings.auto_approve
    sys_text = system_prompt(session["lang"], today_in().isoformat(), data.get("city"), review_mode)
    system = [{"type": "text", "text": sys_text, "cache_control": {"type": "ephemeral"}}]
    if extra_system:
        system.append({"type": "text", "text": extra_system})
    # cache the conversation so far (incremental prompt caching keeps cost per turn low)
    msgs = [dict(m) for m in session["messages"]]
    last = msgs[-1]
    if isinstance(last["content"], str):
        last["content"] = [{"type": "text", "text": last["content"], "cache_control": {"type": "ephemeral"}}]
    else:
        blocks = [dict(b) for b in last["content"]]
        blocks[-1] = {**blocks[-1], "cache_control": {"type": "ephemeral"}}
        last["content"] = blocks
    return client().messages.create(
        model=settings.model, max_tokens=settings.max_tokens, system=system,
        tools=_tools_cached(), messages=msgs,
    )


def respond(session: dict, user_text: str) -> dict:
    """Append the family's message, run the tool loop, return the reply + UI hints."""
    session["messages"].append({"role": "user", "content": user_text})
    session["data"].pop("ui_fields", None)
    reply = ""
    for step in range(MAX_STEPS):
        resp = _call(session)
        blocks = _blocks_to_dicts(resp.content)
        session["messages"].append({"role": "assistant", "content": blocks})
        if resp.stop_reason == "tool_use":
            results = []
            for b in blocks:
                if b["type"] == "tool_use":
                    out = run_tool(b["name"], b["input"], session)
                    results.append({"type": "tool_result", "tool_use_id": b["id"],
                                    "content": tool_result_text(out),
                                    **({"is_error": True} if "error" in out else {})})
            session["messages"].append({"role": "user", "content": results})
            continue
        reply = "".join(b["text"] for b in blocks if b["type"] == "text").strip()
        break
    else:
        reply = ""

    problems = _leaks(reply, session) if reply else ["empty reply"]
    if problems:
        log.warning("guardrail: %s", problems)
        # one corrective regeneration
        session["messages"].pop()  # drop the bad assistant turn
        fix = ("Your previous draft reply had problems: " + "; ".join(problems) +
               ". Rewrite the reply to the family without any date or time that is not in a tool result"
               + ("" if settings.auto_approve else ", and without revealing option dates/times before pandit approval")
               + ".")
        resp = _call(session, extra_system=fix)
        blocks = [b for b in _blocks_to_dicts(resp.content) if b["type"] == "text"]
        reply = "".join(b["text"] for b in blocks).strip()
        if _leaks(reply, session):
            reply = _safe_fallback(session)
        session["messages"].append({"role": "assistant", "content": [{"type": "text", "text": reply}]})

    _trim(session)
    return {
        "reply": reply,
        "state": session["state"],
        "request_id": session.get("request_id"),
        "ui_fields": session["data"].get("ui_fields", []),
        "usage": {"input_tokens": getattr(resp.usage, "input_tokens", None),
                  "output_tokens": getattr(resp.usage, "output_tokens", None)},
    }


_FALLBACK = {
    "en": "Thank you. Our senior pandit is verifying the muhurthams now; you will receive them in the app shortly.",
    "te": "ధన్యవాదాలు. మా సీనియర్ పండితులు ముహూర్తాలను పరిశీలిస్తున్నారు; త్వరలో యాప్‌లో మీకు అందుతాయి.",
    "hi": "धन्यवाद। हमारे वरिष्ठ पंडित जी मुहूर्त की जाँच कर रहे हैं; शीघ्र ही आपको ऐप में मिल जाएँगे।",
    "mr": "धन्यवाद. आमचे ज्येष्ठ पंडित मुहूर्ताची पडताळणी करत आहेत; लवकरच ते आपल्याला ॲपमध्ये मिळतील.",
}


def _safe_fallback(session: dict) -> str:
    if session.get("state") == "SUBMITTED":
        return _FALLBACK.get(session["lang"], _FALLBACK["en"])
    return {"en": "Could you please tell me a little more?", "te": "దయచేసి కొంచెం వివరంగా చెప్పగలరా?",
            "hi": "कृपया थोड़ा और बताइए?", "mr": "कृपया थोडे अधिक सांगाल का?"}.get(session["lang"], "Please tell me more.")


def _trim(session: dict, keep: int = 60) -> None:
    """Keep the conversation bounded; large search results are summarised in older turns."""
    msgs = session["messages"]
    for m in msgs[:-6]:
        if m["role"] == "user" and isinstance(m["content"], list):
            for b in m["content"]:
                if b.get("type") == "tool_result" and len(str(b.get("content"))) > 4000:
                    try:
                        d = json.loads(b["content"])
                        d = {"options": d.get("options"), "event": d.get("event"), "note": "trimmed"}
                        b["content"] = json.dumps(d, ensure_ascii=False)[:6000]
                    except Exception:
                        b["content"] = str(b["content"])[:4000]
    if len(msgs) > keep:
        # drop oldest complete exchanges but keep the first user message
        cut = len(msgs) - keep
        while cut < len(msgs) and not (msgs[cut]["role"] == "user" and isinstance(msgs[cut]["content"], str)):
            cut += 1
        session["messages"] = msgs[:1] + msgs[cut:]
