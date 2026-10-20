import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ToolsData } from "../api";
import BulkEntry from "../components/tools/BulkEntry";
import InstrumentEditor from "../components/tools/InstrumentEditor";
import ParticipantsPanel from "../components/tools/ParticipantsPanel";
import ProgramNumbers from "../components/tools/ProgramNumbers";

const TABS = [
  { id: "surveys", label: "Surveys" },
  { id: "participants", label: "Participants" },
  { id: "entry", label: "Enter responses" },
  { id: "numbers", label: "Program numbers" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export default function Tools() {
  const [data, setData] = useState<ToolsData | null>(null);
  const [tab, setTab] = useState<Tab>("surveys");
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api.tools().then(setData).catch((e: Error) => setError(e.message)), []);
  useEffect(() => {
    load();
  }, [load]);

  if (!data) return error ? <p className="alert">{error}</p> : <p className="muted">Loading…</p>;

  return (
    <div className="studio">
      <div className="page-title">
        <p className="eyebrow">Step 2 · Collect</p>
        <h1>Survey tools</h1>
        <p className="muted">Built from the questions you chose in your measurement plan. Refine them, publish, then collect pre and post.</p>
      </div>
      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? "is-on" : ""}
                  onClick={() => { setTab(t.id); setEditing(null); }}>
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "surveys" && editing !== null && (
        <InstrumentEditor id={editing} meta={data} onBack={() => setEditing(null)} onChanged={load} />
      )}

      {tab === "surveys" && editing === null && (
        !data.has_plan ? (
          <section className="card empty-state">
            <h3>First, finish your logic model and metrics</h3>
            <p className="muted">Your survey questions come straight from the measurement plan you approve.</p>
            <Link className="btn btn--primary" to="/logic-model">Go to the Logic Model Studio</Link>
          </section>
        ) : data.instruments.length === 0 ? (
          <section className="card empty-state">
            <h3>Build your survey tools</h3>
            <p className="muted">We'll turn your approved metrics into ready-to-edit surveys: participant surveys, staff assessments, and the program numbers you'll enter yourself.</p>
            {error && <p className="alert small">{error}</p>}
            <button className="btn btn--primary" disabled={busy} onClick={async () => {
              setBusy(true);
              setError(null);
              try { setData(await api.buildTools()); } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
            }}>{busy ? "Building…" : "Build from my metrics"}</button>
          </section>
        ) : (
          <div className="tool-grid">
            {data.instruments.map((i) => (
              <button key={i.id} className="card tool-card" onClick={() => setEditing(i.id)}>
                <span className={`chip ${i.status === "published" ? "chip--done" : ""}`}>{i.status === "published" ? "Published" : "Draft"}</span>
                <h3>{i.name}</h3>
                <p className="muted small">{i.method === "participant_survey" ? "Participant survey" : "Staff assessment"} · {i.when}</p>
                <p className="small">{i.questions} questions{i.hidden ? ` (${i.hidden} hidden)` : ""}</p>
                <p className="small"><strong>{i.responses.pre}</strong> pre · <strong>{i.responses.post}</strong> post responses</p>
                <span className="link-button small">{i.reviewed ? "Edit · reviewed ✓" : "Edit and review →"}</span>
              </button>
            ))}
          </div>
        )
      )}

      {tab === "participants" && <ParticipantsPanel instruments={data.instruments} />}
      {tab === "entry" && <BulkEntry instruments={data.instruments} meta={data} />}
      {tab === "numbers" && <ProgramNumbers />}
    </div>
  );
}
