"""End-to-end API flow with a scripted stand-in for the language model (no API key needed)."""
import json
import os
import tempfile
from datetime import date, timedelta

os.environ["KAAMYA_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ["KAAMYA_API_KEY"] = "app-key"
os.environ["KAAMYA_ADMIN_KEY"] = "admin-key"
os.environ["ANTHROPIC_API_KEY"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from app.acharya import agent  # noqa: E402

APP = {"X-API-Key": "app-key"}
ADMIN = {"X-Admin-Key": "admin-key"}
START = date.today() + timedelta(days=20)


class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def model_dump(self, exclude_none=True):
        return dict(self.__dict__)


class _Resp:
    def __init__(self, blocks, stop):
        self.content = blocks
        self.stop_reason = stop
        self.usage = _Block(input_tokens=100, output_tokens=50)


def text(t):
    return _Resp([_Block(type="text", text=t)], "end_turn")


def tool(name, inp, i):
    return _Resp([_Block(type="tool_use", id=f"tu_{i}", name=name, input=inp)], "tool_use")


class FakeClient:
    """Plays the Acharya: decides the next step from the conversation so far."""

    def __init__(self):
        self.messages = self
        self.n = 0
        self.leak_once = False

    def create(self, **kw):
        self.n += 1
        msgs = kw["messages"]
        last = msgs[-1]
        content = last["content"]
        if isinstance(content, list) and content and content[0].get("type") == "text":
            content = content[0]["text"]
        if isinstance(content, str):
            u = content
            if u.startswith("(App context"):
                return text("Namaskaram! I am Kaamya Acharya. For which occasion shall I find a muhurtham?")
            if "griha pravesh" in u.lower():
                return tool("get_event_requirements", {"event": "griha pravesh"}, self.n)
            if "born" in u.lower():
                return tool("compute_birth_star", {"role": "kartha", "name": "Ravi", "dob": "1990-06-15",
                                                   "tob": "07:30", "birthplace": "Hyderabad"}, self.n)
            if "leak test" in u.lower():
                self.leak_once = True
                return text("Your muhurtham is at 07:42 on that day!")  # unverified time -> must be caught
            return text("Thank you.")
        # last message is tool results
        res = json.loads(last["content"][0]["content"])
        if "requirements" in res:
            return text("Please share the owner's date, time and place of birth, and your preferred dates.")
        if "nakshatra" in res and "options" not in res and "request_id" not in res:
            return tool("find_muhurtham", {"event": "griha_pravesh", "from_date": START.isoformat(),
                                           "to_date": (START + timedelta(days=120)).isoformat(),
                                           "venue": "Hyderabad"}, self.n)
        if "options" in res:
            assert "start" not in res["options"][0], "dates must be hidden from the AI in review mode"
            ids = [o["option_id"] for o in res["options"]][:3]
            return tool("submit_for_review", {"option_ids": ids,
                                              "explanations": {i: "A steady, auspicious time." for i in ids},
                                              "note_for_pandit": "Check Kartika option."}, self.n)
        if "request_id" in res:
            return text("Our senior pandit is verifying the muhurthams; you will receive them soon.")
        return text("ok")


def test_full_flow(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(agent, "_client", fake)
    c = TestClient(main.app)

    assert c.get("/v1/events", headers={"X-API-Key": "wrong"}).status_code == 401
    assert len(c.get("/v1/events", headers=APP).json()["events"]) >= 18
    p = c.get("/v1/panchang", params={"date": START.isoformat(), "city": "Mumbai", "lang": "mr"}, headers=APP).json()
    assert p["place"]["name"] == "Mumbai" and p["tithi"]

    r = c.post("/v1/acharya/sessions", json={"lang": "en", "customer_ref": "BK-1001", "city": "Hyderabad"},
               headers=APP).json()
    sid = r["session_id"]
    assert "Namaskaram" in r["reply"]
    r = c.post(f"/v1/acharya/sessions/{sid}/messages", json={"text": "Need griha pravesh muhurtham"}, headers=APP).json()
    assert "birth" in r["reply"]
    r = c.post(f"/v1/acharya/sessions/{sid}/messages",
               json={"text": "Ravi, born 15 June 1990 7:30 am in Hyderabad, any date in next 4 months"},
               headers=APP).json()
    assert r["state"] == "SUBMITTED" and r["request_id"]
    rid = r["request_id"]

    # guardrail: an unverified time in a reply is replaced
    r2 = c.post(f"/v1/acharya/sessions/{sid}/messages", json={"text": "leak test"}, headers=APP).json()
    assert "07:42" not in r2["reply"]

    st = c.get(f"/v1/requests/{rid}", headers=APP).json()
    assert st["status"] == "PENDING_REVIEW" and st["app_status"] == "Pandit Calculating" and "result" not in st

    q = c.get("/v1/review/requests", headers=ADMIN).json()["requests"]
    assert any(x["request_id"] == rid for x in q)
    detail = c.get(f"/v1/review/requests/{rid}", headers=ADMIN).json()
    assert detail["review_input"]["people"][0]["dob"] == "1990-06-15"
    ids = detail["draft"]["option_ids"]

    ap = c.post(f"/v1/review/requests/{rid}/approve",
                json={"reviewer": "Pandit Sharma", "option_ids": ids[:2], "note": "Verified."}, headers=ADMIN).json()
    assert ap["status"] == "APPROVED" and len(ap["result"]["options"]) == 2

    # personal data purged at approval
    detail = c.get(f"/v1/review/requests/{rid}", headers=ADMIN).json()
    assert detail["review_input"] is None and detail["purged"] == 1
    assert "1990-06-15" not in json.dumps(detail)
    assert c.get(f"/v1/acharya/sessions/{sid}", headers=APP).status_code == 404

    res = c.get(f"/v1/requests/{rid}", headers=APP).json()
    assert res["status"] == "DELIVERED" and res["app_status"] == "Muhurth Ready"
    o = res["result"]["options"][0]
    assert o["explanation"] and o["start_time"] and o["panchang"]["nakshatra"]
    assert "1990" not in json.dumps(res)

    acc = c.get("/v1/review/accuracy", headers=ADMIN).json()["by_event"]
    assert acc["griha_pravesh"]["approved_changed"] == 1


def test_structured_search_and_replace():
    c = TestClient(main.app)
    body = {"event": "vehicle", "from_date": START.isoformat(), "to_date": (START + timedelta(days=45)).isoformat(),
            "venue": "Pune", "persons": [{"role": "kartha", "name": "A", "nakshatra": "Rohini"}],
            "lang": "mr", "submit_for_review": True, "customer_ref": "BK-2"}
    r = c.post("/v1/muhurtha/search", json=body, headers=APP).json()
    rid = r["request_id"]
    chk = c.post("/v1/review/check-time", json={"venue": "Pune", "start": f"{START}T10:00", "end": f"{START}T11:00"},
                 headers=ADMIN).json()
    assert "panchang" in chk
    rep = c.post(f"/v1/review/requests/{rid}/replace", headers=ADMIN, json={
        "reviewer": "Pandit Joshi", "options": [{"start": f"{START}T10:00", "end": f"{START}T11:00",
                                                 "explanation": "शुभ मुहूर्त"}]}).json()
    assert rep["status"] == "APPROVED" and rep["result"]["options"][0]["option_id"] == "pandit-1"
