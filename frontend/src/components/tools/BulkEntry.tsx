import { useEffect, useState } from "react";
import { api, type InstrumentDetail, type InstrumentSummary, type ParticipantRow, type ToolsData } from "../../api";

type Row = { participant_code: string; answers: Record<string, string> };
const blankRows = (n: number): Row[] => Array.from({ length: n }, () => ({ participant_code: "", answers: {} }));

/** Staff enter many forms at once: paper surveys or staff assessments. One row per participant. */
export default function BulkEntry({ instruments, meta }: { instruments: InstrumentSummary[]; meta: ToolsData }) {
  const published = instruments.filter((i) => i.status === "published");
  const [toolId, setToolId] = useState<number | null>(published[0]?.id ?? null);
  const [wave, setWave] = useState<"pre" | "post">("pre");
  const [tool, setTool] = useState<InstrumentDetail | null>(null);
  const [people, setPeople] = useState<ParticipantRow[]>([]);
  const [rows, setRows] = useState<Row[]>(blankRows(5));
  const [result, setResult] = useState<string | null>(null);
  const [errors, setErrors] = useState<{ row: number; error: string }[]>([]);
  const [uploading, setUploading] = useState(false);
  const [sheetErrors, setSheetErrors] = useState<{ row: number; error: string }[]>([]);

  const upload = async (file: File) => {
    if (!toolId) return;
    setUploading(true);
    setResult(null);
    setSheetErrors([]);
    try {
      const res = await api.uploadResponses(toolId, wave, file);
      setSheetErrors(res.errors);
      setResult(`Saved ${res.saved} form${res.saved === 1 ? "" : "s"} from the spreadsheet.`);
    } catch (e) {
      setResult((e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    api.participants().then((d) => setPeople(d.participants));
  }, []);
  useEffect(() => {
    if (toolId) api.instrument(toolId).then(setTool);
  }, [toolId]);

  if (published.length === 0) return <p className="empty card">Publish a survey tool first; then you can enter responses here.</p>;
  const qs = (tool?.questions ?? []).filter((q) => !q.hidden && q.waves.includes(wave));
  const setCell = (r: number, qid: string, v: string) =>
    setRows(rows.map((row, i) => (i === r ? { ...row, answers: { ...row.answers, [qid]: v } } : row)));

  const save = async () => {
    if (!toolId) return;
    setResult(null);
    const payload = rows.filter((r) => r.participant_code.trim()).map((r) => ({
      participant_code: r.participant_code,
      answers: Object.fromEntries(Object.entries(r.answers).filter(([, v]) => v !== "")),
    }));
    try {
      const res = await api.enterResponses(toolId, wave, payload);
      setErrors(res.errors);
      setResult(`Saved ${res.saved} form${res.saved === 1 ? "" : "s"}.`);
      if (res.errors.length === 0) setRows(blankRows(5));
    } catch (e) {
      setResult((e as Error).message);
    }
  };

  return (
    <section className="card bulk">
      <div className="inline-form">
        <label className="field field--inline">
          <span>Survey tool</span>
          <select value={toolId ?? ""} onChange={(e) => setToolId(Number(e.target.value))}>
            {published.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </label>
        <div className="segmented">
          {(["pre", "post"] as const).map((w) => (
            <button key={w} type="button" className={wave === w ? "is-on" : ""} onClick={() => setWave(w)}>
              {w === "pre" ? "Pre (start)" : "Post (end)"}
            </button>
          ))}
        </div>
      </div>
      <div className="numbers-upload bulk__excel">
        <strong>Have a lot of forms? Use Excel.</strong>
        <p className="muted small">
          Download a sheet with every participant code and this survey's {wave === "pre" ? "pre" : "post"} questions (answers
          you've already entered are filled in). Fill in the yellow cells using the dropdowns, save, and upload it.
        </p>
        <div className="inline-form">
          {toolId && <a className="btn btn--secondary btn--small" href={api.responsesTemplate(toolId, wave)} download>Download Excel template</a>}
          <label className="btn btn--primary btn--small file-button">
            {uploading ? "Uploading…" : "Upload filled template"}
            <input type="file" accept=".xlsx" hidden disabled={uploading} onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (f) upload(f);
            }} />
          </label>
        </div>
      </div>
      <p className="muted small">Or type forms in below. One row per participant. Entering a form again for the same code and wave replaces it.</p>

      <datalist id="codes">{people.map((p) => <option key={p.id} value={p.code} />)}</datalist>
      <div className="bulk__scroll">
        <table className="table bulk__table">
          <thead>
            <tr>
              <th>Code</th>
              {qs.map((q) => <th key={q.id} title={q.text}>{q.text.length > 48 ? q.text.slice(0, 46) + "…" : q.text}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => (
              <tr key={r} className={errors.some((e) => e.row === r + 1) ? "has-error" : ""}>
                <td>
                  <input list="codes" value={row.participant_code} placeholder="Code"
                         onChange={(e) => setRows(rows.map((x, i) => (i === r ? { ...x, participant_code: e.target.value.toUpperCase() } : x)))} />
                </td>
                {qs.map((q) => {
                  const opts = meta.scales[q.scale].options;
                  const base = q.scale === "scale_0_10" || q.scale === "yes_no" ? 0 : 1;
                  return (
                    <td key={q.id}>
                      {q.scale === "choice" ? (
                        <select value={row.answers[q.id] ?? ""} onChange={(e) => setCell(r, q.id, e.target.value)}>
                          <option value="">–</option>
                          {(q.options ?? []).map((o) => <option key={o} value={o}>{o}</option>)}
                        </select>
                      ) : q.scale === "multi_choice" ? (
                        <input value={row.answers[q.id] ?? ""} placeholder="Choice; choice" title={(q.options ?? []).join("; ")}
                               onChange={(e) => setCell(r, q.id, e.target.value)} />
                      ) : opts ? (
                        <select value={row.answers[q.id] ?? ""} onChange={(e) => setCell(r, q.id, e.target.value)}>
                          <option value="">–</option>
                          {opts.map((o, i) => <option key={o} value={String(i + base)}>{o}</option>)}
                        </select>
                      ) : (
                        <input type={q.scale === "number" ? "number" : "text"} value={row.answers[q.id] ?? ""}
                               onChange={(e) => setCell(r, q.id, e.target.value)} />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="inline-form">
        <button className="link-button small" onClick={() => setRows([...rows, ...blankRows(5)])}>+ 5 more rows</button>
        <button className="btn btn--primary" onClick={save}>Save all</button>
        {result && <span className="small">{result}</span>}
      </div>
      {sheetErrors.length > 0 && (
        <ul className="alert small">{sheetErrors.map((e, i) => <li key={i}>Spreadsheet row {e.row}: {e.error}</li>)}</ul>
      )}
      {errors.length > 0 && <ul className="alert small">{errors.map((e) => <li key={e.row}>Row {e.row}: {e.error}</li>)}</ul>}
    </section>
  );
}
