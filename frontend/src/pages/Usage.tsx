import { useEffect, useState } from "react";
import { api, type TokenTotals, type UsageReport } from "../api";

const n = (v: number) => v.toLocaleString();

function Rows({ rows, label }: { rows: (TokenTotals & { key: string })[]; label: string }) {
  if (!rows.length) return <p className="empty">No AI use yet.</p>;
  return (
    <table className="table">
      <thead><tr><th>{label}</th><th>Requests</th><th>Tokens in</th><th title="Part of the input the model provider had cached (billed at a tenth of the price)">of which cached</th><th>Tokens out</th><th>Total tokens</th></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.key}><td>{r.key}</td><td>{n(r.requests)}</td><td>{n(r.input_tokens)}</td><td className="muted">{n(r.cached_input_tokens ?? 0)}</td><td>{n(r.output_tokens)}</td><td><strong>{n(r.total_tokens)}</strong></td></tr>
        ))}
      </tbody>
    </table>
  );
}

/** How much AI this person and their organization have used, and what's left of each allowance. */
export default function Usage() {
  const [u, setU] = useState<UsageReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.usage().then(setU).catch((e: Error) => setError(e.message));
  }, []);

  if (!u) return error ? <p className="alert">{error}</p> : <p className="muted">Loading…</p>;
  return (
    <div className="studio">
      <div className="page-title">
        <p className="eyebrow">Your account</p>
        <h1>AI usage</h1>
        <p className="muted">Every time an AI agent works for you, we record the tokens (the units AI models are billed in). Each tool also has a limit, so costs stay predictable.</p>
      </div>
      <section className="tiles">
        <div className="tile"><span className="tile__value">{n(u.me.total_tokens)}</span><span className="tile__label">tokens you've used</span></div>
        <div className="tile"><span className="tile__value">{n(u.organization.total_tokens)}</span><span className="tile__label">tokens your organization has used</span></div>
        <div className="tile"><span className="tile__value">{n(u.organization.requests)}</span><span className="tile__label">AI requests in total</span></div>
      </section>

      <section className="card stack">
        <h3>What's left</h3>
        <table className="table">
          <thead><tr><th>Tool</th><th>Used</th><th>Limit</th><th /></tr></thead>
          <tbody>
            {u.allowances.map((a) => (
              <tr key={a.feature}>
                <td>{a.feature}</td>
                <td>{a.used ?? "–"}</td>
                <td>{a.limit === null ? "No limit" : `${a.limit} per ${a.per}`}</td>
                <td className="muted small">{a.note ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small">Need more? Contact Through Line and we can add to your allowance.</p>
      </section>

      <div className="charts">
        <section className="card stack"><h3>Your use, by tool</h3><Rows rows={u.me.by_feature} label="Tool" /></section>
        <section className="card stack"><h3>Your organization, by tool</h3><Rows rows={u.organization.by_feature} label="Tool" /></section>
        <section className="card stack"><h3>By month</h3><Rows rows={u.organization.by_month} label="Month" /></section>
        {u.organization.by_person && (
          <section className="card stack"><h3>By person</h3><Rows rows={u.organization.by_person} label="Staff member" /></section>
        )}
      </div>
    </div>
  );
}
