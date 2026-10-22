# AI Prompts — Final Project: Through Line (Nonprofit Impact Toolkit)

This file records the prompts used to build the final project, verbatim, step by step.
It also serves as the build roadmap to the MVP: each step lists its **goal**, what
**done** looks like, and **what the prompt should cover**, followed by space for the
verbatim prompt, any follow-up prompts, and a reflection.

The full product plan lives in [PROJECT_PLAN.md](PROJECT_PLAN.md).

**Ground rules for every step**
- Build one piece at a time; don't start the next step until the current one is "done."
- Synthetic data only. No real names, no real participant information, ever.
- `PORTKEY_API_KEY` stays in `.env`. Never commit it, print it, or send it to the frontend.
- All agents use OpenAI via Portkey with `gpt-6-luna`.
- Every agent run is written to the append-only agent audit log (built in Step 6).
- `output/harness.md` is updated at the end of every step that changes the system.
- Bauhaus design: clean, modern, lots of color.

---

## Roadmap at a Glance

| Phase | Steps |
|---|---|
| **Setup** | 0 Planning · 1 Project rules & repo · 2 Harness kickoff |
| **Foundation** | 3 Scaffold · 4 Data model · 5 Auth & org isolation · 6 Agent foundations & audit log |
| **Module 1: Logic Model Studio** | 7 Agent team + interview + draft + Studio UI (built) · 8 Studio redesign + measurement plan (built) |
| **Module 2: Data Collection** | 10 Working prototype: accounts, survey tools, both portals, program numbers, dashboard + exports (also covers 4, 5, 11, 14, 15) |
| **Module 3: Qualitative Insight** | 12 Privacy Guard · 13 Outcome Coder + Testimonials + approval queue |
| **Module 4: Reporting** | 14 Dashboard charts (built in 10) · 15 Report Designer agent, branded deck + flyer, program-number templates (built) |
| **Hardening & Ship** | 16 Security review · 17 End-to-end test · 18 Reflection · 19 README & GitHub |
| **Stretch** | S1 Voice reflections · S2 AI narrative summary · S3 Funder share link |

---

## Step 0: Planning the Project

**Goal:** Turn the idea into a clear plan and a step-by-step prompt log.
**Done when:** `PROJECT_PLAN.md` and this file exist.

### Verbatim prompt

> Okay, right now we are going to work in the folder for the final project. We are not going to do any coding or building right now. This session is just about planning for the final project. For the final project, I want to build a tool that will help a nonporfit clearly articulate its theory of change, identify metrics that it wants to track to know if it is havening an impact, and then I want it to have tools to help collect that data, aggregate it, and then be able to communicate it to a funder/donor/or for an impact report. I want this to work for a variety of nonprofits, so that many different very low resourced nonprofits could use it and more easily articulate their impact. This is going to have a lot of different pieces that will build upon all of the work that we've done in this class. So I want it to have a Vite/ react front and fastAPI backend. I will want two different areas of this work where the nonprofit will work with a small team of pydantic agents that will work with them: The first is when they are building their logic model and i want the person to be able to have a small team that reviews information they already have, and asks the nonprofit executive about their enterprise to help build a logic model, and then to slect metrics and a plan for how to measure it. This will result in: the logic model, the top metrics, and 1 or 2 tools to help get the information. I then want to be able to deploy the  survey tools that can help collect this information: like program participants might self rank their knowledge of a certain topic before hand and then it will also have a post survey as well. I also want this to be able to record qualitative data---I the think that is a big part of this--so we want a person to be able to respond with qualitative reflections or to talk into it and give their expeirence before and after and thenfor the AI to help assess that information to record data and to create testimonials. For the data collection, the firm should choose two diffent methhods: either they can distribute the survey out to people, so send people a link and they complete the survye, or can have staff submit their reflections on a particular individual (think abotu homelessness, a case manager may write their reflections or assessment). Lastly, once we have this data, i want there to be some basic charts that the software helps to build to help the firm communcate their data. A key piece tha we will thorughout here is data security and integrity: we want people's personal information to be anonymous and any passwords and things to be safe. Build me an MD file with this idea cleaned up and outlined. And then in the chat here give me feedback on how complex this is and if we should simplify.

### Follow-up prompt

> Okay I agree with all of those things. Can you build me a prompt log md file that has a structure like what we've done for past assignments that will guide us to build each piece one at a time as we build up to the MVP. Be sure to include some time for us to build the harness, an audit log for the agents that we will have in there, etc.

### Reflection

---

## Step 1: Project Rules, Repo Setup & .gitignore

**Goal:** Set the ground rules before any code exists so the vibe coder and the agents always know them.
**Done when:** Folder structure exists, `.gitignore` covers secrets/DB/recordings, and a project rules file records the non-negotiables.

**What the prompt should cover**
- Folder layout: `frontend/`, `backend/`, `backend/prompts/`, `data/`, `output/`.
- `.gitignore`: `.env`, database files, uploaded documents, audio, `node_modules/`, `__pycache__/`, `output/audit_log.jsonl` (decide whether to commit a sample).
- A rules file (e.g., `PROJECT_RULES.md` or a `CLAUDE.md` in the folder) with: synthetic data only, no PII sent to the LLM, model = `gpt-6-luna`, human approves every AI output that leaves the app, the audit log is append-only.
- The scope decisions from planning: one program per org, voice is stretch, AI tags themes before it scores.

