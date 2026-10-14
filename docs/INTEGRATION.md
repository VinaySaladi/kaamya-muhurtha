# Kaamya Muhurtha API: integration guide (for Vinay)

This service is a separate backend that the **Kaamya backend** calls server to server. The app (web or mobile) never talks to it directly and never holds its keys. To the customer it is simply the Muhurtham screen inside Kaamya, with "Kaamya Acharya" as the guide.

```
Kaamya app  ──▶  Kaamya backend  ──X-API-Key──▶  Muhurtha API  ──▶  Claude API (conversation only)
Admin console ─────────────────────X-Admin-Key──▶  Muhurtha API (pandit review)
Muhurtha API ──webhook──▶ Kaamya backend  (status changes)
```

Swagger docs are served at `/docs` once the service runs.

---

## 1. Where it fits in the current Muhurth flow

| Today (test app) | With the AI | Who acts |
|---|---|---|
| Customer pays Rs 199 → Muhurth request with birth details | Customer pays Rs 199 → **Acharya chat** opens, using the booking id as `customer_ref` | Customer |
| Status **Awaiting Pandit** | Chat in progress (state `COLLECTING`) | Customer + Acharya |
| **Pandit Calculating** | Request `PENDING_REVIEW`: the engine has computed and the AI has drafted | Senior pandit reviews in admin console |
| **Muhurth Ready** + "Book Pooja on this date" | `APPROVED` / `DELIVERED`: show the result card | Customer |
| (pandit can't do it) | `NEEDS_MANUAL`: fall back to today's manual claim flow | Pandit desk |

`GET /v1/requests/{id}` returns `app_status` already mapped to your existing status names.

---

## 2. Keys and environment

Set the variables in `.env.example`. The two keys you need:

- `KAAMYA_API_KEY`: sent by the Kaamya backend as header `X-API-Key`
- `KAAMYA_ADMIN_KEY`: sent by the admin console (pandit review) as `X-Admin-Key`

---

## 3. Customer chat (the main flow)

### Start (after payment)
`POST /v1/acharya/sessions`
```json
{ "lang": "te", "customer_ref": "BK-10234", "city": "Hyderabad",
  "customer_first_name": "Ravi", "event_hint": "griha_pravesh" }
```
`lang` is one of `en`, `te`, `hi`, `mr`. `event_hint` is optional (if the user tapped an event tile).

Response:
```json
{ "session_id": "ses_...", "state": "COLLECTING", "lang": "te", "request_id": null,
  "reply": "నమస్కారం! ...", "ui_fields": [], "usage": {...} }
```

### Each customer message
`POST /v1/acharya/sessions/{session_id}/messages` with `{ "text": "..." }`, which returns the same shape.

- Show `reply` as the Acharya's chat bubble.
- `ui_fields`: when present, show pickers above the keyboard so input feels native:
  `[{ "key":"bride.dob", "type":"date", "label":"Bride's date of birth" }, { "key":"window", "type":"date_range", ... }]`
  Types: `date`, `time`, `date_range`, `place`, `choice` (with `choices`), `text`.
  When the user picks a value, send it as a normal message (e.g. `"Bride's date of birth: 1998-03-14"`).
- When `request_id` becomes non-null and `state` = `SUBMITTED`, save `request_id` on your Muhurth booking and show
  "Our senior pandit is verifying your muhurthams" (the Acharya says this too).

A session can be resumed with `GET /v1/acharya/sessions/{id}` (returns the visible message history). `DELETE` cancels it and erases its data.

### Typical latency
1–6 s per message (most of it is the AI). A wedding search over 6 months takes 3–5 s of engine time. Show a typing indicator.

---

## 4. Getting the result

Either:
- **Webhook** (recommended): set `KAAMYA_WEBHOOK_URL`. On every status change we POST
  `{ "type":"muhurtha.status", "request_id":"mhr_...", "status":"APPROVED", "customer_ref":"BK-10234" }`
  with header `X-Kaamya-Signature` = HMAC-SHA256(body, `KAAMYA_WEBHOOK_SECRET`). Then call `GET /v1/requests/{id}`.
- **Polling**: `GET /v1/requests/{id}` every few minutes while the booking is in Pandit Calculating.

`GET /v1/requests/{id}` once approved:
```json
{
  "request_id": "mhr_...", "status": "DELIVERED", "app_status": "Muhurth Ready", "customer_ref": "BK-10234",
  "result": {
    "event": {"code": "griha_pravesh", "name": "Griha Pravesh (House warming)"},
    "lang": "te", "verified_by": "Pandit Sharma", "verified_at": "2026-11-02T10:12:00+00:00",
    "options": [
      {
        "option_id": "opt-2027-02-19-0640",
        "date": "2027-02-19", "weekday": "శుక్రవారం", "hindu_vara": "శుక్రవారం",
        "start": "2027-02-19 06:40", "end": "2027-02-19 08:02",
        "start_time": "06:40 AM", "end_time": "08:02 AM", "duration_minutes": 82,
        "quality": "shubha", "score": 79.0,
        "panchang": { "samvatsara": "Parabhava", "masa": "మాఘం", "paksha": "శుక్ల పక్షం", "tithi": "త్రయోదశి",
                      "nakshatra": "పుష్యమి", "yoga": "...", "karana": "...", "lagna": "కుంభం",
                      "lagna_type": "Sthira (fixed)", "sunrise": "06:39", "sunset": "18:18", "rahu_kalam": ["10:52","12:21"] },
        "explanation": "ఈ ముహూర్తం ... (Acharya's explanation, pandit-approved, in the customer's language)",
        "pandit_note": "",
        "why_good": ["Magha masa is favourable", "..."], "cautions": []
      }
    ],
    "message_to_family": "...", "pandit_note": "..."
  }
}
```
The first fetch after approval flips the status to `DELIVERED`.

**Result card UI:** one card per option showing weekday, date, start–end, quality badge (Uttama / Shubha / Madhyama), a panchang line (masa · paksha tithi · nakshatra · lagna), the explanation, "Verified by Kaamya pandit", and the existing **Book Pooja on this date** button (prefill date and time from `start`).

`why_good` and `cautions` are in English, for the admin console or an optional "details" drawer.

---

## 5. Pandit review (admin console)

| Action | Endpoint |
|---|---|
| Queue | `GET /v1/review/requests?status=PENDING_REVIEW` |
| Detail | `GET /v1/review/requests/{id}`: engine options with reasons, the AI's draft explanations, the AI's note for the pandit, and the birth details (`review_input.people`) |
| Approve | `POST /v1/review/requests/{id}/approve` `{ "reviewer":"Pandit Sharma", "option_ids":["opt-…","opt-…"], "explanation_edits": {"opt-…":"edited text"}, "option_notes": {"opt-…":"Start puja 15 min early"}, "note":"…" }` |
| Pandit gives own times | `POST /v1/review/requests/{id}/replace` `{ "reviewer":"…", "options":[{"start":"2027-02-19T06:45","end":"2027-02-19T07:30","explanation":"…"}] }`: the engine still checks them and attaches `engine_warnings` (e.g. "overlaps Rahu Kalam") |
| Check a time before replacing | `POST /v1/review/check-time` `{ "venue":"Hyderabad", "start":"…", "end":"…" }` |
| Send to manual flow | `POST /v1/review/requests/{id}/reject` `{ "reviewer":"…", "reason":"…" }` → `NEEDS_MANUAL` |
| Close a manual one | `POST /v1/review/requests/{id}/close` (erases birth details) |
| Accuracy so far | `GET /v1/review/accuracy`: per event, how often the pandit approved the engine's options unchanged |

Suggested admin screen: a list (oldest first) → a detail page with 2–3 option cards with checkboxes, editable explanation text boxes, an "Approve selected" button, and a "Replace with my own time" form. A working reference is the **Pandit review** tab of `/demo`.

---

## 6. Structured mode (no chat)

If you also want a plain form screen, call the engine directly:

`POST /v1/muhurtha/search`
```json
{ "event": "vehicle_purchase", "from_date": "2026-11-01", "to_date": "2026-12-15", "venue": "Mumbai",
  "persons": [ { "role":"kartha", "name":"Amit", "dob":"1991-02-10", "tob":"14:20", "birthplace":"Pune" } ],
  "time_pref": "morning", "lang": "mr", "submit_for_review": true, "customer_ref": "BK-2001" }
```
Without `submit_for_review` it just returns the options (useful for the admin or pandit tools).

Other read endpoints: `GET /v1/events?lang=te` (event list with required fields) and `GET /v1/panchang?date=2026-11-02&city=Hyderabad&lang=te` (daily panchang, which can also power a "Today's Panchangam" home widget).

**Roles** used in `persons`: `kartha` (owner / main person), `bride`, `groom`, `child`, `father`, `wife`, `husband`.
**Events:** see `GET /v1/events` or `docs/RULEBOOK.md` (20 events plus `general`).

---

## 7. Privacy (what you must also do on your side)

- This service deletes birth details and the chat **when the pandit approves** (or when an abandoned chat is 48 h old). It keeps only the final options (no date, time or place of birth) for 30 days, plus anonymous accuracy counts.
- Don't log the chat text or birth details in the Kaamya backend either. Store only `session_id`, `request_id` and the final result.
- Show a one-line notice in the chat screen: "Birth details are used only to fix your muhurtham and are deleted after delivery."

---

## 8. Deploy

- Docker: `docker build -t kaamya-muhurtha . && docker run -p 8080:8080 --env-file .env -v $(pwd)/data:/data kaamya-muhurtha`
- Render: `render.yaml` is included (Singapore region, 1 GB disk for the SQLite file).
- Health check: `GET /health`.
- Give it its own subdomain, e.g. `muhurtha-api.thevaidikgroup.com` (not a Netlify or Replit URL).
- SQLite suits the beta. Move to Postgres (Supabase/Neon) when you run more than one instance; only `app/store.py` changes.
