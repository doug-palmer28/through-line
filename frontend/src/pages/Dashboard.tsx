import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type DashboardData } from "../api";
import { ChartCard } from "../components/charts/Charts";

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch((e: Error) => setError(e.message));
  }, []);

  if (!data) return error ? <p className="alert">{error}</p> : <p className="muted">Loading…</p>;
  const h = data.headline;
  const outcomes = data.charts.filter((c) => c.group === "outcomes");
  const answers = data.charts.filter((c) => c.group === "answers");
  const people = data.charts.filter((c) => c.group === "people");
  const program = data.charts.filter((c) => c.group === "program");
  const empty = data.charts.length === 0;

  return (
    <div className="studio">
      <div className="page-title page-title--row">
        <div>
          <p className="eyebrow">Step 3 · Share</p>
          <h1>Impact dashboard</h1>
          <p className="muted">Built from your surveys and program numbers as they come in.</p>
        </div>
        <div className="downloads">
          <a className="btn btn--ghost btn--small" href={api.dataXlsx} download>All data (Excel)</a>
          <a className="btn btn--ghost btn--small" href={api.reportPptx} download>Quick report (PowerPoint)</a>
          <Link className="btn btn--primary btn--small" to="/report">Design a funder report →</Link>
        </div>
      </div>

      <section className="tiles">
        <div className="tile"><span className="tile__value">{h.participants}</span><span className="tile__label">participants enrolled</span></div>
        <div className="tile"><span className="tile__value">{h.responses_pre} / {h.responses_post}</span><span className="tile__label">pre / post surveys</span></div>
        <div className="tile"><span className="tile__value">{h.matched}</span><span className="tile__label">matched pre and post</span></div>
        <div className="tile tile--accent">
          <span className="tile__value">{h.top_improvement ? `${h.top_improvement.pct}%` : "–"}</span>
          <span className="tile__label">{h.top_improvement ? `improved: ${h.top_improvement.metric}` : "improvement shows once pre and post match"}</span>
        </div>
      </section>

      {empty && (
        <section className="card empty-state">
          <h3>No data yet</h3>
          <p className="muted">Publish a survey tool, add participants, and enter program numbers. Charts appear here automatically.</p>
          <Link className="btn btn--primary" to="/tools">Go to Survey Tools</Link>
        </section>
      )}

      {outcomes.length > 0 && <h2 className="section-head">Outcomes</h2>}
      <div className="chart-grid">{outcomes.map((c) => <ChartCard key={c.id} chart={c} xlsxUrl={api.chartXlsx(c.id)} />)}</div>

      {answers.length > 0 && <h2 className="section-head">Survey answers</h2>}
      <div className="chart-grid">{answers.map((c) => <ChartCard key={c.id} chart={c} xlsxUrl={api.chartXlsx(c.id)} />)}</div>

      {people.length > 0 && <h2 className="section-head">Who we serve</h2>}
      <div className="chart-grid">{people.map((c) => <ChartCard key={c.id} chart={c} xlsxUrl={api.chartXlsx(c.id)} />)}</div>

      {program.length > 0 && <h2 className="section-head">Program activity</h2>}
      <div className="chart-grid">{program.map((c) => <ChartCard key={c.id} chart={c} xlsxUrl={api.chartXlsx(c.id)} />)}</div>

      {data.open_responses.length > 0 && (
        <>
          <h2 className="section-head">In their words</h2>
          <section className="quotes">
            {data.open_responses.slice(0, 6).map((q, i) => (
              <blockquote key={i} className="card quote">
                <p>“{q.text}”</p>
                <cite className="muted small">{q.question} · {q.wave === "pre" ? "start" : "end"} of program</cite>
              </blockquote>
            ))}
          </section>
          <p className="muted small">Read quotes before sharing them: make sure no one can be identified.</p>
        </>
      )}
      <p className="muted small">Privacy: demographic groups with fewer than {data.min_group_size} people are combined so no one can be identified.</p>
    </div>
  );
}