### Verbatim prompt

*(One prompt covered both Step 1 and Step 2.)*

> I would like you to set up our workspace in the folder based on what I've told you So we're going to need a Python environment. We're going to need a git ignore file. We're going to need a file, file folder structure, like the one that you've proposed, to just sort of set everything up and give us space to work in. I also want us to go ahead and work on the second step of this project. So I want us to also make the harness file, harness.md file. This is going to be that living document that's going to structure the and then everything for the project and make it very, very clear for outside observers. We'll also later on have a readme file that will provide some better direct information. So let's make sure we're clear about the purpose of the two. The harness file, we really want to make this really focus more on the actual agents themselves and the work that they're doing. And kind of putting in the loops, um, how many um, you know, times and files, uh, the prompts, the tools, those sorts of things, the models. You know, from the get-go here, let's make sure that we only do Luna for our models. Um, and let's also go ahead and make that audit log, um, which will just be a file, an MD file that, or actually let's not make it an MD file, make a JSON file that will just record all the information that the agents that we're going to make on later on are going to use. So let's just set up the whole space, including the harness, the folders, the audit log, and get us ready to go.

### Follow-up prompt

> 

### Reflection

---

## Step 2: Harness Kickoff

**Goal:** Start `output/harness.md`, the living document that explains the whole system to a manager (or grader).
**Done when:** The harness has its skeleton sections, filled in where we already know the answer.

**What the prompt should cover**
- Sections: Purpose & users · Architecture · Data model · Agents (role, prompt file, tools, inputs/outputs) · Routes · Audit log · Security & privacy guardrails · Human-in-the-loop checkpoints · Testing evidence · Known limitations.
- Rule: every later step updates the relevant section; the document should read smoothly, not as a pile of notes.

### Verbatim prompt

> *(Same prompt as Step 1; see above.)*

### Follow-up prompt

> 

### Reflection

---

## Step 3: Scaffold the App + Bauhaus Design System

**Goal:** A running FastAPI backend and Vite + React frontend that talk to each other, with the visual language set.
**Done when:** Frontend loads, calls a `/health` route on the backend, and shows the Bauhaus shell (nav, color palette, typography, buttons, cards).

**What the prompt should cover**
- `backend/main.py` (FastAPI) with `/health`; CORS for the Vite dev server.
- Vite + React (TypeScript?) frontend with routing and placeholder pages: Dashboard, Logic Model Studio, Instruments, Responses, Insights, Reports, Settings.
- A small design system: colors, type scale, reusable components.
- A small "test project for a class, synthetic data" disclaimer in the footer.
- Update harness: Architecture section + how to run.

### Verbatim prompt

> Yeah, I know we have the space all set up. Um, for the work that we do. I'm going to go ahead and kind of build the actual app structure. And so we're going to now we have this space all set up um, for the work that we do. I'm going to go ahead and kind of build the actual app structure. We're going to scaffold. Build a fast API backend and a deep plus React frontend. We want these two pieces to talk to each other. You know, think about the end in mind here. We want the front page, the website, to have a few different things. If we're thinking about first the view of the main user, which is an employee at the nonprofit that we're working with, right? And so that person is going to have sort of a tab with the logic model, and that's where they're going to build it with their agents, and that's where we're going to build this sort of cohort of agents that sort of help them with that. Then it's going to have sort of a tool place uh, with various um, where they're going to build and sort of deploy the actual survey tools to individuals that are in their nonprofit and working with that nonprofit. And then we're going to have a charting table or like a, a dashboard place where they can look at the data. And preferably, you know, at first we'll just make these sorts of basic charts and we might try to improve that with some time. This is just kind of creating the overall structure for what we're going to be doing.

### Follow-up prompt

> 

### Reflection

---

## Step 4: Data Model & Database

**Goal:** Define every table up front so later steps plug in cleanly.
**Done when:** SQLModel tables exist, the DB is created on startup, and a seed script loads two synthetic demo nonprofits.

**What the prompt should cover**
- Tables: `Organization`, `User`, `OrgDocument`, `LogicModel`, `Outcome`, `Metric`, `Instrument` (with `mode`: self-report / staff), `Question`, `Cohort`, `Participant` (code only), `Response` (wave: pre / post), `Answer`, `Reflection`, `QualCoding`, `Testimonial`, `Consent`, `AuditEvent`.
- Every org-owned table has `org_id`.
- Seed data: a youth financial-literacy program and a homelessness case-management program, all synthetic.
- A reset script to restore the seed state before a fresh demo run.
- Update harness: Data model section (each table, its fields, why it matters).

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 5: Accounts, Roles & Org Isolation

**Goal:** Secure logins and a guarantee that one nonprofit never sees another's data.
**Done when:** Admin and staff can log in; every protected route checks the role and scopes queries by `org_id`; a test proves cross-org access is blocked.

