import { useEffect, useState } from "react";
import { api, type InstrumentDetail, type SurveyFix, type SurveyIssue, type ToolQuestion, type ToolsData } from "../../api";
import Thinking from "../studio/Thinking";

type Props = { id: number; meta: ToolsData; onBack: () => void; onChanged: () => void };

const WAVE_CHOICES: { label: string; waves: ("pre" | "post")[] }[] = [
  { label: "Pre & post", waves: ["pre", "post"] },
  { label: "Pre only", waves: ["pre"] },
  { label: "Post only", waves: ["post"] },
];
const newId = () => "q_" + Math.random().toString(16).slice(2, 10);

/** Edit one survey tool: hide/show, small rewording, add open questions, demographics, and Survey Review Bot fixes. */
export default function InstrumentEditor({ id, meta, onBack, onChanged }: Props) {
  const [inst, setInst] = useState<InstrumentDetail | null>(null);
  const [work, setWork] = useState<{ name: string; questions: ToolQuestion[]; demographics: string[] } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = (d: InstrumentDetail) => {
    setInst(d);
    setWork({ name: d.name, questions: d.questions, demographics: d.demographics });
  };
  useEffect(() => {
    api.instrument(id).then(load).catch((e: Error) => setError(e.message));
  }, [id]);

  if (!inst || !work) return error ? <p className="alert">{error}</p> : <p className="muted">Loading…</p>;

  const dirty = JSON.stringify(work) !== JSON.stringify({ name: inst.name, questions: inst.questions, demographics: inst.demographics });
  const setQ = (qid: string, patch: Partial<ToolQuestion>) =>
    setWork({ ...work, questions: work.questions.map((q) => (q.id === qid ? { ...q, ...patch } : q)) });
  const original = new Set(inst.questions.map((q) => q.id));
  const lockedQ = (q: ToolQuestion) => inst.locked && original.has(q.id);

  const run = async (label: string, fn: () => Promise<InstrumentDetail>) => {
    setBusy(label);
    setError(null);
    try {
      load(await fn());
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };
  const save = () => run("Saving…", () => api.saveInstrument(id, work));

  const applyFix = (issue: SurveyIssue) => {
    const fix = issue.fix as SurveyFix;
    if (fix.action === "add_open_question") {
      setWork({
        ...work,
        questions: [...work.questions, { id: newId(), text: fix.text || "What would you like to tell us?", scale: "open_text",
          metric: null, source: "staff", hidden: false, reverse: false, note: "Suggested by the Survey Review Bot", waves: ["post"] }],
      });
      return;
    }
    if (!issue.question_id) return;
    const patch: Partial<ToolQuestion> =
      fix.action === "rewrite" ? { text: fix.text ?? undefined }
      : fix.action === "change_scale" ? { scale: fix.scale ?? undefined }
      : fix.action === "hide" ? { hidden: true }
      : fix.action === "set_waves" ? { waves: fix.waves ?? ["pre", "post"] }
      : { reverse: fix.reverse ?? true };
    setQ(issue.question_id, patch);
  };
  const fixLabel: Record<SurveyFix["action"], string> = {
    rewrite: "Use this wording", change_scale: "Change scale", hide: "Hide question", set_waves: "Change timing",
    set_reverse: "Mark reverse-scored", add_open_question: "Add this question",
  };
  const questionText = (qid: string | null) => work.questions.find((q) => q.id === qid)?.text;
  const issues = [...inst.checks.map((c) => ({ ...c, from: "check" })), ...(inst.review?.issues ?? []).map((c) => ({ ...c, from: "bot" }))];
  const isParticipant = inst.method === "participant_survey";

  return (
    <div className="stage stage--work">
      <div className="stage__main">
        <button className="link-button small" onClick={onBack}>← All survey tools</button>
        <section className="card tool-editor">
          <div className="lm__head">
            <div>
              <p className="eyebrow">
                {isParticipant ? "Participant survey" : "Staff assessment"} · {inst.status === "published" ? "Published" : "Draft"}
                {inst.locked && " · has responses"}
              </p>
              <input className="lm__title" value={work.name} onChange={(e) => setWork({ ...work, name: e.target.value })} />
              <p className="muted small">{inst.when}</p>
            </div>
            {dirty && (
              <div className="lm__save">
                <span className="muted small">Unsaved changes</span>
                <button className="link-button" onClick={() => setWork({ name: inst.name, questions: inst.questions, demographics: inst.demographics })}>
                  Undo
                </button>
                <button className="btn btn--primary btn--small" disabled={!!busy} onClick={save}>Save changes</button>
              </div>
            )}
          </div>
          {inst.locked && (
            <p className="notice small">
              Answers are coming in, so existing questions can't be reworded or re-scaled (it would break pre/post comparison).
              You can still hide questions and add new ones.
            </p>
          )}

          <ol className="tq-list">
            {work.questions.map((q) => (
              <li key={q.id} className={`tq ${q.hidden ? "is-hidden" : ""}`}>
                <div className="tq__main">
                  <textarea rows={1} value={q.text} disabled={lockedQ(q)} onChange={(e) => setQ(q.id, { text: e.target.value })} />
                  <div className="tq__meta">
                    {q.metric ? <span className="chip">{q.metric}</span> : <span className="chip chip--staff">Added by staff</span>}
                    <select value={q.scale} disabled={lockedQ(q)} onChange={(e) => setQ(q.id, { scale: e.target.value as ToolQuestion["scale"] })}>
                      {Object.entries(meta.scales).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                    </select>
                    <select value={q.waves.join(",")} onChange={(e) => setQ(q.id, { waves: WAVE_CHOICES.find((w) => w.waves.join(",") === e.target.value)!.waves })}>
                      {WAVE_CHOICES.map((w) => <option key={w.label} value={w.waves.join(",")}>{w.label}</option>)}
                    </select>
                    {["agree_5", "frequency_5", "confidence_5", "scale_0_10", "yes_no"].includes(q.scale) && (
                      <label className="tq__check" title="For items where a higher answer is worse (e.g. 'returned to shelter: yes'), so higher always means better">
                        <input type="checkbox" checked={q.reverse} disabled={lockedQ(q)} onChange={(e) => setQ(q.id, { reverse: e.target.checked })} />
                        Reverse-scored
                      </label>
                    )}
                  </div>
                </div>
                <div className="tq__actions">
                  <button className="link-button small" onClick={() => setQ(q.id, { hidden: !q.hidden })}>{q.hidden ? "Show" : "Hide"}</button>
                  {!original.has(q.id) || (q.source === "staff" && !inst.locked) ? (
                    <button className="icon-button" title="Remove" aria-label="Remove"
                            onClick={() => setWork({ ...work, questions: work.questions.filter((x) => x.id !== q.id) })}>×</button>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>
          <div className="tool-editor__add">
            <button className="btn btn--ghost btn--small" onClick={() => setWork({
              ...work,
              questions: [...work.questions, { id: newId(), text: "", scale: "open_text", metric: null, source: "staff",
                hidden: false, reverse: false, note: "", waves: ["post"] }],
            })}>+ Add an open-response question</button>
          </div>

          {isParticipant && (
            <div className="tool-editor__demo">
              <p className="eyebrow">Demographics (asked once, at the start)</p>
              <p className="muted small">Helps describe who's in your program. Every item includes "Prefer not to say", and groups under 5 are hidden in reports.</p>
              <div className="demo-picks">
                {Object.entries(meta.demographics).map(([key, d]) => (
                  <label key={key} className="tq__check">
                    <input type="checkbox" checked={work.demographics.includes(key)}
                           onChange={(e) => setWork({ ...work, demographics: e.target.checked ? [...work.demographics, key] : work.demographics.filter((k) => k !== key) })} />
                    {d.label}
                  </label>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>

      <aside className="stage__side">
        <section className="card approve">
          <h3>{inst.status === "published" ? "Collecting data" : "Ready to send?"}</h3>
          <p className="muted small">
            {inst.status === "published"
              ? isParticipant ? "Participants see this survey when they sign in." : "Staff can enter assessments in Enter responses."
              : "Publishing makes it available for data collection."}
          </p>
          {inst.status === "published" ? (
            <button className="btn btn--ghost" disabled={!!busy || dirty} onClick={() => run("Saving…", () => api.unpublish(id))}>Move back to draft</button>
          ) : (
            <button className="btn btn--primary" disabled={!!busy || dirty} onClick={() => run("Publishing…", () => api.publish(id))}>Publish</button>
          )}
          {dirty && <p className="small hint">Save your changes first.</p>}
        </section>

        <section className="card review-bot">
          <div className="review-bot__head">
            <span className="review-bot__icon" aria-hidden="true" />
            <h3>Survey Review Bot</h3>
          </div>
          <p className="muted small">Checks wording, scale consistency, and whether you'll learn what your logic model needs.</p>
          <button className="btn btn--secondary btn--small" disabled={!!busy || dirty || inst.reviews_left === 0} onClick={() => run("The Survey Review Bot is reading your survey…", () => api.reviewInstrument(id))}>
            {inst.review ? "Review again" : "Review this survey"}
          </button>
          <span className="muted small"> {inst.reviews_left === 0 ? "This survey has had its reviews." : `${inst.reviews_left} review${inst.reviews_left === 1 ? "" : "s"} left for this survey.`}</span>
          {busy && <Thinking label={busy} />}
          {error && <p className="alert small">{error}</p>}
          {inst.review && (
            <div className={`review-bot__summary ${inst.review.ready ? "is-ready" : ""}`}>
              <strong>{inst.review.ready ? "Ready to send" : "A few things to fix"}</strong>
              {inst.review.stale && <span className="small muted"> · you've edited since this review; run it again to refresh</span>}
              <p className="small">{inst.review.summary}</p>
            </div>
          )}
          {issues.length > 0 && (
            <ul className="issues">
              {issues.map((issue, i) => (
                <li key={i} className={`issue issue--${issue.severity}`}>
                  <span className="issue__tag">{issue.from === "check" ? "Automatic check" : "Review Bot"} · {issue.kind.replace("_", " ")}</span>
                  {issue.question_id && questionText(issue.question_id) && <em className="issue__q">“{questionText(issue.question_id)}”</em>}
                  <p>{issue.problem}</p>
                  <p className="muted">{issue.suggestion}</p>
                  {issue.fix?.action === "rewrite" && issue.fix.text && <p className="issue__new">→ “{issue.fix.text}”</p>}
                  {issue.fix && (
                    <button className="link-button small" onClick={() => applyFix(issue)}>{fixLabel[issue.fix.action]}</button>
                  )}
                </li>
              ))}
            </ul>
          )}
          {inst.review && inst.review.strengths.length > 0 && (
            <details className="small">
              <summary>What's working</summary>
              <ul>{inst.review.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </details>
          )}
          <p className="muted small">Fixes change your draft; nothing is saved until you click Save.</p>
        </section>
      </aside>
    </div>
  );
}
