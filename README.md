# Kaamya Muhurtha: engine + Kaamya Acharya

The muhurtham service for the **Kaamya** app (Vaidikya Technologies Pvt Ltd · The Vaidik Group).

A family chats with **Kaamya Acharya** in English, Telugu, Hindi or Marathi. The Acharya asks only what that event needs, a panchang engine calculates the muhurthams, and a senior pandit approves them before the family sees 2–3 verified options with explanations in their own language.

## Why it's accurate

| Layer | What it does | AI? |
|---|---|---|
| `app/astro/`: panchang engine | Sun, Moon and planets (Drik, Lahiri), tithi, nakshatra, yoga, karana, vara, amanta masa and adhika masa, samvatsara, lagna, sunrise/sunset, Rahu/Yama/Gulika, Durmuhurtham, Varjyam, Amrita, Abhijit, moudhyam, eclipses visible at the venue | No |
| `app/rules/`: muhurtha rules | 20 events plus a general one, with Telugu, Marathi and North profiles: tarabalam/chandrabalam (paksha rule), lagna shuddhi, months, Dhanurmasa, Chaturmasa, Pitru Paksha, Sarvartha Siddhi, swayam-siddha days, and more | No |
| `app/acharya/`: Kaamya Acharya | Talks like a senior pandit, collects details, calls the engine, writes explanations | Claude, with tool use |
| `app/review.py`: pandit review | Approve, edit, replace or reject before delivery | Human |

The AI never calculates. It can only pass on what the engine returned. In review mode it can't see option dates at all, so it can't reveal them early, and any clock time in a reply that no tool produced is caught and rewritten.

**Verified** against published Drik-method panchangams for Hyderabad: nakshatra, yoga, karana, varjyam and amrita times match to within 1 minute (see `tests/test_panchang.py`). Visible-eclipse dates for India also match.

## Quick start

```bash
pip install -r requirements-dev.txt
python -m pytest                       # 60 tests
cp .env.example .env                   # add ANTHROPIC_API_KEY and the two Kaamya keys
uvicorn app.main:app --port 8080       # API docs at /docs; set KAAMYA_ENABLE_DEMO=true for /demo
```

## Docs

- `docs/INTEGRATION.md`: endpoints, flows, the webhook and the app/admin screens (for Vinay)
- `docs/RULEBOOK.md`: every rule in plain words, for the senior pandit to sign off (regenerate with `python tools/gen_rulebook.py`)
- `docs/SETUP.md`: Claude API account, costs, deployment, the beta → automatic plan
- `validation/`: accuracy harness that compares the engine with your pandits' past muhurthams

## Privacy

Birth details and the chat are deleted when the pandit approves, or after 48 h if the chat is abandoned. Only the final options (no date, time or place of birth) and anonymous accuracy counts are kept.

## Licences

All dependencies are permissive (astronomy-engine MIT, FastAPI MIT, anthropic SDK MIT, timezonefinder MIT). No Swiss Ephemeris, so there is no AGPL obligation and no licence fee.
