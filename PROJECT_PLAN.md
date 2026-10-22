# Final Project Plan — Nonprofit Impact Toolkit

*Working title: **Through Line** — from mission to evidence to story.*
*Status: built and live. This is the original design from the planning session, kept as written; some ideas (voice reflections, AI-coded testimonials) became next steps. What was actually built is documented in `output/harness.md`, and how, prompt by prompt, in `AI_prompts.md`.*

---

## 1. The Problem

Small, low-resourced nonprofits do real work but struggle to *prove* it. Funders ask for a theory of change, outcome metrics, and an impact report — and most small organizations have no evaluation staff, no data system, and no time. They end up with anecdotes in one place, sign-in sheets in another, and a scramble every grant cycle.

## 2. The Idea

A web app that walks a nonprofit through the full impact cycle, with AI agents doing the heavy lifting and humans making the decisions:

```
 1. ARTICULATE        2. MEASURE           3. COLLECT            4. COMMUNICATE
 Theory of change  →  Pick top metrics  →  Surveys + staff    →  Charts, numbers,
 + logic model        + measurement plan    reflections + voice    testimonials,
                      + 1–2 tools           (pre / post)           impact report
```

It must work for **many kinds of nonprofits** (youth programs, housing/homelessness, food security, workforce training, arts, health) — so nothing is hard-coded to one sector. The agents adapt to whatever the organization tells them.

## 3. Users

| User | What they do in the app |
|---|---|
| **Executive Director / Admin** | Builds the logic model with the agent team, approves metrics and tools, views dashboards, exports reports. |
| **Staff (e.g., case manager)** | Submits structured reflections/assessments about a participant they work with. |
| **Participant** | Opens a survey link (no account), answers pre/post questions, types or speaks a reflection. |
| **Funder / Donor** *(read-only output)* | Never logs in. Receives an exported report or shared, aggregated view. |

---

## 4. Module 1 — Logic Model Studio (Agent Team #1)

The ED works with a small team of Pydantic AI agents to go from "what we do" to a funder-ready logic model and measurement plan.

### Inputs
- Existing materials the org already has: mission statement, past grant applications, annual reports, program descriptions (paste text or upload PDF/DOCX).
- A guided interview with the ED.

### Agent team

| Agent | Role | Output (Pydantic-typed) |
|---|---|---|
| **Document Reviewer** | Reads uploaded materials; extracts programs, populations served, activities, claimed outcomes; flags gaps. | `OrgProfile` + list of `Gaps` |
| **Interviewer** | Asks the ED focused follow-up questions to fill those gaps, one at a time, in plain language. | Interview transcript + updated `OrgProfile` |
| **Logic Model Architect** | Drafts the theory of change and logic model: Inputs → Activities → Outputs → Short-term outcomes → Long-term outcomes, plus key assumptions. | `LogicModel` |
| **Measurement Planner** | Proposes candidate metrics for each outcome, helps the ED pick the **top 3–5**, and designs **1–2 data-collection tools** (e.g., pre/post self-assessment survey, staff assessment rubric). | `MetricPlan` + `Instrument` drafts |

An orchestrator coordinates the hand-offs. The ED can edit every artifact directly; agents propose, the human approves.

### Deliverables
1. **Theory of change** statement (one paragraph, "If… then… because…").
2. **Logic model** — visual diagram rendered in HTML/React (Bauhaus style) + exportable.
3. **Top metrics** — each with definition, data source, collection method, frequency, and target.
4. **1–2 measurement tools** — ready to deploy in Module 2.

---

## 5. Module 2 — Data Collection

Every tool is an **Instrument**. Each instrument has one of two **collection modes**, chosen by the org:

### Mode A — Participant self-report (distributed link)
- Org generates a unique survey link (or QR code) for a program cohort.
- Participant answers without creating an account.
- Supports **pre** and **post** waves of the same instrument.
- Question types: Likert/self-rating (e.g., "Rate your knowledge of budgeting 1–5"), multiple choice, numeric, open-text reflection, and **voice reflection** (speak → transcribed).