**What the prompt should cover**
- Password hashing (Argon2 or bcrypt), never stored or logged in plain text.
- JWT or secure cookie sessions with expiry.
- Roles: Admin (ED) and Staff. Participants never get accounts.
- A shared dependency that injects the current user + `org_id` into every route.
- Login / logout UI.
- Update harness: Security section + routes.

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 6: Agent Foundations & the Agent Audit Log

**Goal:** Build the shared plumbing every agent will use, *before* building any agent, including the audit log.
**Done when:** A trivial test agent runs through Portkey on `gpt-6-luna`, and its full run appears in the audit log.

**What the prompt should cover**
- Shared Portkey/OpenAI client config (key from `.env` only).
- `backend/models.py` for the Pydantic output types agents will return.
- `backend/prompts/` with one `.md` file per agent.
- **Agent audit log**, append-only (`output/audit_log.json` + the `AuditEvent` table), recording for every agent step: timestamp, org, run ID, agent name, input summary (already redacted), tool calls, structured output, hand-offs, token usage, and which human approved or edited the result.
- Never edit or delete audit entries; only append.
- A backend route + simple frontend view to browse the audit log for an org.
- Update harness: Audit log section.

*Mostly built in Step 7: the shared model config, `models.py`, prompts folder, and the append-only hash-chained audit writer (`backend/audit.py`, plus a per-session audit route). Still open: a live test run on gpt-6-luna, and a frontend view of the audit log.*

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 7: Agent Team #1: Logic Model Studio

*Re-scoped when built: one prompt built the team, the interview, the draft, the PowerPoint round trip, the Studio UI (old Step 9), and the audit writer (old Step 6).*

**Goal:** A boss agent works with the client and consults three specialists (Evaluation Specialist, Client Advocate, Sector Expert) to turn the client's materials and five interview answers into a logic model the client can edit in PowerPoint and approve.
**Done when:** A client can upload materials, answer five questions, review a draft, revise it, download and re-upload it as PowerPoint, and approve it, with every agent step in the audit log and no uploads saved.

### Verbatim prompt

> Okay, what I want to do now is go ahead and build the team of agents that are going to help the party build their logic model. You already have a clear idea of who those folks are, what kind of agents you want for them. I want them to really have one boss agent, and that is the party that's really going to think through and interact with the actual client, um, but take information from the client and consult the other agents. I think it would be valuable to make sure that somebody else, one agent is really focused on measurement and evaluation and has that background. One of them is more thinking from the actual client's perspective. It'd be great if we could build an agent that kind of is focused on having area expertise in the subject matter of the client. So if it's like a homelessness service provider is the client, then that person is going to build up their knowledge base and be thinking about what makes sense, what are the best practices and standards for a homeless service provider. I want to make sure that we're thinking about tokenomics and not like having this go on forever and ever. So I think where we wanted this to be is have the first step is to have the client send whatever information they have about their firm already, like decks or old logic models or things like that, as well as maybe your website, so that the team can get up to speed with what currently exists. And then go through a process where you ask the client five questions. And you know, one of the times the client can ask provide an answer to that question and then have that inform the agents and then do it again and again and again and then let's see if we can get use that enough information to build a first draft and then the agents can propose the client and then get feedback. Ultimately I then also want to make sure that what the agents produce is something that um, is downloadable like a PDF or something or Rather than, not a PDF, something that's downloadable and manipulable, like a PowerPoint presentation, so that the client can manipulate it just in something that they're used to, like PowerPoint, and then upload it uh, to move forward. After they do that, then that, you know, we'll have an aligned upon logic model, and then the next step will be really more focusing on the specific metrics. on this. We want agent prompt files in the backend slash prompts folder. Uh, one prompt file per agent. There's probably data types in a models.py file. And we want agent files in the backend folder. We want to make sure that the prompts for each agent are you know, very robust to guide the work that they're doing. Make sure that the agents have the tools that they need uh, to communicate and to kind of do their work. Uh, one thing that's really important is that I want to make sure that information that goes to these agents doesn't survive or pass the actual session, that we're not collecting lots and lots and lots of client data. But they're using this information um, in their thinking. So particularly for file uploads that they might put in the chat window, we don't want to save those, but inevitably we need to save the information they type into the chat. Again, make sure that we're appending to the audit trail as a JSON file, and that we're updating the harness appropriately.

### Follow-up prompt

> My hope is that this work will get us to kind of a minimal viable product on just the first step of this work, which is to uh, work with the agents and have that conversation and find a little bit of context and build a very simple logic model. If there's more that we need to do to get to that MVP step, let me know. I don't feel like you need to do it on your own without my express consent or like prompting. But let's figure out what other steps we'll want to do to make sure that we can get something that we can play around with and test out.

### Reflection

---

## Step 8: Studio Redesign + Measurement Plan (Metrics)

*One prompt covered refinements to Step 7 (live team huddle, session length, word limits, a staged game-like flow with a tutorial, in-app editing, a subtler style, optional document requests) and the metrics step.*

**Goal:** After approving the logic model, the team recommends 3–5 metrics with the exact questions and scales plus 1–2 collection tools. The client edits, gives feedback, and approves, then downloads everything.
**Done when:** The full Studio runs tutorial → share → five questions → logic model → metrics → download, with the team's work visible live.

