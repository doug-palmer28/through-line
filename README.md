# Through Line

**Live app: [through-line.onrender.com](https://through-line.onrender.com)**

**From mission to evidence to story.** Through Line helps small, low-resourced nonprofits prove the change they create. A team of AI agents does the heavy lifting, and people approve everything that matters. Built by Doug Palmer for AI Foundations at the Yale School of Management. **All data in this repo is synthetic** (fictional organizations and participants), except the token counts and feedback from our outside tester.

## For graders: start here

| You want to… | Go to |
|---|---|
| **Try the live app** | [through-line.onrender.com](https://through-line.onrender.com). The sign-up **access code** and step-by-step instructions are on page 1 of the submitted report (`report.html`) and on the last slide (`slides.html`), along with a view-only login for a finished example. |
| **See what it produces** | [`examples/keystone/`](examples/keystone/): every file the app made for a fictional housing nonprofit (logic model, survey, dashboard data, funder deck, flyer, grant draft). PDF copies open in the browser. |
| **Check the evidence** | [`evidence/`](evidence/): test results, the hidden-text defense in action, the audit-log check, and the live site's token ledger, each tied to a claim in the report. |
| **Read how the agents work** | [`output/harness.md`](output/harness.md): every agent's prompt, tools, limits, guardrails, and audit trail. |
| **See how it was built** | [`AI_prompts.md`](AI_prompts.md): every prompt, verbatim and in order. |
| **Read the report or slides here** | Sources: [`docs/report/index.html`](docs/report/index.html) and [`docs/slides/index.html`](docs/slides/index.html) (reveal.js). |

## What it does

| Tab | What it does |
|---|---|
| **Logic Model** | A five-agent team (Team Lead, Sector Expert, Client Advocate, Evaluation Specialist, and a Funder Researcher with live web search) reads your materials, asks five questions, and drafts a logic model and measurement plan that you edit and approve. Downloads as PowerPoint. |
| **Survey Tools** | Pre/post surveys built from your approved metrics, a Survey Review Bot with one-click fixes, participant codes + PINs, a phone-friendly participant portal, staff bulk entry, and monthly program numbers (one at a time or from an Excel template). |
| **Dashboard** | % improved, before and after, who you serve (as percentages, with small groups hidden), and program activity. Every chart downloads as Excel, plus all data and a quick PowerPoint report. |
| **Impact Report** | Describe your brand and pick your results. The Report Designer builds a 10–15 minute funder deck with speaker notes and a one-page PDF flyer. Its numbers refresh from your latest data for free. |
| **Grants** | Name a foundation, share its website and RFP, and paste its questions. The team researches what the foundation cares about and drafts a tailored application (Word) from your live data. |

Every agent runs on `gpt-6-luna` through Portkey (OpenAI Responses API) with Pydantic AI. A typical organization costs cents per month in AI fees (see the report's Tokenomics section).

**Safety is built in:**
- Agents read only text a person can see in a document, so hidden instructions never reach them.
- A Privacy Reviewer checks everything that leaves the organization.
- Participants are codes and PINs, never names.
- Passwords and PINs are hashed with Argon2id. Usernames are stored only as keyed hashes.
- Each organization's data is isolated from every other's.
- Every agent run is written to an append-only, hash-chained audit log.
- Every run's tokens are recorded per person, and each tool has a usage allowance.

---

## Run it on your computer

You need Python 3.13, Node 22+, and a [Portkey](https://portkey.ai) API key that can reach OpenAI's `gpt-6-luna`.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt      # macOS/Linux: .venv/bin/python
cd frontend && npm install && cd ..
cp .env.example .env                                          # then put your key in PORTKEY_API_KEY
```

The app looks for `.env` in this folder first, then one folder up.

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

**Tests** (offline, no AI calls; 64 tests):

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
python ../scripts/operator_tools.py report-data            # the same, as compact JSON by task
python ../scripts/operator_tools.py orgs                   # allowances used
python ../scripts/operator_tools.py allow <org id> grants  # give an organization one more
```

Limits per organization live in `backend/allowances.py`.

**Load the Keystone example** (a fictional housing nonprofit with a full set of results, no AI calls). In the Shell:

```bash
python ../scripts/operator_tools.py import-org ../scripts/demo/keystone_family_housing.json --username keystone.demo --name "Keystone demo"
```

It asks you to choose a password, then you can sign in as `keystone.demo`. That account is **view-only**: anyone with its password can look around and download files, but can't change anything or lock it out with wrong passwords.

---

## Project layout

```
backend/         FastAPI app: agents/ (the AI agents), prompts/ (one per agent), routes/ (the API)
frontend/        Vite + React + TypeScript website
tests/           64 offline tests and the scripted demo server
scripts/         operator tools, test-profile runner, and builders for the deliverables, examples, and evidence
docs/            report/ and slides/ (sources of the submitted report.html and slides.html)
examples/        keystone/: every file the app produced for the Keystone example
evidence/        proof behind the report's claims
output/          harness.md (the agents, documented) and audit_log.json
data/            fictional test organizations and the Keystone test profile
PROJECT_PLAN.md  the original product plan
AI_prompts.md    every prompt used to build it
```

The submitted `report.html` and `slides.html` are single files with every image embedded, built with `python scripts/build_deliverables.py --access-code <code>`. They go into `deliverables/`, which is git-ignored so the access code stays out of this public repo.
