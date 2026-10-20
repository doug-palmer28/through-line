import { useEffect, useState } from "react";
import type { MeasurementPlan, Method, Metric, Scale, SurveyQuestion } from "../../api";
import { SourceChips, SourcesList } from "./Sources";
import AutoTextarea from "../AutoTextarea";

export const SCALES: Record<Scale, string> = {
  agree_5: "Agree (1–5)",
  confidence_5: "Confidence (1–5)",
  frequency_5: "How often (1–5)",
  scale_0_10: "Rating 0–10",
  yes_no: "Yes / No",
  number: "Number",
  open_text: "Written answer",
};
export const METHODS: Record<Method, string> = {
  participant_survey: "Participant survey",
  staff_assessment: "Staff assessment",
  program_records: "Program records",
};

type Props = {
  plan: MeasurementPlan;
  version: number;
  outcomes: string[];
  readOnly?: boolean;
  busy?: boolean;
  onSave?: (plan: MeasurementPlan) => Promise<void>;
  onDirtyChange?: (dirty: boolean) => void;
};

const blankMetric = (outcome: string): Metric => ({
  name: "New metric",
  outcome,
  method: "participant_survey",
  questions: [{ text: "", scale: "agree_5", included: true, source_ids: [] }],
  timing: "Pre and post",
  how_scored: "",
  why_it_matters: "",
  funder_relevance: "",
  source_ids: [],
});

const clean = (p: MeasurementPlan): MeasurementPlan => ({
  ...p,
  metrics: p.metrics.map((m) => ({ ...m, questions: m.questions.filter((q) => q.text.trim()) })),
});

