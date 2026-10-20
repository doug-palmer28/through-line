import { useEffect, useState } from "react";
import { api, type IndicatorRow } from "../../api";

/** Numbers the organization already has (dollars spent, event attendance): staff enter them, no survey needed. */
export default function ProgramNumbers() {
  const [rows, setRows] = useState<IndicatorRow[]>([]);
  const [draft, setDraft] = useState<Record<number, { period: string; value: string; note: string }>>({});
  const [adding, setAdding] = useState({ name: "", unit: "", description: "" });
  const [error, setError] = useState<string | null>(null);
  const thisMonth = new Date().toISOString().slice(0, 7);
  const [month, setMonth] = useState(thisMonth);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ saved: number; errors: { line: number; error: string }[]; months: string[] } | null>(null);

  useEffect(() => {
    api.indicators().then((d) => setRows(d.indicators)).catch((e: Error) => setError(e.message));
  }, []);

  const upload = async (file: File) => {
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.uploadNumbers(file);
      setRows(res.indicators);
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  const save = async (ind: IndicatorRow) => {
    const d = draft[ind.id];
    if (!d || d.value === "") return;
    setError(null);
    try {
      const res = await api.addEntries(ind.id, [{ period: `${d.period || thisMonth}-01`, value: Number(d.value), note: d.note }]);
      setRows(res.indicators);
      setDraft({ ...draft, [ind.id]: { period: d.period, value: "", note: "" } });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="stack">
      <p className="muted">
        Some results come from your own records rather than participants. Enter them here, by month, and they appear on the dashboard.
      </p>
      {error && <p className="alert small">{error}</p>}

      <section className="card numbers-upload">
        <h3>Fill in a whole month at once</h3>
        <p className="muted small">
          Download the Excel template for a month: it lists every number you track. Type the values in the yellow column,
          save, and upload it here. Each value replaces that number's entry for the month, so re-uploading a corrected file is safe.
        </p>
        <div className="inline-form">
          <label className="field field--inline"><span>Month</span>
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value || thisMonth)} />
          </label>
          <a className="btn btn--secondary btn--small" href={api.numbersTemplate(month)} download>Download template</a>
          <label className="btn btn--primary btn--small file-button">
            {uploading ? "Uploading…" : "Upload filled template"}
            <input type="file" accept=".xlsx" hidden disabled={uploading} onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (f) upload(f);
            }} />
          </label>
        </div>
        {result && (
          <div className={result.errors.length ? "alert alert--soft small" : "notice small"}>
            <p>
              Saved {result.saved} {result.saved === 1 ? "number" : "numbers"}
              {result.months.length > 0 && ` for ${result.months.join(", ")}`}. They now appear on every chart and report that uses them.
            </p>
            {result.errors.length > 0 && (
              <ul>{result.errors.map((er) => <li key={er.line}>Row {er.line}: {er.error}</li>)}</ul>
            )}
          </div>
        )}
      </section>

      {rows.map((ind) => {
        const d = draft[ind.id] ?? { period: thisMonth, value: "", note: "" };
        const total = ind.entries.reduce((s, e) => s + e.value, 0);
        return (
          <section key={ind.id} className="card numbers">
            <div className="numbers__head">
              <div>
                <h3>{ind.name}</h3>
                <p className="muted small">{ind.description || (ind.source === "plan" ? "From your measurement plan" : "Added by staff")}</p>
              </div>
              <span className="numbers__total">{total.toLocaleString()} {ind.unit}</span>
            </div>
            <div className="inline-form">
              <label className="field field--inline"><span>Month</span>
                <input type="month" value={d.period} onChange={(e) => setDraft({ ...draft, [ind.id]: { ...d, period: e.target.value } })} />
              </label>
              <label className="field field--inline"><span>Value {ind.unit && `(${ind.unit})`}</span>
                <input type="number" min={0} value={d.value} onChange={(e) => setDraft({ ...draft, [ind.id]: { ...d, value: e.target.value } })} />
              </label>
              <label className="field field--inline field--grow"><span>Note (optional)</span>
                <input value={d.note} maxLength={300} onChange={(e) => setDraft({ ...draft, [ind.id]: { ...d, note: e.target.value } })} />
              </label>
              <button className="btn btn--primary btn--small" onClick={() => save(ind)}>Add</button>
            </div>
            {ind.entries.length > 0 && (
              <table className="table">
                <thead><tr><th>Month</th><th>Value</th><th>Note</th><th /></tr></thead>
                <tbody>
                  {ind.entries.map((e) => (
                    <tr key={e.id}>
                      <td>{e.period.slice(0, 7)}</td>
                      <td>{e.value.toLocaleString()}</td>
                      <td className="muted">{e.note}</td>
                      <td><button className="icon-button" title="Delete" aria-label="Delete" onClick={async () => setRows((await api.deleteEntry(e.id)).indicators)}>×</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        );
      })}

      <section className="card">
        <h3>Track another number</h3>
        <div className="inline-form">
          <label className="field field--inline field--grow"><span>What is it?</span>
            <input value={adding.name} placeholder="e.g. Dollars spent on move-in kits" onChange={(e) => setAdding({ ...adding, name: e.target.value })} />
          </label>
          <label className="field field--inline"><span>Unit</span>
            <input value={adding.unit} placeholder="$, people, events" onChange={(e) => setAdding({ ...adding, unit: e.target.value })} />
          </label>
          <button className="btn btn--secondary btn--small" disabled={!adding.name.trim()} onClick={async () => {
            setRows((await api.addIndicator(adding)).indicators);
            setAdding({ name: "", unit: "", description: "" });
          }}>Add number</button>
        </div>
      </section>
    </div>
  );
}
