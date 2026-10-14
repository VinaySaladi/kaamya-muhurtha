"""
Persistence with privacy built in. SQLite by default; Postgres (e.g. Supabase) when
KAAMYA_DATABASE_URL is set, so data survives restarts on hosts without a disk.

* Birth details and the full conversation live ONLY in `sessions` and are deleted
  the moment the muhurtham is delivered (or when an abandoned session expires).
* `requests` keeps what the pandit and the app need, and after delivery only the
  final, approved options (no date / time / place of birth).
* `audit` keeps anonymous numbers for accuracy tracking (event, scores, whether the
  pandit accepted the engine's options) - nothing that identifies a person.

On Postgres the tables live in their own schema (`muhurtha`), which Supabase does not
expose through its public REST API.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone

from .config import settings

log = logging.getLogger("kaamya.store")

_lock = threading.RLock()
_conn = None
PG = bool(settings.database_url)

# Table names (schema-qualified on Postgres)
SESSIONS, REQUESTS, AUDIT = (("muhurtha.sessions", "muhurtha.requests", "muhurtha.audit") if PG
                             else ("sessions", "requests", "audit"))

SCHEMA_SQLITE = """
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

SCHEMA_PG = """
CREATE SCHEMA IF NOT EXISTS muhurtha;
CREATE TABLE IF NOT EXISTS muhurtha.sessions (
  id TEXT PRIMARY KEY, created TEXT, updated TEXT, lang TEXT, state TEXT,
  customer_ref TEXT, messages TEXT, data TEXT, request_id TEXT
);
CREATE TABLE IF NOT EXISTS muhurtha.requests (
  id TEXT PRIMARY KEY, session_id TEXT, customer_ref TEXT, created TEXT, updated TEXT,
  status TEXT, event TEXT, lang TEXT, engine TEXT, draft TEXT, review_input TEXT,
  final TEXT, reviewer TEXT, note TEXT, delivered_at TEXT, purged INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS muhurtha.audit (
  id BIGSERIAL PRIMARY KEY, ts TEXT, request_id TEXT, event TEXT,
  outcome TEXT, engine_version TEXT, top_score DOUBLE PRECISION, options INTEGER, pandit_changed INTEGER
);
CREATE INDEX IF NOT EXISTS idx_muhurtha_requests_status ON muhurtha.requests (status, created);
CREATE INDEX IF NOT EXISTS idx_muhurtha_sessions_updated ON muhurtha.sessions (updated);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def conn():
    global _conn
    with _lock:
        if _conn is None:
            if PG:
                import psycopg
                from psycopg.rows import dict_row
                # autocommit: every statement is its own transaction (same behaviour as the SQLite commits).
                # prepare_threshold=None keeps it working behind PgBouncer/Supavisor transaction pooling.
                _conn = psycopg.connect(settings.database_url, autocommit=True, row_factory=dict_row,
                                        prepare_threshold=None, connect_timeout=10)
                for stmt in filter(str.strip, SCHEMA_PG.split(";")):
                    _conn.execute(stmt)
            else:
                _conn = sqlite3.connect(settings.db_path, check_same_thread=False)
                _conn.row_factory = sqlite3.Row
                _conn.executescript(SCHEMA_SQLITE)
        return _conn


def _reset() -> None:
    global _conn
    try:
        if _conn is not None:
            _conn.close()
    except Exception:
        pass
    _conn = None


def _exec(sql: str, params: tuple = (), fetch: str | None = None):
    """Runs one statement. fetch: None (returns rowcount), 'one' or 'all' (returns dict rows)."""
    if PG:
        sql = sql.replace("?", "%s")
    with _lock:
        for attempt in (1, 2):
            try:
                cur = conn().execute(sql, params)
                if fetch == "one":
                    r = cur.fetchone()
                    out = dict(r) if r is not None else None
                elif fetch == "all":
                    out = [dict(r) for r in cur.fetchall()]
                else:
                    out = cur.rowcount
                if not PG:
                    conn().commit()
                return out
            except Exception as e:
                # Pooled Postgres connections get dropped when idle: reconnect once
                if PG and attempt == 1 and _is_connection_error(e):
                    log.warning("database connection lost, reconnecting: %s", e)
                    _reset()
                    continue
                raise


def _is_connection_error(e: Exception) -> bool:
    try:
        import psycopg
    except ImportError:
        return False
    return isinstance(e, (psycopg.OperationalError, psycopg.InterfaceError))


def _row(r: dict | None) -> dict | None:
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
    _exec(f"INSERT INTO {SESSIONS} (id, created, updated, lang, state, customer_ref, messages, data, request_id)"
          " VALUES (?,?,?,?,?,?,?,?,?)",
          (sid, now(), now(), lang, "COLLECTING", customer_ref, "[]", json.dumps(data), None))
    return get_session(sid)


def get_session(sid: str) -> dict | None:
    return _row(_exec(f"SELECT * FROM {SESSIONS} WHERE id=?", (sid,), "one"))


def save_session(s: dict) -> None:
    _exec(f"UPDATE {SESSIONS} SET updated=?, lang=?, state=?, messages=?, data=?, request_id=? WHERE id=?",
          (now(), s["lang"], s["state"], json.dumps(s["messages"], ensure_ascii=False),
           json.dumps(s["data"], ensure_ascii=False), s.get("request_id"), s["id"]))


def delete_session(sid: str) -> None:
    _exec(f"DELETE FROM {SESSIONS} WHERE id=?", (sid,))


# ---------------------------------------------------------------- requests

def create_request(session: dict | None, event: str, lang: str, engine: dict, draft: dict,
                   review_input: dict, status: str = "PENDING_REVIEW") -> dict:
    rid = "mhr_" + uuid.uuid4().hex[:20]
    _exec(f"INSERT INTO {REQUESTS} (id, session_id, customer_ref, created, updated, status, event, lang, engine, draft,"
          " review_input) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
          (rid, session["id"] if session else None, session.get("customer_ref") if session else None,
           now(), now(), status, event, lang, json.dumps(engine, ensure_ascii=False),
           json.dumps(draft, ensure_ascii=False), json.dumps(review_input, ensure_ascii=False)))
    return get_request(rid)


def get_request(rid: str) -> dict | None:
    return _row(_exec(f"SELECT * FROM {REQUESTS} WHERE id=?", (rid,), "one"))


def list_requests(status: str | None = None, limit: int = 50) -> list[dict]:
    if status:
        rows = _exec(f"SELECT * FROM {REQUESTS} WHERE status=? ORDER BY created LIMIT ?", (status, limit), "all")
    else:
        rows = _exec(f"SELECT * FROM {REQUESTS} ORDER BY created DESC LIMIT ?", (limit,), "all")
    return [_row(r) for r in rows]


def update_request(rid: str, **fields) -> dict:
    sets, vals = [], []
    for k, v in fields.items():
        sets.append(f"{k}=?")
        vals.append(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
    sets.append("updated=?")
    vals.append(now())
    _exec(f"UPDATE {REQUESTS} SET {', '.join(sets)} WHERE id=?", (*vals, rid))
    return get_request(rid)


def audit(rid: str, event: str, outcome: str, engine: dict, pandit_changed: bool) -> None:
    opts = engine.get("options", []) if engine else []
    _exec(f"INSERT INTO {AUDIT} (ts, request_id, event, outcome, engine_version, top_score, options, pandit_changed)"
          " VALUES (?,?,?,?,?,?,?,?)",
          (now(), rid, event, outcome, engine.get("engine_version") if engine else None,
           max((o["score"] for o in opts), default=None), len(opts), int(pandit_changed)))


def accuracy_stats() -> dict:
    rows = _exec(f"SELECT event, outcome, pandit_changed, COUNT(*) AS n FROM {AUDIT}"
                 " GROUP BY event, outcome, pandit_changed", (), "all")
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
            _exec(f"DELETE FROM {SESSIONS} WHERE id=?", (r["session_id"],))
        engine = r.get("engine") or {}
        engine.pop("people", None)
        _exec(f"UPDATE {REQUESTS} SET review_input=NULL, draft=NULL, engine=?, purged=1, updated=? WHERE id=?",
              (json.dumps({"engine_version": engine.get("engine_version"),
                           "event": engine.get("event"),
                           "window": engine.get("window")}), now(), rid))


def purge_expired() -> int:
    cut_s = (datetime.now(timezone.utc) - timedelta(hours=settings.session_ttl_hours)).isoformat()
    cut_r = (datetime.now(timezone.utc) - timedelta(days=settings.result_ttl_days)).isoformat()
    with _lock:
        n = _exec(f"DELETE FROM {SESSIONS} WHERE updated < ? AND (request_id IS NULL)", (cut_s,))
        _exec(f"DELETE FROM {REQUESTS} WHERE delivered_at IS NOT NULL AND delivered_at < ?", (cut_r,))
    return n
