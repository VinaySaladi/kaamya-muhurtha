"""
Persistence (SQLite by default) with privacy built in:

* Birth details and the full conversation live ONLY in `sessions` and are deleted
  the moment the muhurtham is delivered (or when an abandoned session expires).
* `requests` keeps what the pandit and the app need, and after delivery only the
  final, approved options (no date / time / place of birth).
* `audit` keeps anonymous numbers for accuracy tracking (event, scores, whether the
  pandit accepted the engine's options) - nothing that identifies a person.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone

from .config import settings

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, created TEXT, updated TEXT, lang TEXT, state TEXT,
  customer_ref TEXT, messages TEXT, data TEXT, request_id TEXT
);
CREATE TABLE IF NOT EXISTS requests (
  id TEXT PRIMARY KEY, session_id TEXT, customer_ref TEXT, created TEXT, updated TEXT,
  status TEXT, event TEXT, lang TEXT, engine TEXT, draft TEXT, review_input TEXT,
  final TEXT, reviewer TEXT, note TEXT, delivered_at TEXT, purged INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, request_id TEXT, event TEXT,
  outcome TEXT, engine_version TEXT, top_score REAL, options INTEGER, pandit_changed INTEGER
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(settings.db_path, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.executescript(SCHEMA)
        return _conn


def _row(r) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in ("messages", "data", "engine", "draft", "final", "review_input"):
        if k in d and d[k]:
            d[k] = json.loads(d[k])
    return d


# ---------------------------------------------------------------- sessions

def create_session(lang: str, customer_ref: str | None, data: dict) -> dict:
    sid = "ses_" + uuid.uuid4().hex[:20]
    with _lock:
        conn().execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)",
                       (sid, now(), now(), lang, "COLLECTING", customer_ref, "[]", json.dumps(data), None))
        conn().commit()
    return get_session(sid)


def get_session(sid: str) -> dict | None:
    with _lock:
        return _row(conn().execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone())


def save_session(s: dict) -> None:
    with _lock:
        conn().execute(
            "UPDATE sessions SET updated=?, lang=?, state=?, messages=?, data=?, request_id=? WHERE id=?",
            (now(), s["lang"], s["state"], json.dumps(s["messages"], ensure_ascii=False),
             json.dumps(s["data"], ensure_ascii=False), s.get("request_id"), s["id"]))
        conn().commit()


def delete_session(sid: str) -> None:
    with _lock:
        conn().execute("DELETE FROM sessions WHERE id=?", (sid,))
        conn().commit()


# ---------------------------------------------------------------- requests

def create_request(session: dict | None, event: str, lang: str, engine: dict, draft: dict,
                   review_input: dict, status: str = "PENDING_REVIEW") -> dict:
    rid = "mhr_" + uuid.uuid4().hex[:20]
    with _lock:
        conn().execute(
            "INSERT INTO requests (id, session_id, customer_ref, created, updated, status, event, lang, engine, draft, review_input)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (rid, session["id"] if session else None, session.get("customer_ref") if session else None,
             now(), now(), status, event, lang, json.dumps(engine, ensure_ascii=False),
             json.dumps(draft, ensure_ascii=False), json.dumps(review_input, ensure_ascii=False)))
        conn().commit()
    return get_request(rid)


def get_request(rid: str) -> dict | None:
    with _lock:
        return _row(conn().execute("SELECT * FROM requests WHERE id=?", (rid,)).fetchone())


def list_requests(status: str | None = None, limit: int = 50) -> list[dict]:
    with _lock:
        if status:
            rows = conn().execute("SELECT * FROM requests WHERE status=? ORDER BY created LIMIT ?", (status, limit))
        else:
            rows = conn().execute("SELECT * FROM requests ORDER BY created DESC LIMIT ?", (limit,))
        return [_row(r) for r in rows.fetchall()]


def update_request(rid: str, **fields) -> dict:
    sets, vals = [], []
    for k, v in fields.items():
        sets.append(f"{k}=?")
        vals.append(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
    sets.append("updated=?")
    vals.append(now())
    with _lock:
        conn().execute(f"UPDATE requests SET {', '.join(sets)} WHERE id=?", (*vals, rid))
        conn().commit()
    return get_request(rid)


def audit(rid: str, event: str, outcome: str, engine: dict, pandit_changed: bool) -> None:
    opts = engine.get("options", []) if engine else []
    with _lock:
        conn().execute(
            "INSERT INTO audit (ts, request_id, event, outcome, engine_version, top_score, options, pandit_changed)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (now(), rid, event, outcome, engine.get("engine_version") if engine else None,
             max((o["score"] for o in opts), default=None), len(opts), int(pandit_changed)))
        conn().commit()


def accuracy_stats() -> dict:
    with _lock:
        rows = conn().execute(
            "SELECT event, outcome, pandit_changed, COUNT(*) n FROM audit GROUP BY event, outcome, pandit_changed"
        ).fetchall()
    out: dict = {}
    for r in rows:
        e = out.setdefault(r["event"], {"approved_unchanged": 0, "approved_changed": 0, "rejected": 0})
        if r["outcome"] == "approved":
            e["approved_changed" if r["pandit_changed"] else "approved_unchanged"] += r["n"]
        else:
            e["rejected"] += r["n"]
    for e in out.values():
        total = sum(e.values())
        e["acceptance_rate"] = round(e["approved_unchanged"] / total, 3) if total else None
    return out


# ---------------------------------------------------------------- privacy

def purge_personal_data(rid: str) -> None:
    """Delete birth details + conversation for a delivered request."""
    r = get_request(rid)
    if not r:
        return
    with _lock:
        if r.get("session_id"):
            conn().execute("DELETE FROM sessions WHERE id=?", (r["session_id"],))
        engine = r.get("engine") or {}
        engine.pop("people", None)
        conn().execute("UPDATE requests SET review_input=NULL, draft=NULL, engine=?, purged=1, updated=? WHERE id=?",
                       (json.dumps({"engine_version": engine.get("engine_version"),
                                    "event": engine.get("event"),
                                    "window": engine.get("window")}), now(), rid))
        conn().commit()


def purge_expired() -> int:
    cut_s = (datetime.now(timezone.utc) - timedelta(hours=settings.session_ttl_hours)).isoformat()
    cut_r = (datetime.now(timezone.utc) - timedelta(days=settings.result_ttl_days)).isoformat()
    with _lock:
        n = conn().execute("DELETE FROM sessions WHERE updated < ? AND (request_id IS NULL)", (cut_s,)).rowcount
        conn().execute("DELETE FROM requests WHERE delivered_at IS NOT NULL AND delivered_at < ?", (cut_r,))
        conn().commit()
    return n
