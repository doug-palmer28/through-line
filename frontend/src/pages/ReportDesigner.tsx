import { useEffect, useState } from "react";
import { api, type Brand, type ReportOptions, type ReportRun } from "../api";
import PrivacyPanel from "../components/PrivacyPanel";
import { when } from "../format";

const GROUPS: { key: string; label: string }[] = [
  { key: "outcomes", label: "Outcomes" },
  { key: "people", label: "Who we serve" },
  { key: "program", label: "Program activity" },
];

/** Step 4: tell the Report Designer about your brand, pick what to include, and get a funder deck + one-pager. */
export default function ReportDesigner() {
  const [opts, setOpts] = useState<ReportOptions | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reportOptions().then(setOpts).catch((e: Error) => setError(e.message));
  }, []);

  if (!opts) return error ? <p className="alert">{error}</p> : <p className="muted">Loading…</p>;
  const shell = opts.runs[0];
  const replaceShell = (run: ReportRun) => setOpts({ ...opts, runs: [run, ...opts.runs.slice(1)] });

  return (
    <div className="studio">
      <div className="page-title">
        <p className="eyebrow">Step 4 · Tell the story</p>
        <h1>Impact report designer</h1>
        <p className="muted">
          Choose what to show, tell the designer about your brand, and it designs a 10–15 minute funder presentation
          (with speaker notes) and a one-page impact flyer. You get one design and one round of feedback. After that,
          the report keeps itself up to date: every number refreshes from your latest data, for free.
        </p>
      </div>
      {error && <p className="alert small">{error}</p>}
      <div className="designer">
        <div className="stack">
          <BrandForm opts={opts} onSaved={setOpts} onError={setError} />
          {opts.designs_left > 0 ? (
            <BuildForm opts={opts} onBuilt={(run) => setOpts({ ...opts, designs_left: 0, runs: [run, ...opts.runs] })} onError={setError} />
          ) : (
            shell && <ShellControls run={shell} onChange={replaceShell} onError={setError} />
          )}
        </div>
        <div className="stack">
          {!shell ? (
            <section className="card card--quiet">
              <h3>Your materials appear here</h3>
              <p className="muted small">The design makes a PowerPoint deck and a PDF flyer you can download and edit.</p>
            </section>
          ) : (
            <RunView run={shell} brand={opts.brand} hasLogo={opts.has_logo} />
          )}
          {opts.runs.length > 1 && (
            <section className="card">
              <h3>Earlier versions</h3>
              <ul className="runs">
                {opts.runs.slice(1).map((r) => (
                  <li key={r.id}>
                    <span><strong>{r.draft.deck_title}</strong> <span className="muted small">· {when(r.created_at)}</span></span>
                    <span className="downloads">
                      <a className="link-button small" href={api.deckUrl(r.id)} download>Deck ↓</a>
                      <a className="link-button small" href={api.onePagerUrl(r.id)} download>One-pager ↓</a>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================ brand

function BrandForm({ opts, onSaved, onError }: { opts: ReportOptions; onSaved: (o: ReportOptions) => void; onError: (e: string | null) => void }) {
  const [brand, setBrand] = useState<Brand>(opts.brand);
  const [logo, setLogo] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(opts.has_logo ? `${api.logoUrl}?v=${Date.now()}` : null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const set = (k: keyof Brand, v: string) => { setBrand({ ...brand, [k]: v }); setSaved(false); };

  const save = async () => {
    setSaving(true);
    onError(null);
    const form = new FormData();
    Object.entries(brand).forEach(([k, v]) => form.append(k, v ?? ""));
    if (logo) form.append("logo", logo);
    try {
      onSaved(await api.saveBrand(form));
      setLogo(null);
      setSaved(true);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const color = (k: "primary" | "secondary" | "accent", label: string) => (
    <label className="field swatch-field"><span>{label}</span>
      <span className="swatch-input">
        <input type="color" value={brand[k] || "#ffffff"} onChange={(e) => set(k, e.target.value)} aria-label={`${label} color`} />
        <input value={brand[k] ?? ""} placeholder="#1F4E5F" maxLength={7} onChange={(e) => set(k, e.target.value)} />
      </span>
    </label>
  );

  return (
    <section className="card stack">
      <div>
        <h3>1 · Your brand</h3>
        <p className="muted small">Saved for every report. Describe your style in your own words; the designer reads it.</p>
      </div>
      <label className="field"><span>Design standards</span>
        <textarea rows={3} maxLength={2000} value={brand.standards ?? ""}
          placeholder="e.g. Warm and hopeful, never clinical. Deep teal with gold accents. Lots of white space. Photos of homes, not people."
          onChange={(e) => set("standards", e.target.value)} />
      </label>
      <div className="brand-colors">
        {color("primary", "Main color")}
        {color("secondary", "Second color")}
        {color("accent", "Accent")}
      </div>
      <div className="brand-row">
        <label className="field"><span>Heading font</span>
          <select value={brand.heading_font ?? ""} onChange={(e) => set("heading_font", e.target.value)}>
            <option value="">Let the designer pick</option>
            {opts.fonts.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </label>
        <label className="field"><span>Body font</span>
          <select value={brand.body_font ?? ""} onChange={(e) => set("body_font", e.target.value)}>
            <option value="">Let the designer pick</option>
            {opts.fonts.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </label>
      </div>
      <div className="brand-row">
        <label className="field"><span>Tagline</span>
          <input maxLength={120} value={brand.tagline ?? ""} placeholder="Home starts here" onChange={(e) => set("tagline", e.target.value)} />
        </label>
        <label className="field"><span>Contact line (for the flyer)</span>
          <input maxLength={160} value={brand.contact ?? ""} placeholder="yourorg.org · info@yourorg.org" onChange={(e) => set("contact", e.target.value)} />
        </label>
      </div>
      <div className="logo-row">
        <div className="logo-box">{preview ? <img src={preview} alt="Your logo" /> : <span className="muted small">No logo</span>}</div>
        <label className="btn btn--ghost btn--small file-button">
          {preview ? "Replace logo" : "Upload logo"}
          <input type="file" accept="image/png,image/jpeg" hidden onChange={(e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            setLogo(f);
            setPreview(URL.createObjectURL(f));
            setSaved(false);
          }} />
        </label>
        <span className="muted small">PNG or JPG, under 2 MB.</span>
      </div>
      <div className="row-end">
        {saved && <span className="muted small">Saved.</span>}
        <button className="btn btn--secondary btn--small" disabled={saving} onClick={save}>{saving ? "Saving…" : "Save brand"}</button>
      </div>
    </section>
  );
}

// ============================================================ build

function BuildForm({ opts, onBuilt, onError }: { opts: ReportOptions; onBuilt: (r: ReportRun) => void; onError: (e: string | null) => void }) {
  const [picked, setPicked] = useState<Set<string>>(() => new Set(opts.charts.filter((c) => c.group === "outcomes").map((c) => c.id)));
  const [audience, setAudience] = useState(opts.audiences[0]);
  const [minutes, setMinutes] = useState(12);
  const [quotes, setQuotes] = useState(opts.quotes_available > 0);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);

  const toggle = (id: string) => {
    const next = new Set(picked);
    if (next.has(id)) next.delete(id); else next.add(id);
    setPicked(next);
  };

  const build = async () => {
    setBusy(true);
    onError(null);
    try {
      onBuilt(await api.buildReport({ chart_ids: [...picked], audience, minutes, include_quotes: quotes, notes }));
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card stack">
      <div>
        <h3>2 · What to include</h3>
        <p className="muted small">Pick the results you want funders to see. The designer only uses what you check.</p>
      </div>
      {opts.charts.length === 0 && <p className="empty">No charts yet. Collect some survey data or program numbers first.</p>}
      {GROUPS.map((g) => {
        const items = opts.charts.filter((c) => c.group === g.key);
        if (!items.length) return null;
        return (
          <fieldset key={g.key} className="pick-group">
            <legend>{g.label}</legend>
            {items.map((c) => (
              <label key={c.id} className="pick">
                <input type="checkbox" checked={picked.has(c.id)} onChange={() => toggle(c.id)} />
                <span>{c.title}</span>
              </label>
            ))}
          </fieldset>
        );
      })}
      <div className="brand-row">
        <label className="field"><span>Audience</span>
          <select value={audience} onChange={(e) => setAudience(e.target.value)}>
            {opts.audiences.map((a) => <option key={a}>{a}</option>)}
          </select>
        </label>
        <label className="field"><span>Talk length: {minutes} minutes</span>
          <input type="range" min={8} max={20} value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} />
        </label>
      </div>
      <label className="pick">
        <input type="checkbox" checked={quotes} disabled={opts.quotes_available === 0} onChange={(e) => setQuotes(e.target.checked)} />
        <span>Use participant quotes ({opts.quotes_available} available; contact details are removed before the designer sees them)</span>
      </label>
      <label className="field"><span>Anything else the designer should know? (optional)</span>
        <textarea rows={2} maxLength={1000} value={notes} placeholder="e.g. This is for our renewal ask with the Hartwell Foundation; lead with housing stability."
          onChange={(e) => setNotes(e.target.value)} />
      </label>
      <p className="muted small">You get one design, so choose carefully. You'll have one round of feedback afterwards.</p>
      <div className="row-end">
        {busy && <span className="muted small">Designing and running the privacy check… this takes a minute or two.</span>}
        <button className="btn btn--primary" disabled={busy || picked.size === 0} onClick={build}>
          {busy ? "Building…" : "Design deck + one-pager"}
        </button>
      </div>
    </section>
  );
}

// ============================================================ the shell: refresh (free), one feedback round, privacy check

function ShellControls({ run, onChange, onError }: { run: ReportRun; onChange: (r: ReportRun) => void; onError: (e: string | null) => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState("");
  const words = feedback.trim() ? feedback.trim().split(/\s+/).length : 0;

  const act = async (label: string, fn: () => Promise<ReportRun>) => {
    setBusy(label);
    onError(null);
    try {
      onChange(await fn());
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <section className="card stack">
      <div>
        <h3>Your report</h3>
        <p className="muted small">
          {run.live_numbers.length} numbers in this report update from your latest data every time you open or download it.
          Last refreshed {when(run.numbers_as_of)}.
        </p>
      </div>
      {run.missing_numbers.length > 0 && (
        <p className="alert alert--soft small">
          {run.missing_numbers.length} number{run.missing_numbers.length === 1 ? "" : "s"} the design uses no longer exist in your
          data (shown as “–”): {run.missing_numbers.join(", ")}. Edit those lines in the downloaded file.
        </p>
      )}
      <div className="downloads">
        <button className="btn btn--ghost btn--small" disabled={!!busy} onClick={() => act("Refreshing…", () => api.refreshReport(run.id))}>
          Refresh with latest data
        </button>
        <button className="btn btn--ghost btn--small" disabled={!!busy} onClick={() => act("The Privacy Reviewer is reading…", () => api.checkReportPrivacy(run.id))}>
          Run privacy check
        </button>
      </div>
      {busy && <p className="muted small">{busy}</p>}

      <div className="feedback-round">
        <h4>One round of feedback</h4>
        {run.revisions_left > 0 ? (
          <>
            <p className="muted small">Tell the designer everything you'd like changed. This is the last AI pass, so include it all.</p>
            <textarea rows={3} value={feedback} maxLength={4000}
              placeholder="e.g. Lead with housing stability, cut the second chart slide, and make the ask about renewing rent assistance."
              onChange={(e) => setFeedback(e.target.value)} />
            <div className="row-end">
              <span className={`small ${words > 150 ? "hint" : "muted"}`}>{words} / 150 words</span>
              <button className="btn btn--primary btn--small" disabled={!!busy || !words || words > 150}
                onClick={() => act("Revising your report and re-checking privacy…", () => api.reviseReport(run.id, feedback))}>
                Send feedback
              </button>
            </div>
          </>
        ) : (
          <p className="muted small">
            Feedback round used{run.feedback.length ? `: “${run.feedback[run.feedback.length - 1].text}”` : ""}. You can still edit the
            downloaded PowerPoint, and the numbers keep refreshing.
          </p>
        )}
      </div>
    </section>
  );
}

// ============================================================ results

function RunView({ run, brand, hasLogo }: { run: ReportRun; brand: Brand; hasLogo: boolean }) {
  const d = run.draft;
  const p = run.privacy;
  const primary = brand.primary || d.design.primary;
  const secondary = brand.secondary || d.design.secondary;
  const accent = brand.accent || d.design.accent;

  return (
    <>
      <section className="card stack">
        <div className="numbers__head">
          <div>
            <p className="eyebrow">Your report · {run.request.audience} · {run.request.minutes} min</p>
            <h3>{d.deck_title}</h3>
            <p className="muted small">{d.deck_subtitle}</p>
          </div>
          <div className="downloads">
            <a className="btn btn--primary btn--small" href={api.deckUrl(run.id)} download>Deck (PowerPoint)</a>
            <a className="btn btn--secondary btn--small" href={api.onePagerUrl(run.id)} download>One-pager (PDF)</a>
          </div>
        </div>
        <PrivacyPanel privacy={p} />
      </section>

      <section className="card stack">
        <h3>One-pager preview</h3>
        <div className="flyer" style={{ fontFamily: d.design.body_font }}>
          <div className="flyer__band" style={{ background: primary }}>
            {hasLogo && <img src={api.logoUrl} alt="" className="flyer__logo" />}
            <div>
              <div className="flyer__head" style={{ fontFamily: d.design.heading_font }}>{d.one_pager.headline}</div>
              <div className="flyer__sub">{d.one_pager.subhead}</div>
            </div>
          </div>
          <div className="flyer__stats">
            {d.one_pager.stats.map((s, i) => (
              <div key={i} className="flyer__stat" style={{ borderTopColor: [secondary, accent, primary][i % 3] }}>
                <span className="flyer__value" style={{ color: primary }}>{s.value}</span>
                <span className="small">{s.label}</span>
              </div>
            ))}
          </div>
          <p className="small flyer__story">{d.one_pager.story}</p>
          {d.one_pager.quote && <blockquote className="flyer__quote" style={{ borderLeftColor: accent }}>“{d.one_pager.quote}”</blockquote>}
          <div className="flyer__cta" style={{ background: secondary }}>{d.one_pager.call_to_action}</div>
        </div>
      </section>

      <section className="card stack">
        <h3>Slide outline <span className="muted small">· {d.slides.length} slides, speaker notes included</span></h3>
        <ol className="outline">
          {d.slides.map((s, i) => (
            <li key={i}>
              <details>
                <summary><span className="tag">{s.layout}</span> {s.headline}</summary>
                {s.body.length > 0 && <ul className="small">{s.body.map((b, j) => <li key={j}>{b}</li>)}</ul>}
                {s.stats.length > 0 && <p className="small">{s.stats.map((st) => `${st.value} ${st.label}`).join(" · ")}</p>}
                {s.quote && <p className="small"><em>“{s.quote}”</em></p>}
                <p className="small muted"><strong>Say:</strong> {s.speaker_notes}</p>
              </details>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}