### Verbatim prompt

> Okay, let’s make some modifications:
> 1.	I want something that shows the user that the team is thinking about it. In particular, can you make it so that we can see the connections that are being made between the agents and how they are passing information to each other. I like the idea of continuing to have them represented by colors and shapes rather than people. But show how information is going back and forth to each other and what they are thinking. I want a live window that summarizes the things they are thinking/discussing.
> 2.	The session timed out while I was drafting my response. I want it to last longer. It could take someone a long time to think through these questions.
> 3.	Give the author a word limit or a time limit. And have it tick downward.
> 4.	The layout is not very clear and I think that it moved around (like the order of some of the elements changed at some point). I think that maybe it should be a little bit more like a game. So that you do not see all of the stuff for the logic model until its ready. First you are just interacting with the chat bot and telling it information and answering their five questions, then once you are done with answering the questions the logic model appears and that is when you go into the edit stage. It wasn’t super clear to me how to refine the logic model at first, so to make it clear, I think we start this process there should first be a small tutorial that tells you the steps that you are going through and what to expect at each step in the process. Then the screen can change depending on if you are just giving the bots information and asking their questions versus refiing the logic model.
> 5.	Rather than download the powerpoint and upload it, would it be possible for the person to edit directly in a shared workspace? Either way works well. Certaintly we want a download option at the end.
> 6.	In general, the Bauhaus style is a bit overwhelming and intimidating. Can we make it a bit more sublte?
> 7.	I think that the agent team should also feel free to ask for additional uploads that could aid their task. These can always be optional.
> Let’s also build out the metric build section. So after you build the model and then provide feedback on the model, Let’s walk through making metrics for it. I think this can start with the bots recommending measures and a measurement plan. What are the questions, and on what scale? Then the person can provide feedback on those metrics.

### Follow-up prompt

*Step 8b: collaboration, research, and cited metrics.*

> •	The agent team doesn’t really use the other agents very much. Is there additional ways that they could collaborate, or are there better collaborators that could help this process?
> •	I think one way that would help with this, is if the team did some best practices research on what are the most compelling metrics for funders (philanthropic or government) in the chosen sector and to really propose the logic model and the metrics to be aligned with how other key organizations with that individuals field would put it together. So rather than seeing the person putting it together as the soul expert, go out and find other sources of information. In particular, I think that this would help create stronger questions for the metrics section.
> •	Speaking of the metrics section, lets not just offer up one question per metric but multiple. Ideally, based on your research, you could offer up recommended questions or things that should be asked based on other sources and you could site those sources (like if a big time grantor in that sector will want to know a specific measure, help the person know that and make informed decisions).

*Decisions Doug made when asked:* collaboration = **add a Funder Researcher + required rounds** (question proposals at intake, peer review of every draft); research = **live web search with a fallback** to model knowledge, sources marked unverified.

### Reflection

---

## Step 9: Logic Model Studio UI

*Built together with Step 7, then redesigned in Step 8.*

---

## Step 10: Working Prototype: Accounts, Survey Tools, Portals & Dashboard

*One prompt covered old Steps 4 (data model), 5 (accounts), 10 (participant surveys), 11 (staff assessments), 14 (dashboard) and 15 (report export).*

**Goal:** A working prototype. Staff create an account first, and everything (logic model, metrics, surveys, data) is saved to their organization. Survey tools are built straight from the approved metric questions, with matched pre/post surveys, a Survey Review Bot, light staff edits, demographics, a participant portal, staff bulk entry, program numbers entered by staff, and dashboards with Excel and PowerPoint downloads.
**Done when:** A staff member can sign up, build the logic model and metrics, publish a survey, have participants log in and answer pre and post, enter program numbers, and download the data, each chart (Excel), and the report (PowerPoint).

### Verbatim prompt

> Okay, I think this looks good. I want you to go ahead and build out the next two components so that we can build a working prototype. I want this to include the survey tools that could be used by nonprofit staff to collect the informaiton that is being recorded based on the logic model. I want the questions to flow into it directly from the questions that were decided upon in the metrics section. I want this to include pre and post surveys that can be matched up. We will need a log in portal, actually, I think we will need two: one for staff where they can enter more forms at once, and then one for individual participants that may be sent this survey and who would then fill it out. I think in here we should have a survey review bot that will review the survey to make sure that the questions make sense, that the scales are the same throughout, and that there is valuable insights being collected. For the survey tools, I want the staff to be able to modify the tools slightly, in particular, they should be able to add open response questions, hide quesitons  (in case it is not relevant) or make other small refinements that the survey bot recommends. They should also be able to add basic demographic information so that the firm can describe who is in their program.  For the sign in portal, we are going to want to make sure that these are very safe like we have done before, passwords and usernames should be hashed and the information should be secure. Then I walso want to see dashboards that are populated by the data that is coming in from the surveys. Lastly, it strikes me that some of the data that the logic model will wnat and, therefore, we will want in the dashboards, is information that the firm has rather than the participants (perhaps, amount of dollars spent on xyz thing, or just attendees as an event but you do not want to send a survey to every single person) for these we will also wnat there to be a way for the staff in their protal to just be able to log in and provide those numbers. I'm actually thinking of a few more things: Since we are building a sign in page, we should probably go ahead and do that from the beginnning, so that If I am a staff member I first make my account, and then i build my logic model and metrics and it is all saved with me the whole time. I will also want to be able to download the data that I have coming in from the surveys, as well as download the impact report charts and figures. I think being able to download each graph as an excel file, and then also download the collection as a powerpoint or pdf would be ideal.

