import { useCallback, useEffect, useState } from "react";
import { api, type PortalForm, type PortalSurvey } from "../api";

type View = { kind: "login" } | { kind: "list" } | { kind: "form"; id: number; wave: string } | { kind: "thanks" };

/** The participant portal: sign in with a code + PIN, then answer pre and post surveys. Phone-friendly. */
export default function ParticipantPortal() {
  const [view, setView] = useState<View>({ kind: "login" });
  const [info, setInfo] = useState<{ code: string; org_name: string; surveys: PortalSurvey[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    try {
      setInfo(await api.mySurveys());
      setView({ kind: "list" });
    } catch {
      setView({ kind: "login" });
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  return (
    <div className="portal">
      <header className="portal__head">
        <span className="brand__mark" aria-hidden="true">
          <span className="shape shape--circle" />
          <span className="shape shape--square" />
          <span className="shape shape--triangle" />
        </span>
        <span className="portal__title">{info?.org_name ?? "Participant surveys"}</span>
        {view.kind !== "login" && (
          <button
            className="link-button small"
            onClick={async () => {
              await api.participantLogout();
              setInfo(null);
              setView({ kind: "login" });
            }}
          >
            Sign out
          </button>
        )}
      </header>

      <main className="portal__main">
        {error && <p className="alert">{error}</p>}
        {view.kind === "login" && <PortalLogin onDone={loadList} />}
        {view.kind === "list" && info && (
          <section className="card">
            <p className="eyebrow">Signed in as {info.code}</p>
            <h2>Your surveys</h2>
            <p className="muted">Your answers are private and are only reported in totals. Thank you for sharing.</p>
            {info.surveys.length === 0 && <p className="empty">There are no surveys for you right now.</p>}
            <ul className="portal__list">
              {info.surveys.map((s) => (
                <li key={s.id}>
                  <strong>{s.name}</strong>
                  <div className="portal__waves">
                    {s.waves.map((w) =>
                      w.done ? (
                        <span key={w.wave} className="chip chip--done">
                          ✓ {w.wave === "pre" ? "Starting survey" : "Ending survey"} done
                        </span>
                      ) : (
                        <button
                          key={w.wave}
                          className="btn btn--primary btn--small"
                          onClick={() => {
                            setError(null);
                            setView({ kind: "form", id: s.id, wave: w.wave });
                          }}
                        >
                          {w.wave === "pre" ? "Start: beginning-of-program survey" : "Start: end-of-program survey"}
                        </button>
                      ),
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
        {view.kind === "form" && (
          <SurveyForm
            id={view.id}
            wave={view.wave}
            onCancel={() => setView({ kind: "list" })}
            onError={setError}
            onDone={() => setView({ kind: "thanks" })}
          />
        )}
        {view.kind === "thanks" && (
          <section className="card portal__thanks">
            <h2>Thank you!</h2>
            <p>Your answers were saved.</p>
            <button className="btn btn--primary" onClick={loadList}>
              Back to my surveys
            </button>
          </section>
        )}
      </main>
      <footer className="footer">Class project prototype (AI Foundations, Yale). Synthetic data only.</footer>
    </div>
  );
}

function PortalLogin({ onDone }: { onDone: () => void }) {
  const [code, setCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <form
      className="card auth"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError(null);
        try {
          await api.participantLogin(code, pin);
          onDone();
        } catch (err) {
          setError((err as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <p className="eyebrow">Participant sign-in</p>
      <h2>Welcome</h2>
      <p className="muted">Enter the code and PIN your program gave you. You don't need your name.</p>
      <label className="field">
        <span>Your code</span>
        <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="e.g. HLH-4821K" required
               autoComplete="username" />
      </label>
      <label className="field">
        <span>PIN (6 digits)</span>
        <input type="password" inputMode="numeric" value={pin} onChange={(e) => setPin(e.target.value)} required
               maxLength={6} autoComplete="current-password" />
      </label>
      {error && <p className="alert">{error}</p>}
      <button className="btn btn--primary" disabled={busy}>
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}

function SurveyForm(props: { id: number; wave: string; onCancel: () => void; onError: (e: string | null) => void; onDone: () => void }) {
  const [form, setForm] = useState<PortalForm | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [demo, setDemo] = useState<Record<string, unknown>>({});
  const [busy, setBusy] = useState(false);
  const { id, wave, onError } = props;

  useEffect(() => {
    api.surveyForm(id, wave).then(setForm).catch((e: Error) => onError(e.message));
  }, [id, wave, onError]);

  if (!form) return <p className="muted">Loading…</p>;
  const answered = Object.keys(answers).length;

  return (
    <form
      className="card portal__form"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        props.onError(null);
        try {
          await api.submitSurvey(id, wave, answers, demo);
          props.onDone();
        } catch (err) {
          props.onError((err as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <p className="eyebrow">{wave === "pre" ? "Beginning of program" : "End of program"}</p>
      <h2>{form.name}</h2>
      <p className="muted small">There are no right or wrong answers. Skip anything you'd rather not answer.</p>

      {form.questions.map((q, i) => (
        <fieldset key={q.id} className="pq">
          <legend>
            <span className="pq__num">{i + 1}</span> {q.text}
          </legend>
          {q.scale === "open_text" ? (
            <textarea rows={3} maxLength={2000} value={(answers[q.id] as string) ?? ""}
                      onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} />
          ) : q.scale === "multi_choice" ? (
            <div className="pq__checks">
              {(q.options ?? []).map((o) => {
                const list = (answers[q.id] as string[]) ?? [];
                return (
                  <label key={o} className={`pq__opt ${list.includes(o) ? "is-on" : ""}`}>
                    <input type="checkbox" checked={list.includes(o)}
                           onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.checked ? [...list, o] : list.filter((x) => x !== o) })} />
                    {o}
                  </label>
                );
              })}
            </div>
          ) : q.scale === "choice" ? (
            <div className="pq__options">
              {(q.options ?? []).map((o) => (
                <label key={o} className={`pq__opt ${answers[q.id] === o ? "is-on" : ""}`}>
                  <input type="radio" name={q.id} checked={answers[q.id] === o} onChange={() => setAnswers({ ...answers, [q.id]: o })} />
                  {o}
                </label>
              ))}
            </div>
          ) : q.scale === "number" ? (
            <input type="number" min={0} inputMode="numeric" value={(answers[q.id] as string) ?? ""}
                   onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} />
          ) : (
            <div className={`pq__options ${q.options && q.options.length > 6 ? "pq__options--row" : ""}`}>
              {q.options!.map((label, idx) => {
                const value = q.scale === "scale_0_10" || q.scale === "yes_no" ? idx : idx + 1;
                return (
                  <label key={label} className={`pq__opt ${answers[q.id] === value ? "is-on" : ""}`}>
                    <input type="radio" name={q.id} checked={answers[q.id] === value}
                           onChange={() => setAnswers({ ...answers, [q.id]: value })} />
                    {label}
                  </label>
                );
              })}
            </div>
          )}
        </fieldset>
      ))}

      {form.demographics.length > 0 && (
        <div className="pq__demo">
          <p className="eyebrow">About you (optional)</p>
          <p className="muted small">This helps the program describe who it serves. Results are only shown for groups of 5 or more.</p>
          {form.demographics.map((d) => (
            <label key={d.key} className="field">
              <span>{d.label}</span>
              {d.multi ? (
                <div className="pq__checks">
                  {d.options.map((o) => {
                    const list = (demo[d.key] as string[]) ?? [];
                    return (
                      <label key={o} className="pq__check">
                        <input type="checkbox" checked={list.includes(o)}
                               onChange={(e) => setDemo({ ...demo, [d.key]: e.target.checked ? [...list, o] : list.filter((x) => x !== o) })} />
                        {o}
                      </label>
                    );
                  })}
                </div>
              ) : (
                <select value={(demo[d.key] as string) ?? ""} onChange={(e) => setDemo({ ...demo, [d.key]: e.target.value })}>
                  <option value="">Choose…</option>
                  {d.options.map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              )}
            </label>
          ))}
        </div>
      )}

      <div className="portal__actions">
        <button type="button" className="link-button" onClick={props.onCancel}>
          Back
        </button>
        <button className="btn btn--primary" disabled={busy || answered === 0}>
          {busy ? "Saving…" : "Submit my answers"}
        </button>
      </div>
    </form>
  );
}