/** The measurement plan as an editable workspace: metrics, their questions and scales, and the tools. */
export default function MetricsEditor({ plan, version, outcomes, readOnly, busy, onSave, onDirtyChange }: Props) {
  const [work, setWork] = useState(plan);
  useEffect(() => setWork(plan), [version]); // reset only when a new version arrives
  const dirty = !readOnly && JSON.stringify(clean(work)) !== JSON.stringify(clean(plan));
  useEffect(() => onDirtyChange?.(dirty), [dirty, onDirtyChange]);

  const setMetric = (i: number, patch: Partial<Metric>) =>
    setWork({ ...work, metrics: work.metrics.map((m, j) => (j === i ? { ...m, ...patch } : m)) });
  const outcomeOptions = (current: string) => (outcomes.includes(current) ? outcomes : [current, ...outcomes]);

  return (
    <section className="card plan">
      <div className="lm__head">
        <div>
          <p className="eyebrow">Measurement plan · version {version}</p>
          <h2>How you'll know it's working</h2>
        </div>
        {!readOnly && dirty && (
          <div className="lm__save">
            <span className="muted small">Unsaved changes</span>
            <button className="link-button" onClick={() => setWork(plan)}>
              Undo
            </button>
            <button className="btn btn--primary btn--small" disabled={busy} onClick={() => onSave?.(clean(work))}>
              Save changes
            </button>
          </div>
        )}
      </div>

      {readOnly ? (
        <p>{work.summary}</p>
      ) : (
        <textarea rows={2} value={work.summary} onChange={(e) => setWork({ ...work, summary: e.target.value })} />
      )}

      <div className="metrics">
        {work.metrics.map((m, i) => (
          <article key={i} className="metric">
            <div className="metric__head">
              <span className="metric__num">{i + 1}</span>
              {readOnly ? (
                <h3>{m.name}</h3>
              ) : (
                <input className="metric__name" value={m.name} onChange={(e) => setMetric(i, { name: e.target.value })} />
              )}
              {!readOnly && (
                <button
                  className="icon-button"
                  title="Remove metric"
                  aria-label="Remove metric"
                  onClick={() => setWork({ ...work, metrics: work.metrics.filter((_, j) => j !== i) })}
                >
                  ×
                </button>
              )}
            </div>

            <div className="metric__meta">
              <label>
                <span>Outcome it tracks</span>
                {readOnly ? (
                  <p>{m.outcome}</p>
                ) : (
                  <select value={m.outcome} onChange={(e) => setMetric(i, { outcome: e.target.value })}>
                    {outcomeOptions(m.outcome).map((o) => (
                      <option key={o}>{o}</option>
                    ))}
                  </select>
                )}
              </label>
              <label>
                <span>Method</span>
                {readOnly ? (
                  <p>{METHODS[m.method]}</p>
                ) : (
                  <select value={m.method} onChange={(e) => setMetric(i, { method: e.target.value as Method })}>
                    {Object.entries(METHODS).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                )}
              </label>
              <label>
                <span>When</span>
                {readOnly ? (
                  <p>{m.timing}</p>
                ) : (
                  <input value={m.timing} onChange={(e) => setMetric(i, { timing: e.target.value })} />
                )}
              </label>
              <label>
                <span>How it's scored</span>
                {readOnly ? (
                  <p>{m.how_scored}</p>
                ) : (
                  <input value={m.how_scored} onChange={(e) => setMetric(i, { how_scored: e.target.value })} />
                )}
              </label>
            </div>

            {(m.funder_relevance || m.source_ids.length > 0) && (
              <p className="metric__funders">
                <span className="eyebrow">Why funders care</span> {m.funder_relevance}{" "}
                <SourceChips ids={m.source_ids} sources={work.sources} />
              </p>
            )}

            <div className="questions">
              <div className="questions__head">
                <span className="eyebrow">Questions</span>
                {!readOnly && (
                  <span className="small muted">
                    {m.questions.filter((q) => q.included).length} of {m.questions.length} selected
                  </span>
                )}
              </div>
              {m.questions
                .map((q, qi) => ({ q, qi }))
                .filter(({ q }) => !readOnly || q.included)
                .map(({ q, qi }) => {
                  const setQ = (patch: Partial<SurveyQuestion>) =>
                    setMetric(i, { questions: m.questions.map((x, j) => (j === qi ? { ...x, ...patch } : x)) });
                  return (
                    <div key={qi} className={`question ${q.included ? "" : "is-off"}`}>
                      {readOnly ? (
                        <>
                          <p>
                            {q.text} <SourceChips ids={q.source_ids} sources={work.sources} />
                          </p>
                          <span className="chip">{SCALES[q.scale]}</span>
                        </>
                      ) : (
                        <>
                          <input
                            type="checkbox"
                            className="question__pick"
                            checked={q.included}
                            title={q.included ? "Included: click to leave out" : "Optional: click to include"}
                            onChange={(e) => setQ({ included: e.target.checked })}
                          />
                          <div className="question__body">
                            <AutoTextarea value={q.text} placeholder="Question wording" onChange={(e) => setQ({ text: e.target.value })} />
                            {(q.note || q.source_ids.length > 0) && (
                              <p className="question__note">
                                {q.note} <SourceChips ids={q.source_ids} sources={work.sources} />
                              </p>
                            )}
                          </div>
                          <select value={q.scale} onChange={(e) => setQ({ scale: e.target.value as Scale })}>
                            {Object.entries(SCALES).map(([k, v]) => (
                              <option key={k} value={k}>
                                {v}
                              </option>
                            ))}
                          </select>
                          <button
                            className="icon-button"
                            title="Remove question"
                            aria-label="Remove question"
                            onClick={() => setMetric(i, { questions: m.questions.filter((_, j) => j !== qi) })}
                          >
                            ×
                          </button>
                        </>
                      )}
                    </div>
                  );
                })}
              {!readOnly && (
                <button
                  className="link-button"
                  onClick={() =>
                    setMetric(i, {
                      questions: [...m.questions, { text: "", scale: "agree_5", included: true, source_ids: [] }],
                    })
                  }
                >
                  + Add your own question
                </button>
              )}
            </div>
            {m.why_it_matters && <p className="metric__why">{m.why_it_matters}</p>}
          </article>
        ))}
        {!readOnly && work.metrics.length < 6 && (
          <button
            className="btn btn--ghost"
            onClick={() => setWork({ ...work, metrics: [...work.metrics, blankMetric(outcomes[0] ?? "")] })}
          >
            + Add a metric
          </button>
        )}
      </div>

      <div className="tools-list">
        <span className="eyebrow">Collection tools</span>
        {work.tools.map((t, i) => (
          <div key={i} className="tool">
            <strong>{t.name}</strong>
            <span className="chip">{METHODS[t.method]}</span>
            <p className="muted small">
              {t.when} · covers {t.metrics.join(", ")}
            </p>
          </div>
        ))}
      </div>

      <SourcesList sources={work.sources} />
    </section>
  );
}