### Follow-up prompt

>

### Reflection

---

## Step 11: (merged into Step 10)

*Staff assessments are part of the Step 10 survey tools.*

---

## Step 12: Privacy Guard (PII Redaction)

**Goal:** Make sure no personal information reaches the LLM or the analysis tables.
**Done when:** Every reflection passes through the Privacy Guard before any other agent sees it, and a test set of synthetic reflections full of fake names, addresses, and phone numbers comes out redacted.

**What the prompt should cover**
- Rule-based pass (regex for phones, emails, addresses) **plus** an agent pass for names and places.
- Store the redacted text for analysis; keep a redaction log (what *type* was redacted, never the value).
- Fail closed: if redaction fails, the text does not go to downstream agents.
- Update harness: Security & privacy section + Agents.

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 13: Agent Team #2: Outcome Coder + Testimonial Writer + Approval Queue

**Goal:** Turn qualitative reflections into evidence linked to the org's outcomes, plus testimonials.
**Done when:** Redacted reflections are tagged with themes and linked outcomes (with quoted evidence); consented reflections get testimonial drafts; staff approve or reject everything in an approval queue.

**What the prompt should cover**
- Outcome Coder: themes + outcome links + evidence quotes first; a rubric score **only** where the instrument defines a rubric, always with a rationale.
- Pre vs. post comparison for the same participant code.
- Testimonial Writer: light editing only, no invented content, only for consented reflections.
- Approval queue UI: AI draft and human final version both stored.
- All runs and approvals go to the audit log.
- Update harness: Agents + human-in-the-loop.

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 14: Dashboard Charts

**Goal:** Auto-build a small set of clear charts from the metric plan and collected data.
**Done when:** Each demo org's dashboard shows its charts and headline numbers, computed from the seeded responses.

**What the prompt should cover**
- Fixed chart types: pre vs. post per metric (paired bars / dumbbell), rating distribution (stacked bar), outputs over time, qualitative theme frequency.
- Headline stats (e.g., "% of participants who improved by ≥1 point").
- **Small-cell suppression:** hide any breakdown with fewer than 5 people.
- Approved testimonials shown next to the numbers.
- Bauhaus styling; follow the dataviz guidance.
- Update harness.

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 15: Report Designer, Program-Number Templates & Cleanup

**Goal:**
- Program numbers can be filled in a downloadable Excel template and uploaded back.
- Demographic charts show percentages.
- The quick impact report looks good.
- A new Report Designer agent builds a branded 10–15 minute funder deck and a one-page flyer from chosen metrics and the org's design standards, and checks that no personal information gets in.
- Run it for Keystone, then clean up the whole project.

**Done when:** Keystone's branded deck and flyer are generated live, pass the privacy check, and look polished; tests pass; the code and docs are tidy.

### Verbatim prompt

> For the program numbers, i want there to be an upload feature where the person can download an excel file with all of the questions that need to be answered, and then they can update that file for a specific month,  with all of the answers in there, and then when they upload it, the numbers flow through to every metric. I want demographic charts to be percentages rather than raw numbers (what percentage of the people you serve are white not the number) I wan tthe impact repor taht you download to be more beautiful, the charts are not well designed. Additionally lets build a feature where you can go in and design your impact report. The person will input what metrics they want to have included, and then they will also tell a bot about their firm's desgn standards (color, logo, etc.) and the agent will build a deck for talking to funders/donors (10-15 min presentaiton about the org and its impact to date) as well as a one pager that will look like a flyer for their impact as well. Build that capability and and then run it for keystone iwth the example data that you have and making up the design informaiton. This agent will also be the one that will check that no personal identifying information makes it into the final materials. Once you do this, go through an do a clean up of everything. Ensure the work is clear and clean.

*Outputs:*
- Backend: `design.py` (all deck/flyer rendering), `privacy.py` (PII scanner), `branding.py`, `program_numbers.py`, `agents/report_designer.py`, `prompts/report_designer.md`, `routes/reports.py`
- Frontend: `pages/ReportDesigner.tsx` (Impact Report tab), template download/upload on Program numbers, % demographics
- Keystone brand + generated logo in `data/test_profiles/keystone_family_housing/`; the runner now uploads numbers by template and has a `report` stage
- Live run: `data/test_profiles/keystone_family_housing/runs/20261020_104049/` (14-slide funder deck, one-pager PDF, previews)
- Tests: `tests/test_reports.py` (28 passing in total)

### Follow-up prompt

>

### Reflection

---

## Step 15b: Visible-Text Safety, Token Accounting, Usage Limits & Grant Writer

**Goal:**
- Agents read only what a person can see in a document (no hidden, white, tiny, or off-page text).
- Every agent run's tokens are recorded per staff member; staff see their own, and the operator sees everyone's.
- Each bot has a usage limit; the impact report becomes a shell (one design + one feedback round) that refreshes with new data; the privacy check can run any time.
- A final **Grants** tab researches a foundation and drafts a tailored application from the organization's live data.

