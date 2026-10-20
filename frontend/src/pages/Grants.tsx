import { useEffect, useState } from "react";
import { api, type GrantApplication, type GrantList } from "../api";
import PrivacyPanel from "../components/PrivacyPanel";
import { SourceChips, SourcesList } from "../components/studio/Sources";
import Thinking from "../components/studio/Thinking";
import { when } from "../format";

const ACCEPT = ".pdf,.docx,.pptx,.txt,.md";

/** Step 5: research a foundation and draft a grant application from everything the organization has built. */
export default function Grants() {
  const [list, setList] = useState<GrantList | null>(null);
  const [current, setCurrent] = useState<GrantApplication | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const l = await api.grants();
    setList(l);
    return l;
  };

  useEffect(() => {
    load()
      .then((l) => (l.applications[0] ? api.grant(l.applications[0].id).then(setCurrent) : null))
      .catch((e: Error) => setError(e.message));
  }, []);

  if (!list) return error ? <p className="alert">{error}</p> : <p className="muted">Loading…</p>;

  return (
    <div className="studio">
      <div className="page-title">
        <p className="eyebrow">Step 5 · Fund the work</p>
        <h1>Grant applications</h1>
        <p className="muted">
          Name a foundation, share its website and request for proposals, and paste its questions. The team researches what
          the foundation cares about and drafts answers that put your logic model and latest results in front of it.
          Your numbers stay current: they fill in from your latest data every time you open or download the draft.
        </p>
      </div>
      {error && <p className="alert small">{error}</p>}
      <div className="designer">
        <div className="stack">
          <NewApplication list={list} onError={setError}
            onCreated={async (app) => { setCurrent(app); await load(); }} />
          {list.applications.length > 0 && (
            <section className="card">
              <h3>Your applications</h3>
              <ul className="runs">
                {list.applications.map((a) => (
                  <li key={a.id} className={current?.id === a.id ? "is-current" : ""}>
                    <button className="link-button" onClick={async () => setCurrent(await api.grant(a.id))}>{a.foundation}</button>
                    <span className="muted small">{when(a.created_at)}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
        <div className="stack">
          {current ? (
            <ApplicationView app={current} onChange={setCurrent} onError={setError}
              onDeleted={async () => { setCurrent(null); await load(); }} />
          ) : (
            <section className="card card--quiet">
              <h3>Your draft appears here</h3>
              <p className="muted small">You'll get answers to each question, a checklist of what to attach, and a Word document to finish and submit.</p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================ new application

function NewApplication({ list, onCreated, onError }: { list: GrantList; onCreated: (a: GrantApplication) => void; onError: (e: string | null) => void }) {
  const [form, setForm] = useState({ foundation: "", foundation_url: "", opportunity: "", questions: "", notes: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value });

  const submit = async () => {
    setBusy(true);
    onError(null);
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => data.append(k, v));
    files.forEach((f) => data.append("files", f));
    try {
      onCreated(await api.createGrant(data));
      setForm({ foundation: "", foundation_url: "", opportunity: "", questions: "", notes: "" });
      setFiles([]);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const none = list.left_this_month === 0;
  return (
    <section className="card stack">
      <div>
        <h3>Start an application</h3>
        <p className="muted small">
          {list.left_this_month} of {list.per_month} new applications left this month. Each one includes {list.revisions} round of feedback.
        </p>
      </div>
      {!list.has_plan && (
        <p className="alert alert--soft small">Approve your logic model and metrics first: the writer builds your case from them.</p>
      )}
      <label className="field"><span>Foundation name *</span>
        <input value={form.foundation} maxLength={160} onChange={set("foundation")} placeholder="e.g. Elm City Community Foundation" />
      </label>
      <label className="field"><span>Foundation website</span>
        <input value={form.foundation_url} maxLength={300} onChange={set("foundation_url")} placeholder="https://…" />
      </label>
      <label className="field"><span>Opportunity or RFP name (optional)</span>
        <input value={form.opportunity} maxLength={200} onChange={set("opportunity")} placeholder="e.g. 2027 Housing Stability Fund" />
      </label>
      <label className="field"><span>Questions or materials they ask for</span>
        <textarea rows={5} maxLength={6000} value={form.questions} onChange={set("questions")}
          placeholder={"Paste each question on its own line, with any word limits, e.g.\n1. Describe the need your program addresses (250 words)\n2. How will you measure success? (200 words)"} />
      </label>
      <label className="field"><span>Anything else the writer should know? (optional)</span>
        <textarea rows={2} maxLength={1000} value={form.notes} onChange={set("notes")} placeholder="e.g. We're asking for $40,000 for one year of rent assistance." />
      </label>
      <label className="field"><span>Upload the RFP or anything about your organization (up to 3 files)</span>
        <input type="file" multiple accept={ACCEPT} onChange={(e) => setFiles(Array.from(e.target.files ?? []).slice(0, 3))} />
      </label>
      <p className="muted small">Files are read once, in memory, and never saved. The AI only reads text a person can see on the page.</p>
      <div className="row-end">
        <button className="btn btn--primary" disabled={busy || none || form.foundation.trim().length < 2} onClick={submit}>
          {busy ? "Working…" : "Research & draft"}
        </button>
      </div>
      {busy && <Thinking label="Researching the foundation, drafting your answers, and checking privacy… this takes a few minutes." />}
    </section>
  );
}

// ============================================================ one application

function Placeholdered({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\[ADD:[^\]]*\])/).map((part, i) =>
        part.startsWith("[ADD:") ? <mark key={i} className="placeholder">{part}</mark> : <span key={i}>{part}</span>)}
    </>
  );
}

function ApplicationView({ app, onChange, onError, onDeleted }: {
  app: GrantApplication; onChange: (a: GrantApplication) => void; onError: (e: string | null) => void; onDeleted: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState("");
  const words = feedback.trim() ? feedback.trim().split(/\s+/).length : 0;
  const d = app.draft;
  const p = app.profile;
  const sources = p?.sources ?? [];

  const act = async (label: string, fn: () => Promise<GrantApplication>) => {
    setBusy(label);
    onError(null);
    try {
      onChange(await fn());
      setFeedback("");
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  if (!d) return null;
  return (
    <>
      <section className="card stack">
        <div className="numbers__head">
          <div>
            <p className="eyebrow">{app.foundation}{d.opportunity ? ` · ${d.opportunity}` : ""}</p>
            <h3>{d.title}</h3>
            <p className="muted small">Numbers as of {when(app.numbers_as_of)}. They refresh every time you open or download this.</p>
          </div>
          <div className="downloads">
            <a className="btn btn--primary btn--small" href={api.grantDocUrl(app.id)} download>Word document</a>
            <button className="btn btn--ghost btn--small" disabled={!!busy}
              onClick={() => act("The Privacy Reviewer is reading…", () => api.checkGrantPrivacy(app.id))}>Run privacy check</button>
          </div>
        </div>
        {app.privacy && <PrivacyPanel privacy={app.privacy} />}
        {app.missing_numbers.length > 0 && (
          <p className="alert alert--soft small">Some numbers the draft uses no longer exist in your data (shown as “–”): {app.missing_numbers.join(", ")}.</p>
        )}
        {busy && <Thinking label={busy} />}
      </section>

      {p && (
        <section className="card stack">
          <h3>What {p.foundation} cares about</h3>
          <p className="small"><em>{p.mission}</em></p>
          {app.research_mode === "knowledge" && (
            <p className="alert alert--soft small">Live web search wasn't available, so this comes from the model's knowledge. Check each source before relying on it.</p>
          )}
          <ol className="priorities small">
            {p.priorities.map((pr, i) => (
              <li key={i}><strong>{pr.priority}</strong> {pr.evidence} <SourceChips ids={pr.source_ids} sources={sources} /></li>
            ))}
          </ol>
          {p.typical_grant && <p className="small"><strong>Typical grant:</strong> {p.typical_grant}</p>}
          {p.cautions.length > 0 && <p className="small"><strong>Watch out:</strong> {p.cautions.join("; ")}</p>}
        </section>
      )}

      <section className="card stack">
        <h3>Why you're a strong fit</h3>
        <p className="small"><Placeholdered text={d.fit_summary} /></p>
        {d.answers.map((a, i) => (
          <div key={i} className="answer">
            <h4>{a.question}</h4>
            <p className={`small ${a.over_limit ? "hint" : "muted"}`}>
              {a.words} words{a.word_limit ? ` of ${a.word_limit}` : ""}{a.over_limit ? ": over the limit, please trim" : ""}
              {a.priorities_addressed.length > 0 && ` · speaks to: ${a.priorities_addressed.join(", ")}`}
              {" "}<SourceChips ids={a.source_ids} sources={sources} />
            </p>
            <div className="answer__text"><Placeholdered text={a.answer} /></div>
            <button className="link-button small" onClick={() => navigator.clipboard?.writeText(a.answer)}>Copy answer</button>
          </div>
        ))}
      </section>

      {(d.checklist.length > 0 || d.needs_input.length > 0) && (
        <section className="card stack">
          <h3>Before you submit</h3>
          {d.checklist.length > 0 && (
            <ul className="checklist small">
              {d.checklist.map((c, i) => (
                <li key={i} className={c.status === "ready" ? "is-ready" : ""}>
                  <span className="tag">{c.status === "ready" ? "Ready" : "Needs input"}</span> <strong>{c.item}</strong> {c.note}
                </li>
              ))}
            </ul>
          )}
          {d.needs_input.length > 0 && (
            <>
              <p className="small"><strong>Information to add</strong> (highlighted in the draft):</p>
              <ul className="small">{d.needs_input.map((n, i) => <li key={i}>{n}</li>)}</ul>
            </>
          )}
        </section>
      )}

      <section className="card stack">
        <h3>One round of feedback</h3>
        {app.revisions_left > 0 ? (
          <>
            <p className="muted small">Tell the writer everything you'd like changed. This is the last AI pass, so include it all.</p>
            <textarea rows={3} value={feedback} maxLength={4000} onChange={(e) => setFeedback(e.target.value)}
              placeholder="e.g. Emphasize our landlord partnerships, and keep answer 2 under 180 words." />
            <div className="row-end">
              <span className={`small ${words > 150 ? "hint" : "muted"}`}>{words} / 150 words</span>
              <button className="btn btn--primary btn--small" disabled={!!busy || !words || words > 150}
                onClick={() => act("Revising your draft and re-checking privacy…", () => api.reviseGrant(app.id, feedback))}>Send feedback</button>
            </div>
          </>
        ) : (
          <p className="muted small">Feedback round used. Finish the draft in the Word document; its numbers stay current.</p>
        )}
      </section>

      {sources.length > 0 && <section className="card"><SourcesList sources={sources} title="Foundation sources" /></section>}

      <div className="row-end">
        <button className="link-button small" onClick={async () => {
          if (!window.confirm("Delete this draft? This month's allowance isn't given back.")) return;
          try {
            await api.deleteGrant(app.id);
            onDeleted();
          } catch (e) {
            onError((e as Error).message);
          }
        }}>Delete this draft</button>
      </div>
    </>
  );
}