### Mode B — Staff-submitted assessment
- A logged-in staff member fills out an instrument *about* a participant (e.g., a case manager's housing-stability assessment or narrative reflection).
- Same question types, same pre/post structure.
- Narrative reflections flow into the qualitative pipeline below.

### Linking pre and post — anonymously
- Each participant gets a **participant code** (e.g., `HX-4821`), not a name.
- Pre and post responses are joined on the code, so the app can compute change per person without ever storing who that person is.
- Any name ↔ code mapping (if the org needs one at all) stays with the org, outside the app — or in a separately encrypted table only admins can see.

---

## 6. Module 3 — Qualitative Insight (Agent Team #2)

Qualitative data is a core strength of this tool, not an add-on. Reflections (typed or spoken, from participants or staff) go through a second agent team:

| Agent | Role | Output |
|---|---|---|
| **Transcriber** *(tool, not really an agent)* | Converts voice recordings to text. | Transcript |
| **Privacy Guard** | Detects and redacts personal information (names, addresses, phone numbers, specific places) **before** anything else sees the text. | Redacted text + redaction log |
| **Outcome Coder** | Maps the reflection to the org's metrics/outcomes; tags themes; where a rubric exists, proposes a score with a short rationale and quoted evidence. | `QualCoding` (themes, outcome links, optional score, evidence quotes) |
| **Testimonial Writer** | Drafts a short, faithful testimonial from the reflection (light editing only — no invented content). | `TestimonialDraft` |

Rules:
- Testimonials are **only** drafted when the participant gave consent to be quoted.
- Every AI score and testimonial is a **draft** until a staff member approves it.
- Pre vs. post reflections from the same participant code can be compared ("what changed in how they describe X").

---

## 7. Module 4 — Reporting & Communication

- **Dashboard** with a small set of auto-built charts:
  - Pre vs. post comparison per metric (paired bars or dumbbell chart)
  - Distribution of ratings (stacked bar)
  - Outputs over time (e.g., participants served per month)
  - Qualitative theme frequency
- **Headline numbers**, e.g., "78% of participants improved their budgeting confidence by ≥1 point."
- **Approved testimonials** displayed alongside the numbers.
- **Export**: one-page impact report (HTML → PDF) combining logic model, key metrics, charts, and testimonials — ready for a funder or annual report.
- Optional AI-assisted narrative summary of results (always editable).

---

## 8. Data Security & Integrity (cross-cutting)

This is a design principle across every module, not a final step.

**Anonymity & privacy**
- Participants are identified only by participant codes; no names, emails, or birthdates collected by default.
- Privacy Guard redacts PII from free text **before** it is sent to the LLM or stored in analyzable form.
- Explicit consent screen on every survey; separate opt-in for being quoted in a testimonial.
- Small-number suppression: charts/reports don't show breakdowns for groups smaller than 5 people (prevents re-identification).
- Raw voice recordings are deleted after transcription (configurable).

**Accounts & secrets**
- Staff/admin passwords hashed with Argon2 or bcrypt; never stored in plain text.
- Session tokens (JWT or secure cookies) with expiry; role-based access (Admin vs. Staff).
- Survey links use long, random, unguessable tokens and can be closed/expired.
- API keys (`PORTKEY_API_KEY`) live only in `.env` / environment — never in code, never sent to the frontend.

**Integrity**
- Each organization's data is fully isolated (every query scoped by `org_id`).
- Audit log of who created, edited, approved, or exported what.
- AI outputs are stored alongside the human-approved version, so it's always clear what the AI suggested vs. what a person confirmed.
- Input validation on every endpoint via Pydantic models.

---

## 9. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Vite + React (TypeScript optional), Bauhaus visual style — clean, modern, bold color |
| Charts | Recharts (or similar React chart library) |
| Backend | FastAPI |
| Agents | Pydantic AI, structured outputs via Pydantic models |
| LLM | OpenAI via Portkey, model `gpt-6-luna` |
| Voice | Browser recording (MediaRecorder) → transcription endpoint |
| Database | SQLite for development (SQLModel/SQLAlchemy), Postgres-ready |
| Auth | FastAPI auth with hashed passwords + JWT |

### Core data model (draft)
`Organization` · `User` (admin/staff) · `OrgDocument` · `LogicModel` · `Outcome` · `Metric` · `Instrument` · `Question` · `Cohort` · `Participant` (code only) · `Response` (wave: pre/post, mode: self/staff) · `Answer` · `Reflection` · `QualCoding` · `Testimonial` · `Consent` · `AuditEvent`

---

## 10. Proposed Build Phases

| Phase | Goal | Done when… |
|---|---|---|
| **0. Foundation** | Repo, FastAPI + Vite skeleton, auth, DB models, Bauhaus design system | Admin can log in and see an empty org dashboard |
| **1. Logic Model Studio** | Agent team #1 end to end | Demo org produces a logic model, 3–5 metrics, and 1 instrument |
| **2. Collection** | Survey links (Mode A) + staff form (Mode B), pre/post with participant codes | Seeded demo cohort completes pre and post |
| **3. Qualitative** | Text reflections → Privacy Guard → Coder → Testimonial draft → approval | Approved testimonials appear in the app |
| **4. Reporting** | Dashboard charts + exportable impact report | One-page report generated from demo data |
| **5. Stretch** | Voice input, AI narrative summary, multiple programs per org, funder share link | — |

## 11. Demo Scenario

Use two fictional, contrasting nonprofits with synthetic data to show the tool generalizes:
- **A youth financial-literacy program** (participant self-report, pre/post knowledge survey).
- **A homelessness case-management program** (staff-submitted assessments and narrative reflections).

No real personal data is ever used in development or the demo.

## 12. Open Questions

1. One program per organization for the MVP, or multiple programs from the start?
2. Should the name ↔ participant-code mapping live in the app at all, or always stay offline with the org?
3. Voice: MVP or stretch?
4. Should funders get a live share link, or only exported reports?
5. How much should the Outcome Coder *score* qualitative data vs. only tag themes? (Scoring is more powerful but harder to make trustworthy.)
6. Which homework/lecture pieces to reuse directly (e.g., multi-agent patterns from HW5, FastAPI + Pydantic AI backend from Lecture 13)?