**Done when:** hidden-text documents are proven safe in tests; usage is visible to staff and the operator; limits hold; a grant draft is produced offline end to end; harness updated.

### Verbatim prompt

> 1.	Safety: please make sure that whenever a document is provided to the system, that it is reviewed by what a person can see. We don’t want the bots to be fooled by any invisible text, or super small text, or anything like that.
> 2.	Tokenomics: We want to record how many tokens each user of our platform uses up. Feel free to provide that information to the user, but also make it so that I can get that information as well.
> 3.	And important part of ensuring that we don’t use too many tokens, is to limit the amount of times a user can use the bots. So, we only have five questions, we only have a few reviews, similarly when we build the template for the impact reports, we only have one design stage and lets have one review round, where the user can give feedback. The one bot that can be called whnever is the one that will review to make sure that the output doesn’t have personally identifiable information. So fo the branding and deck, we want it to build the shell, but then to have the person be able to update it with fresh data (in the event that more surveys come in).
>
> Lastly, we are going to build a feature (this will be the final tab at the top) that will take all of the information that is going into the system so far, and will help the firm write grant applications or appeals to donors. For foundations, the person should provide a link to the foundation’s website, upload any information they have about the firm or opportunity (like if their was an RFP or something) and the questions/materials that are being aske for by the foundation. The system will then research the foundation, get a sense of what is important to that foundation, and build a custom set of draft application materials that focuses on the things that are important to the foundation, and that highlight up to date data from the firm as well. An adctually, lets just have it focus on grant applications, not on donor appeals.

*Outputs:*
- Safety: `backend/visible.py` (PDF via pdfium, Word, PowerPoint, web pages, Markdown, plain text), wired into `intake.py`; `tests/test_visible_text.py`
- Tokens: `backend/ledger.py` (`TokenUsage` table), `GET /api/usage` + the **AI usage** page, `scripts/operator_tools.py` (usage report, allowances, one-time backfill from the audit log)
- Limits: `backend/allowances.py`; the report shell with live `{{number}}` tokens (`backend/figures.py`); the separate **Privacy Reviewer** agent
- Grants: `routes/grants.py`, `agents/grant_writer.py`, `prompts/grant_writer.md`, the Funder Researcher's foundation job, `grant_docx.py`, and the **Grants** tab
- Tests: `tests/test_limits_grants.py` (44 passing in total)

### Follow-up prompt

>

### Reflection

---

## Step 16: Security & Guardrails Review

**Goal:** Deliberately try to break the privacy and security promises, then fix what breaks.
**Done when:** A written checklist in the harness, with evidence, shows each guardrail holds.

**What the prompt should cover**
- Cross-org access attempts; expired / guessed survey links; unauthenticated routes.
- Prompt injection inside uploaded documents and participant reflections (e.g., "ignore your instructions and…").
- Secret scan: no key in code, logs, frontend bundle, or audit log.
- Confirm PII never appears in the audit log or LLM inputs.
- Update harness: Security section with the test results.

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 17: End-to-End Test with a Fake Organization (live)

**Goal:** Run the whole app with a fictional nonprofit and synthetic data, save that fake firm as a reusable test profile, and show how every piece works in a walkthrough deck.
**Done when:** A live run completes from sign-up to downloads; the profile and outputs are saved; the deck is built from real screenshots and real outputs.

### Verbatim prompt

> Okay, Can you run a full test through the app with how it is built right now using a fake compnay, and fake data, and then build me a powerpoint to show me how all of these pieces work? Save the data in a profile somewhere so that we can use the same fake data about a fake firm again as we run more tests. But build the powerpoint as if you are demonstrating to me what this all looks like and how it works.

*Decision Doug made when asked:* **live gpt-6-luna** (not scripted agents).

*Outputs:*
- `data/test_profiles/keystone_family_housing/` (profile, screenshots, run outputs)
- `scripts/run_test_profile.py`
- `scripts/build_demo_deck.py`
- `docs/Through_Line_live_walkthrough.pptx`

### Follow-up prompt

>

### Reflection

---

## Step 18: Reflection

**Goal:** Reflect on what worked, what didn't, and what building this taught me about AI agents for the social sector.
**Done when:** Written reflection added here and summarized in the harness.

### Verbatim prompt

> 

### Follow-up prompt

> 

### Reflection

---

## Step 19: README & Push to GitHub

**Goal:** Ship a clean, safe public repo.
**Done when:** README explains the project and how to run it; repo is pushed; nothing sensitive is committed.

**What the prompt should cover**
- README: problem, features, architecture, setup, demo walkthrough, screenshots.
- Pre-push check: no `.env`, no database, no uploads/audio, no secrets in history.
- Run the submission check before handing in.

### Verbatim prompt

> Okay this all looks good. i want you to review everything, make sure it is clean, and then push to my github and walk me thorugh putting it on render so that it is a live website that I can easily share with someone who can login

