import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type StudioSession } from "../api";
import Chat from "../components/studio/Chat";
import FeedbackCard from "../components/studio/FeedbackCard";
import Huddle from "../components/studio/Huddle";
import LogicModelEditor from "../components/studio/LogicModelEditor";
import MetricsEditor from "../components/studio/MetricsEditor";
import { AlignmentCard } from "../components/studio/Sources";
import StartForm from "../components/studio/StartForm";
import Stepper, { stepLabel, type StageId } from "../components/studio/Stepper";
import Tutorial from "../components/studio/Tutorial";
import UploadOffer from "../components/studio/UploadOffer";
import { useAuth } from "../auth";
import { useApi } from "../useApi";

const TUTORIAL_KEY = "throughline.tutorialSeen";

function stageOf(session: StudioSession | null): StageId {
  if (!session) return "share";
  switch (session.phase) {
    case "intake":
    case "interview":
      return "interview";
    case "ready_to_draft":
    case "review":
      return "logic";
    case "ready_for_metrics":
    case "metrics_review":
      return "metrics";
    default:
      return "done";
  }
}

export default function LogicModel() {
  const { data: overview, error: overviewError } = useApi(api.studio);
  const [session, setSession] = useState<StudioSession | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTutorial, setShowTutorial] = useState(() => !localStorage.getItem(TUTORIAL_KEY));
  const [unsaved, setUnsaved] = useState(false);
  const autoRan = useRef<string | null>(null);
  const { me, refresh } = useAuth();
  const sessionIdRef = useRef<string | null>(null);
  sessionIdRef.current = session?.session_id ?? me?.studio_session_id ?? null;

  // Resume where you left off (sessions stay open for 7 days).
  useEffect(() => {
    // The organization's current Studio session is saved with the account, so it follows you anywhere.
    const id = me?.studio_session_id;
    if (id) api.getSession(id).then(setSession).catch(() => undefined);
  }, [me?.studio_session_id]);

  const act = useCallback(async (label: string, work: () => Promise<StudioSession>) => {
    setBusy(label);
    setError(null);
    try {
      const next = await work();
      setSession(next);
    } catch (e) {
      setError((e as Error).message);
      const id = sessionIdRef.current;
      if (id) api.getSession(id).then(setSession).catch(() => undefined); // resync after any error
    } finally {
      setBusy(null);
    }
  }, []);

  // Steps the team takes on its own: intake after sharing, drafting after Q5, metrics after approval.
  useEffect(() => {
    if (!session || busy || error) return;
    const key = `${session.session_id}:${session.phase}`;
    if (autoRan.current === key) return;
    const id = session.session_id;
    const auto: Partial<Record<StudioSession["phase"], [string, () => Promise<StudioSession>]>> = {
      intake: ["Your team is reading what you shared…", () => api.intake(id)],
      ready_to_draft: ["Your team is drafting your logic model…", () => api.draft(id)],
      ready_for_metrics: ["Your team is designing your measurement plan…", () => api.draftMetrics(id)],
    };
    const step = auto[session.phase];
    if (step) {
      autoRan.current = key;
      act(...step);
    }
  }, [session, busy, error, act]);

  const closeTutorial = () => {
    localStorage.setItem(TUTORIAL_KEY, "1");
    setShowTutorial(false);
  };

  const startOver = async () => {
    if (session && !confirm("End this session? Your team's working notes will be deleted.")) return;
    if (session) await api.endSession(session.session_id).catch(() => undefined);
    await refresh();
    autoRan.current = null;
    setSession(null);
    setError(null);
  };

  const stage: StageId = showTutorial ? "tutorial" : stageOf(session);
  const id = session?.session_id ?? "";
  const limits = overview?.limits ?? { answer_words: 200, feedback_words: 150 };
  const retry = () => {
    autoRan.current = null;
    setError(null);
  };
  const upload = (file: File) => act("Your team is reading your document…", () => api.addDocument(id, file));
  const skipUpload = () => act("", () => api.skipUpload(id));

  return (
    <div className="studio">
      <Stepper current={stage} onHelp={() => setShowTutorial(true)} />

      {overviewError && <p className="alert">Couldn't reach the server: {overviewError}</p>}
      {error && (
        <div className="alert alert--row">
          <span>{error}</span>
          <button className="btn btn--ghost btn--small" onClick={retry}>
            Try again
          </button>
        </div>
      )}

      {/* ------------------------------------------------ how it works */}
      {stage === "tutorial" && <Tutorial onClose={closeTutorial} starting={!session} />}

      {/* ------------------------------------------------ share */}
      {stage === "share" && (
        <div className="stage stage--narrow">
          <StartForm
            busy={!!busy}
            defaultOrgName={me?.org.name ?? ""}
            onStart={(form) =>
              act("Opening your session…", async () => {
                const next = await api.startSession(form);
                await refresh();
                return next;
              })
            }
          />
        </div>
      )}

      {/* ------------------------------------------------ five questions */}
      {stage === "interview" && session && (
        <div className="stage stage--split">
          <Chat
            session={session}
            busy={busy}
            wordLimit={limits.answer_words}
            onAnswer={(text) => act("Your team is thinking about your answer…", () => api.answer(id, text))}
            onUpload={upload}
            onSkipUpload={skipUpload}
          />
          <Huddle sessionId={id} working={!!busy} />
        </div>
      )}

      {/* ------------------------------------------------ logic model */}
      {stage === "logic" && session && (
        session.phase === "ready_to_draft" || !session.draft ? (
          <div className="stage stage--reveal">
            <p className="eyebrow">{stepLabel("logic")}</p>
            <h2>Your team is putting it together</h2>
            <p className="muted">
              The Team Lead writes a working draft, the whole team reviews it, then you see the improved version.
            </p>
            <Huddle sessionId={id} working={!!busy} large title="Drafting your logic model" />
          </div>
        ) : (
          <div className="stage stage--work">
            <div className="stage__main">
              <TeamMessage session={session} />
              <LogicModelEditor
                model={session.draft.logic_model}
                version={session.draft.version}
                stages={overview?.stages ?? []}
                busy={!!busy}
                onDirtyChange={setUnsaved}
                onSave={(m) => act("Saving your changes…", () => api.saveLogicModel(id, m))}
              />
              <AlignmentCard
                alignment={session.draft.alignment ?? []}
                sources={session.draft.sources ?? []}
                research={session.research}
              />
            </div>
            <aside className="stage__side">
              <ApproveCard
                title="Happy with it?"
                body="Approving locks in your logic model and moves you on to choosing metrics."
                label="Approve logic model"
                disabled={!!busy || unsaved}
                hint={unsaved ? "Save or undo your edits first." : undefined}
                onApprove={() => act("Saving…", () => api.approve(id))}
              />
              <FeedbackCard
                roundsLeft={session.revisions_left}
                wordLimit={limits.feedback_words}
                busy={!!busy}
                placeholder="For example: we don't do job placement, so take that out, and add our peer support groups."
                onSend={(text) => act("Your team is revising…", () => api.feedback(id, text))}
              />
              <Huddle sessionId={id} working={!!busy} />
              {!busy && (
                <div className="card card--quiet">
                  <UploadOffer session={session} onUpload={upload} onSkip={skipUpload} />
                </div>
              )}
            </aside>
          </div>
        )
      )}

      {/* ------------------------------------------------ metrics */}
      {stage === "metrics" && session && (
        session.phase === "ready_for_metrics" || !session.metric_draft ? (
          <div className="stage stage--reveal">
            <p className="eyebrow">{stepLabel("metrics")}</p>
            <h2>Your team is designing your measurement plan</h2>
            <p className="muted">
              The Funder Researcher is looking up the measures funders in your field use; then the team drafts and reviews
              the plan.
            </p>
            <Huddle sessionId={id} working={!!busy} large title="Designing your metrics" />
          </div>
        ) : (
          <div className="stage stage--work">
            <div className="stage__main">
              <TeamMessage session={session} />
              <MetricsEditor
                plan={session.metric_draft.plan}
                version={session.metric_draft.version}
                outcomes={[...(session.approved?.short_term_outcomes ?? []), ...(session.approved?.long_term_outcomes ?? [])]}
                busy={!!busy}
                onDirtyChange={setUnsaved}
                onSave={(p) => act("Saving your changes…", () => api.savePlan(id, p))}
              />
            </div>
            <aside className="stage__side">
              <ApproveCard
                title="Ready to measure?"
                body="Approving finishes this part. You'll get a PowerPoint with your logic model and plan."
                label="Approve measurement plan"
                disabled={!!busy || unsaved}
                hint={unsaved ? "Save or undo your edits first." : undefined}
                onApprove={() =>
                  act("Saving…", async () => {
                    const next = await api.approvePlan(id);
                    await refresh(); // the approved plan is now saved to the organization
                    return next;
                  })
                }
              />
              <FeedbackCard
                roundsLeft={session.metric_revisions_left}
                wordLimit={limits.feedback_words}
                busy={!!busy}
                placeholder="For example: our participants won't fill out more than 5 questions, and add a question about feeling safe."
                onSend={(text) => act("Your team is reworking the plan…", () => api.metricsFeedback(id, text))}
              />
              <Huddle sessionId={id} working={!!busy} />
            </aside>
          </div>
        )
      )}

      {/* ------------------------------------------------ done */}
      {stage === "done" && session && session.approved && session.approved_plan && (
        <div className="stage">
          <section className="card done">
            <div>
              <p className="eyebrow">{stepLabel("done")}</p>
              <h2>Nice work. Your logic model and measurement plan are ready.</h2>
              <p className="muted">
                The PowerPoint is fully editable. Your team's working notes have been deleted.
              </p>
            </div>
            <div className="done__actions">
              <Link className="btn btn--primary" to="/tools">
                Next: build your survey tools →
              </Link>
              <a className="btn btn--ghost" href={api.exportUrl(id)} download>
                Download PowerPoint
              </a>
              <button className="link-button" onClick={startOver}>
                Start a new session
              </button>
            </div>
          </section>
          <LogicModelEditor model={session.approved} version={session.draft?.version ?? 1} stages={overview?.stages ?? []} readOnly />
          <AlignmentCard alignment={session.draft?.alignment ?? []} sources={session.draft?.sources ?? []} research={null} />
          <MetricsEditor
            plan={session.approved_plan}
            version={session.metric_draft?.version ?? 1}
            outcomes={[]}
            readOnly
          />
        </div>
      )}

      {session && stage !== "done" && stage !== "tutorial" && (
        <p className="session-foot muted small">
          {session.org_name}
          {session.sector ? ` · ${session.sector}` : ""} · AI usage {session.usage.requests} calls,{" "}
          {(session.usage.input_tokens + session.usage.output_tokens).toLocaleString()} tokens ·{" "}
          <button className="link-button" onClick={startOver}>
            End session
          </button>
        </p>
      )}
    </div>
  );
}

function TeamMessage({ session }: { session: StudioSession }) {
  const last = [...session.transcript].reverse().find((l) => l.role === "team");
  if (!last) return null;
  return (
    <div className="team-message">
      <p>{last.text}</p>
      {session.team_notes.length > 0 && (
        <details>
          <summary>What the team considered</summary>
          <ul>
            {session.team_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function ApproveCard(props: {
  title: string;
  body: string;
  label: string;
  disabled: boolean;
  hint?: string;
  onApprove: () => void;
}) {
  return (
    <section className="card approve">
      <h3>{props.title}</h3>
      <p className="muted small">{props.body}</p>
      <button className="btn btn--primary" disabled={props.disabled} onClick={props.onApprove}>
        {props.label}
      </button>
      {props.hint && <p className="small hint">{props.hint}</p>}
    </section>
  );
}
