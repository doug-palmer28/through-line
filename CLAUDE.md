# Final Project Rules: Through Line (Nonprofit Impact Toolkit)

These override the parent `AGENTS.md` where they differ.

- **Model:** every agent uses `gpt-6-luna` via Portkey. Not Terra. No per-agent overrides.
- **Secrets:** `PORTKEY_API_KEY` comes from the environment / `.env` only. Never print, log, commit, or send it to the frontend.
- **Synthetic data only.** No real names or real participant information, ever.
- **No PII to the LLM.** Reflections pass through the Privacy Guard (fail closed) before any other agent sees them.
- **Humans approve** every AI output that leaves the app (logic models, metrics, scores, testimonials, reports).
- **Audit log** `output/audit_log.json` is append-only and hash-chained. Never edit or delete entries.
- **Harness** `output/harness.md` is about the agents (prompts, tools, models, loops, limits, guardrails, audit). Update it at the end of every step that changes them. The README (Step 19) is about installing and using the app.
- **Prompt log:** record Doug's prompts verbatim in `AI_prompts.md` under the matching step.
- **Scope (MVP):** one program per org; voice is a stretch goal; the Outcome Coder tags themes first and scores only where a rubric exists.
- **Design:** Bauhaus: clean, modern, lots of color.
- Build one step at a time, following `AI_prompts.md`.
- **Doug starts live agent runs.** Never trigger a gpt-6-luna run yourself, not even to check something. Test offline (`env -u PORTKEY_API_KEY .venv/Scripts/python -m pytest tests`) or click through with `tests/demo_server.py` (scripted agents, temp data).
- **Uploads are never saved to disk.** They're read in memory and dropped once read. `data/sessions/` holds what the client types, drafts, and approvals. Working notes (snapshot, sector brief) are kept there only while a session is active and are wiped at completion, end, or 7-day expiry.
- **Dev server reload** must stay limited to `backend/` (`--reload-dir`). Watching the whole folder lets OneDrive syncing `.venv` restart the server.
- **Accounts (Step 10):** staff sign in first; everything is saved per organization (`data/through_line.db`, git-ignored). Passwords/PINs are Argon2id, usernames only as HMAC hashes, sign-in is an HttpOnly SameSite=Strict JWT cookie. Every query filters on the signed-in `org_id`. Never log usernames, passwords, PINs, or invite codes.
- **Tests and demos use temp databases** (`THROUGH_LINE_DB`, `THROUGH_LINE_SECRET` env vars). Never point them at `data/through_line.db`.
- **Visible text only (Step 15b):** every document or web page an agent reads goes through `intake.py` → `visible.py`. Never add a reader that bypasses it.
- **Tokens and limits (Step 15b):** every agent call goes through `run_agent` (it records the token ledger). Set `org_id`, `actor_id`, and `feature` on shadow sessions. New AI features need an allowance in `allowances.py`; commit the allowance before the AI run and refund it on failure. Only the Privacy Reviewer is unlimited.
- **Numbers (Step 15b):** agents write numbers only as `{{key}}` tokens from `figures.catalog`; the app fills them at render time.
- **Funder materials (Step 15):** the Report Designer may use only the charts staff chose and quotes it was given word for word (`routes/reports.py::_validate`). Keep all three privacy layers: code scrub before the agent, the agent's privacy run, and the final code scan. Decks and flyers re-render from the stored draft, so design fixes never need a new AI call.