*Decisions Doug made when asked:* **public** repo; Render **Starter + 1 GB persistent disk** (the free tier wipes files on restart); new organizations need an **access code** (colleagues join with invite codes).

*Outputs:* `README.md`, `Dockerfile`, `.dockerignore`, `render.yaml`; FastAPI now serves the built website; the sign-up access code (`THROUGH_LINE_SIGNUP_CODE`); security headers; `tests/test_deploy.py`.

### Follow-up prompt

> 

### Reflection

---

## Step 19b: Fixes from Doug's Walk-Through

**Goal:** Polish what Doug found while using the app before sharing it with a pilot organization, and get the Keystone example onto the live site.

### Verbatim prompt

> When working through the logic model progression, I want the six steps to always be visible. So when you scroll up, I want the stages to be clear.
> You can remove the “we skipped text you can’t see” thing. We want this safety feature, but we do not need to broadcast it.
> WEhen they put the logic model together it says “step 3 logic model” and then it also says  4: logic model. Similar mis-match on step 4 metrics and 5-metrics
>
> On the metrics page, in the cells with questions, make them automatically be big enough that you can read the whole thing, right now it is too small to read.
> Can you have the review bot for the survey to also accept feedback. Like I wanted it to make the text response question and turn them into data fields (so that it could be easier to make it quantitative than qualitative.
> Need more instructions on the survey tools tab to let folks know that that there are their surveys, and then there are ways to generate custom information for participants to fill out their responses, and you can enter responses yourself and upload ht eprogram numbers  Also, just like how you can upload data in the program numbers, have a download excel file that you can fill in to mass upload information in the "enter responses" section.
> There was a problem with my survey where it was changed into a pre survey and then the questions didn't make sense. This is something that the survey checker agent should help to fix--if they change the timing of the surveys, they may also need to adjust the wording of the pre and post surveys as well. Can you update the website to have the data from the keystone example on the render website? Or walk me through how to do it.

*Outputs:*
- A sticky Studio stepper; headings numbered from the stepper; the hidden-text notice removed from the UI (the protection and its audit entry stay)
- Question boxes that grow to fit (`AutoTextarea`)
- **Multiple-choice questions** (choose one / choose all that apply) end to end, with a "Survey answers" dashboard section
- The Survey Review Bot takes an optional request and can convert a written question into multiple choice (`make_choice`); a new automatic check and prompt rule catch wording that doesn't fit when a question is asked
- Survey Tools guide; Excel template download/upload for Enter responses (`response_sheets.py`)
- Completed Studio sessions no longer expire
- `operator_tools.py export-org` / `import-org` and the Keystone bundle (`scripts/demo/keystone_family_housing.json`)
- Tests: `test_survey_upgrades.py`, `test_org_import.py` (59 passing in total)

### Follow-up prompt

>

### Reflection

---

## Step 20: Final Report and Slide Deck

**Goal:** A 10–15 page HTML report with app screenshots and a 9–10 slide deck that tell the same story in Through Line's branding.

### Verbatim prompt

> Okay, let's work on the  two key outputs that we need for this final project. First there will be a report. it will be 10-15 pages and it will be built in HTML it will include screenshots of the app to help the reader. It will include the following: A title and links. We will rpovde the link to the GItHUb repo as well as to the render site and a sentence abotu what the app does. The next section is on the motivation: the motivation for this is because funders are increasing the desire to see data that demonstrates their investment in nonprofits are making a real difference. Although this is a noble effort, it creates a signfiicant burden on small nonprofits that do not additional operational funding to hire consultants, let alone full time staff, to focus on program evaluation. This can accidentally lead to increased inequities within the social sector where organizations with assets continue to grow, while small and nimble nonprofits that may serve those furthest from opportunity are locked out of the capital needed to make a real difference. This tool is designed to help small nonprofits articulate their logic model, determine the metrics needed to demonstrate that impact, and then to have the actual tools to collect and report on that data. In doing so, the tool walks the staff through the process of doing this step by step. The next section is about what is new: I could use your help to look and see if there are other software that already does this (who would be competittors for this) I think traditionally this is really done by evaluation frims and consulancies (there are many perhaps we can find a few and demonstrate estimates of what these tend to cost). This project puts that power in the hands of the actual nonprofit. Additionally, by having the survey tools integrated with the logic model, everything flows together (you don't have a logic model that is fully disjoint from the the metrics that the firm tracks and reports on, it all flows together).  The next section is the agents. We have several of them in here. We want to say for each agent (or agent team) what they do, what tools can each agent use, the organization of the agent team (with a diagram) which model is used (everything is on Luna for cost efficienicy and because it has proven to be sufficient in testing), and then to show a real run, step by step with screenshots. Throughout, we will use the Keystone example. The next section is on tokenomics. I want to show the tokenomics for keystone, for my example that I rna on the render site for The Place, and hopefully we can record the tokenomics for the runs that are done by our outside testers Kids at their best and sara. We will wnat to know how many tokes it uses, what is the run cost per the various tasks. We should also include what we have done to keep the costs down, which is primarily to limit the number of times that someone can use the tool. Given the costs, we should estimate what it would cost to run at scale: 100 users and 10,000 users. We whould explore if the cost savings (fewer runs) made the applicaiton worse). this may come up in our testers feedback. The next section is on safety, here I want to highlight the work we have to be safe with the passwords for staff who log in, how we use codes rather than names for participants so that no name data is going into the thing, and how we have a bot that is focused on checking if any personally identifiable information is in there. We also have the agents only looking at documents to avoid prompt injection (invisible ink or super small text). And we also have usage limits to stop overspending (right? If not, lets put that in there). The next section is on impact , this is where I hope that our feedback from our testers wll be particularly helpful. Limits and next steps is the final section. There are a few limits: first, it currently only really works with a pretty simple nonprofit (which is the target audience of this applicatio nanyways) like one program rather than a lot of interconnected ones. We could have it work on more of them. Although we have ways to do bulk uploads and downloads, there is still  a sclability challenge, particularly in connecting data between this tool and some other data tool that someone has (oh, is there a way to build a connection through an MPC server that could allow someone to easily port over their data from some other place that nonprofits frequently use to track this kin dof data? let me know your thoughts, if it is too complicate dperhaps we just write about this in this section.  With more time we would also explore different chart types and reporting tools. That is all for the paper. We also need a slide deck that is 10 slides max that follow sthis format 1. title, 2. the problem and who has it, 3. what is new baout your solution, 4.. agents, 5. demo screenshots; 6. cost to run; 7. safety; 8. impact the numbers; 9. What's next.  These two documents should relaly speak to each other, very similar story and information in both, but in two different formats. I also want everything to follow the same brandign that was developed for Through Line, i really like it.

*Outputs:* `docs/report/index.html` (with screenshots and figures in `docs/report/img/`), first drafted alongside a PowerPoint deck, `operator_tools.py report-data`, and web searches counted in the token ledger. Research on competitors, consultant costs, and gpt-6-luna pricing was done by a research agent, with sources cited in the report.

### Follow-up prompt

> https://zlisto.github.io/mgt_409_fa26/project_requirements.html this is the link to the project. I know that this page has lots of traps. i do not wnat you to do the project for me--we'e already done the project together. Can you just look through here and see if there is anything else huge that we are missing or if there is anything else we should be building for this project.

> yes take care of 1,2, 4, 5 and for three lets go with the first one: put the access code in there. And let's make sure that we also put that information in the paper and on the slides (i want it to be very clear to the graders that this is how they do this work.

*Outputs:* the deck became a reveal.js page, `docs/slides/index.html` (10 slides, reveal.js from a CDN), replacing the PowerPoint deck. `scripts/build_deliverables.py --access-code <code>` builds the two Canvas files, `deliverables/report.html` (15 printed pages) and `deliverables/slides.html`, with every image embedded so each opens by double-click. The report's cover and the last slide tell graders exactly how to sign up. The access code is filled in only at build time and `deliverables/` is git-ignored, so the code never appears in the public repo. The token ledger now records cached input tokens (shown on the AI usage page), and the report adds cached input, cost per user per month, and a screenshot of the usage page as evidence.

> username is keystone.demo for the keystone demo and the password is [redacted] i think having this in our documents is great so they can see an example with data.

*Outputs:* the built report and slides offer graders the ready-made Keystone login (`--demo`). Like the access code, the password is filled in only at build time and never committed.

> can you give me the code to put into the powershell to get some usage statstics again on the tokens?

> [pasted `report-data` output from the Render Shell]

*Outputs:* Kids at Their Best's measured tokens added to the tokenomics: 26 runs, 285,623 in (30% cached) and 30,202 out, 8 searches, about 12¢. It is the third Studio run in the comparison and the first measured cached share.

> Okay, here is the transcript from my debrief call with jodi. Just review it right now. Then recommend some edits/updates to the final presentation materials, and any  updates that we should make to the final project. The deadline is Monday, so I don't want to make too many changes to the software, so i'd be curious your thoughts on if we should build the multiple logic models idea, this feels like it may make things a lot more complicated.
>
> [debrief call transcript pasted; not reproduced here because it includes personal conversation]

> Yes, go ahead and make those edits and updates across all of them.

*Outputs:* Jodi's findings, quotes, and caveats in the report's Impact section and on slide 8; "did limits make it worse?" answered from the tester (the 5-question cap was a favorite) in the report and on slide 6; multiple programs (her #1 ask, with the one-organization-per-program workaround) and a rapid-response logic model for emergencies added to Limits and slide 9. Multiple logic models were deliberately not built before the deadline: one program per organization runs through every feature and the live data. Small fix from the call: the public header now lists **Staff sign in** first and labels the other link "Survey participants (code + PIN)", and the participant sign-in page links to staff sign-in.

### Reflection

---

## Stretch Goals (only after the MVP is done)

### S1: Voice Reflections
Browser recording → transcription → Privacy Guard → same qualitative pipeline. Delete raw audio after transcription.

#### Verbatim prompt

> 

#### Reflection

### S2: AI Narrative Summary for Reports
An agent drafts the narrative section of the impact report from approved data only; the ED edits and approves it.

#### Verbatim prompt

> 

#### Reflection

### S3: Funder Share Link
A read-only, aggregated view of the report behind an expiring link.

#### Verbatim prompt

> 

#### Reflection
