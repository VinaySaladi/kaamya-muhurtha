# Setup: Claude API account, deployment and going live

## 1. Create the Claude API account (about 10 minutes)

This is separate from the Claude app subscription and is paid per use.

1. Go to **https://platform.claude.com** and sign up with the company email (e.g. `tech@thevaidikgroup.com`).
   Use **Vaidikya Technologies Private Limited** as the organisation name.
2. Add billing: open the Console's billing settings, add a card and buy prepaid credits. **USD 10–20 is plenty for the beta.**
   Turn off auto-reload at first so spending can't run away.
3. Set a monthly **spend limit** in the Console's limits settings (e.g. USD 25) as a safety cap.
4. Create the key: **Settings → API keys → Create key**. Name it `kaamya-muhurtha-prod`.
   For a production server, prefer a **service account** key so it isn't tied to one person.
   Copy it immediately (it starts with `sk-ant-` and is shown once) and put it **only** in the server's
   `ANTHROPIC_API_KEY` setting. Never put it in the app, the website code, WhatsApp or email.
5. Create a second key, `kaamya-muhurtha-dev`, for Vinay's local testing.

Docs: https://platform.claude.com/docs/en/get-api-key

## 2. What it costs

| Model (set `KAAMYA_MODEL`) | API price (per million tokens, input / output) | Approx. cost per completed muhurtham chat* |
|---|---|---|
| `claude-sonnet-5-5` (default) | $2 / $10 | about ₹5–15 |
| `claude-haiku-5-5` | $0.10 / $0.50 | under ₹1 |

\*Estimate for an 8–12 message chat with prompt caching on (already built in). The muhurtham calculation itself is
free (it runs on your own server). Recommended: start on Sonnet 5.5 for the best Telugu and Marathi, then test
Haiku 5.5 on 20 real chats. If the pandits are happy with its language, switch and cut AI cost by about 95%.
Prices from https://platform.claude.com/docs/en/about-claude/pricing; check there for current figures.

Hosting: a small server (Render "starter", Railway or similar) is about USD 7–10 a month.

## 3. Deploy (Vinay)

```bash
cp .env.example .env              # fill in the keys
pip install -r requirements-dev.txt
python -m pytest                  # 60 tests: panchang accuracy, rule invariants, full API flow
uvicorn app.main:app --port 8080  # http://localhost:8080/docs
```
Docker and `render.yaml` are included. Point a subdomain such as `muhurtha-api.thevaidikgroup.com` at it.

Quick trial: set `KAAMYA_ENABLE_DEMO=true` and open `/demo`. It has a customer chat tab and a pandit review tab.
Turn it off again in production.

## 4. Beta → full automation (option C)

1. **Now (beta):** `KAAMYA_AUTO_APPROVE=false`. Every muhurtham is drafted by the engine and AI and approved by a senior pandit.
2. **Measure:** `GET /v1/review/accuracy` shows, per event, how often the pandit approved the engine's options unchanged.
   Also run `python -m validation.validate your_pandit_cases.csv` on past muhurthams (template in `validation/`).
3. **Switch per event when ready:** when an event reaches ≥95% unchanged approvals over at least 50 cases, it can go
   automatic. (Today the switch is global. A per-event switch is a small change; ask when you need it.)
4. **Keep a human path:** even in automatic mode, keep the "talk to a pandit" button. It maps to `NEEDS_MANUAL`.

## 5. Before launch checklist

- [ ] Senior pandit reviews and signs off `docs/RULEBOOK.md` (mark changes; we update the rules)
- [ ] 20+ past muhurthams run through the validation harness, and disagreements discussed with the pandit
- [ ] Test chats in all four languages reviewed by a native speaker (Priyanka / pandits)
- [ ] Webhook connected; admin console review screen built
- [ ] Privacy line shown in the chat screen; privacy policy updated to mention birth details are deleted after delivery
- [ ] Spend limit set in the Claude Console
