import { useEffect, useState } from "react";
import { api, type InstrumentSummary, type NewCredential, type ParticipantRow } from "../../api";

/** Participant codes + PINs. PINs are shown once (they're stored only as hashes). No names are ever entered. */
export default function ParticipantsPanel({ instruments }: { instruments: InstrumentSummary[] }) {
  const [rows, setRows] = useState<ParticipantRow[]>([]);
  const [count, setCount] = useState(5);
  const [fresh, setFresh] = useState<NewCredential[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.participants().then((d) => setRows(d.participants)).catch((e: Error) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  const csv = (creds: NewCredential[]) => {
    const text = "code,pin\n" + creds.map((c) => `${c.code},${c.pin}`).join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: "participant_codes.csv" });
    a.click();
    URL.revokeObjectURL(url);
  };
  const surveys = instruments.filter((i) => i.status === "published");

  return (
    <div className="stack">
      <section className="card">
        <h3>Add participants</h3>
        <p className="muted small">
          Each participant gets a code and a 6-digit PIN to sign in at <strong>/participant</strong>. Keep any list that links
          codes to names in your own secure files, not here.
        </p>
        <div className="inline-form">
          <label className="field field--inline">
            <span>How many</span>
            <input type="number" min={1} max={100} value={count} onChange={(e) => setCount(Number(e.target.value))} />
          </label>
          <button className="btn btn--primary" onClick={async () => {
            setError(null);
            try {
              setFresh((await api.addParticipants(count)).created);
              load();
            } catch (e) {
              setError((e as Error).message);
            }
          }}>Create codes</button>
        </div>
        {error && <p className="alert small">{error}</p>}
      </section>

      {fresh && (
        <section className="card creds">
          <h3>New sign-in details: copy them now</h3>
          <p className="notice small">For security, PINs are shown only once. Download or print them before leaving this page.</p>
          <table className="table">
            <thead><tr><th>Code</th><th>PIN</th></tr></thead>
            <tbody>{fresh.map((c) => <tr key={c.code}><td><code>{c.code}</code></td><td><code>{c.pin}</code></td></tr>)}</tbody>
          </table>
          <div className="inline-form">
            <button className="btn btn--secondary btn--small" onClick={() => csv(fresh)}>Download CSV</button>
            <button className="btn btn--ghost btn--small" onClick={() => window.print()}>Print</button>
            <button className="link-button small" onClick={() => setFresh(null)}>I've saved them</button>
          </div>
        </section>
      )}

      <section className="card">
        <h3>Participants ({rows.length})</h3>
        {rows.length === 0 ? (
          <p className="empty">No participants yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Added</th>
                {surveys.map((s) => <th key={s.id}>{s.name}</th>)}
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td><code>{p.code}</code></td>
                  <td>{p.created_at}</td>
                  {surveys.map((s) => (
                    <td key={s.id}>
                      {(["pre", "post"] as const).map((w) => (
                        <span key={w} className={`chip ${p.completed.includes(`${s.id}:${w}`) ? "chip--done" : ""}`}>
                          {w} {p.completed.includes(`${s.id}:${w}`) ? "✓" : "–"}
                        </span>
                      ))}
                    </td>
                  ))}
                  <td>
                    <button className="link-button small" onClick={async () => setFresh([await api.resetPin(p.id)])}>
                      Reset PIN
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
