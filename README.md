# Through Line

**From mission to evidence to story.** Through Line helps small, low-resourced nonprofits prove the change they create, with a team of AI agents doing the heavy lifting and people approving everything that matters.

Built for AI Foundations at Yale. **All data in this repo is synthetic:** fictional organizations, fictional participants.

| Tab | What it does |
|---|---|
| **Logic Model** | A five-agent team (Team Lead, Sector Expert, Client Advocate, Evaluation Specialist, and Funder Researcher with live web search) reads your materials, asks five questions, and drafts a logic model and measurement plan that you edit and approve. Downloads as PowerPoint. |
| **Survey Tools** | Pre/post surveys built from your approved metrics, a Survey Review Bot with one-click fixes, participant codes + PINs, a phone-friendly participant portal, staff bulk entry, and monthly program numbers (one at a time or via an Excel template). |
| **Dashboard** | % improved, before/after, who you serve (as percentages, with small groups hidden), and program activity. Every chart downloads as Excel, plus all data and a quick PowerPoint report. |
| **Impact Report** | Describe your brand and pick your results. The Report Designer builds a 10–15 minute funder deck with speaker notes and a one-page PDF flyer. Its numbers refresh from your latest data, for free. |
| **Grants** | Name a foundation, share its website and RFP, and paste its questions. The team researches what the foundation cares about and drafts a tailored application (Word) from your live data. |

Safety is built in:
- Agents read only text a person can see in a document.
- A Privacy Reviewer checks everything that leaves the organization.
- Passwords and PINs are hashed with Argon2id, and usernames are stored only as keyed hashes.
- Each organization's data is isolated from every other's.
- Every agent run is written to an append-only, hash-chained audit log.
- Every run's tokens are recorded per person, and each tool has a usage allowance.

**How the agents work** (prompts, tools, limits, guardrails, audit, test evidence): see [`output/harness.md`](output/harness.md). **How it was built**, prompt by prompt: [`AI_prompts.md`](AI_prompts.md).

---

## Run it on your computer

You need Python 3.13, Node 22+, and a [Portkey](https://portkey.ai) API key that can reach OpenAI's `gpt-6-luna`.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt      # macOS/Linux: .venv/bin/python
cd frontend && npm install && cd ..
cp .env.example .env                                          # then put your key in PORTKEY_API_KEY
```

Start the API and the website in two terminals:

```bash
cd backend && ../.venv/Scripts/python -m uvicorn main:app --reload --reload-dir . --port 8000
cd frontend && npm run dev
```

Open http://localhost:5173, choose **Create a staff account**, and start in the Logic Model tab. Your data is saved in `data/through_line.db` (git-ignored).

**Try it without an API key** (scripted agents, throwaway data):

```bash
.venv/Scripts/python tests/demo_server.py
```

**Tests** (offline; no AI calls):

```bash
env -u PORTKEY_API_KEY .venv/Scripts/python -m pytest tests
```

**A full fictional organization:** `scripts/run_test_profile.py data/test_profiles/keystone_family_housing` plays Keystone Family Housing Partners through the whole app (see that folder's README). With a real key it makes live AI calls.

---

## Put it on the web (Render)

The repo includes a `Dockerfile` (one container serves the website and the API) and a `render.yaml` blueprint:
- a **Starter** web service;
- a **1 GB persistent disk** at `/var/data` for the database, sessions, logos, and audit log.

1. On [render.com](https://render.com), choose **New → Blueprint** and pick this repository.
2. When asked, enter:
   - `PORTKEY_API_KEY`: your Portkey key.
   - `THROUGH_LINE_SIGNUP_CODE`: an access code you choose. New organizations need it to sign up; colleagues join with invite codes from their admin.
3. Click **Apply**. The first build takes a few minutes. Your site is at `https://through-line-XXXX.onrender.com`.

To share it, send someone the link and the access code. They create an account and invite their own colleagues from the top bar.

### For the operator

On Render, open the service's **Shell** tab:

```bash
python ../scripts/operator_tools.py usage                  # tokens by organization and person
python ../scripts/operator_tools.py orgs                   # allowances used
python ../scripts/operator_tools.py allow <org id> grants  # give an organization one more
```

Limits per organization live in `backend/allowances.py`.

**Load the Keystone example** (a fictional housing nonprofit with a full set of results, no AI calls). In the Shell:

```bash
python ../scripts/operator_tools.py import-org ../scripts/demo/keystone_family_housing.json --username keystone.demo --name "Keystone demo"
```

It asks you to choose a password, then you can sign in as `keystone.demo`. Run it once (a second run says the username is taken).

---

## Project layout

```
backend/     FastAPI app, agents (agents/), prompts (prompts/), routes (routes/)
frontend/    Vite + React + TypeScript
tests/       offline tests and the scripted demo server
scripts/     test-profile runner, demo-deck builder, operator tools
data/        fictional test organizations and the Keystone test profile
output/      harness.md (the agents, documented) and audit_log.json
docs/        walkthrough deck from the live end-to-end test
```

Every agent uses `gpt-6-luna` through Portkey (OpenAI Responses API) with Pydantic AI.
