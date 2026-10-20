import { useState } from "react";
import type { ChartSpec } from "../../api";

// Validated pair (dataviz validator, light mode: CVD ΔE 19.9, normal 28.8, contrast ≥ 3:1).
// Color follows the entity: Pre / "before" is always blue, Post / "after" is always terracotta.
export const SERIES_COLORS = ["#3e63b0", "#d96c4f"];
const AFTER = /after|post/i;

const fmt = (v: number | null, unit: string) =>
  v === null ? "–" : `${Number.isInteger(v) ? v.toLocaleString() : v.toFixed(2)}${unit === "%" ? "%" : ""}`;

type TipState = { x: number; y: number; text: string } | null;

/** Round an axis maximum up to a tidy 1 / 2 / 2.5 / 5 x 10^k so ticks read cleanly. */
function niceMax(v: number) {
  if (v <= 0) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  const step = [1, 2, 2.5, 5, 10].find((m) => m * p >= v)!;
  return step * p;
}

function Tooltip({ tip }: { tip: TipState }) {
  if (!tip) return null;
  return <div className="chart-tip" style={{ left: tip.x, top: tip.y }}>{tip.text}</div>;
}

/** Horizontal bars (grouped when there are 2 series). Thin bars, rounded data-end, hairline grid. */
export function HBarChart({ chart }: { chart: ChartSpec }) {
  const [tip, setTip] = useState<TipState>(null);
  const values = chart.series.flatMap((s) => s.values.map((v) => v ?? 0));
  const max = chart.unit === "%" ? 100 : niceMax(Math.max(1, ...values));
  const labelW = 170, plotW = 360, bar = 16, gap = 2, groupGap = 14;
  const groupH = chart.series.length * bar + (chart.series.length - 1) * gap;
  const h = chart.categories.length * (groupH + groupGap) + 24;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => t * max);
  const single = chart.series.length === 1;
  const colorFor = (si: number, ci: number) =>
    single && chart.categories.length === 2 && AFTER.test(chart.categories[1]) ? SERIES_COLORS[ci === 1 ? 1 : 0] : SERIES_COLORS[si % 2];

  return (
    <div className="chart-plot" onMouseLeave={() => setTip(null)}>
      <svg viewBox={`0 0 ${labelW + plotW + 60} ${h}`} role="img" aria-label={chart.title}>
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={labelW + (t / max) * plotW} x2={labelW + (t / max) * plotW} y1={0} y2={h - 20} className="chart-gridline" />
            <text x={labelW + (t / max) * plotW} y={h - 6} className="chart-axis" textAnchor="middle">
              {Math.round(t).toLocaleString()}{chart.unit === "%" ? "%" : ""}
            </text>
          </g>
        ))}
        {chart.categories.map((cat, ci) => {
          const y0 = ci * (groupH + groupGap) + 4;
          return (
            <g key={cat}>
              <text x={labelW - 10} y={y0 + groupH / 2 + 4} className="chart-label" textAnchor="end">
                {cat.length > 26 ? cat.slice(0, 25) + "…" : cat}
              </text>
              {chart.series.map((s, si) => {
                const v = s.values[ci] ?? 0;
                const w = Math.max(2, (v / max) * plotW);
                const y = y0 + si * (bar + gap);
                const color = colorFor(si, ci);
                return (
                  <g key={s.name}
                     onMouseMove={(e) => {
                       const r = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect();
                       setTip({ x: e.clientX - r.left + 12, y: e.clientY - r.top - 10, text: `${cat}${single ? "" : ` · ${s.name}`}: ${fmt(s.values[ci], chart.unit)}${single && chart.counts ? ` (${chart.counts[ci]} people)` : ""}` });
                     }}>
                    <rect x={labelW} y={y - 3} width={plotW} height={bar + 6} fill="transparent" />
                    <path d={`M${labelW},${y} h${w - 4} a4,4 0 0 1 4,4 v${bar - 8} a4,4 0 0 1 -4,4 h${-(w - 4)} z`} fill={color} />
                    {single && (
                      <text x={labelW + w + 6} y={y + bar - 4} className="chart-value">{fmt(s.values[ci], chart.unit)}</text>
                    )}
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <Tooltip tip={tip} />
    </div>
  );
}

/** Line over time: 2px line, ≥8px markers with a surface ring, crosshair tooltip. */
export function LineChart({ chart }: { chart: ChartSpec }) {
  const [hover, setHover] = useState<number | null>(null);
  const s = chart.series[0];
  const vals = s.values.map((v) => v ?? 0);
  const max = niceMax(Math.max(1, ...vals) * 1.05);
  const W = 560, H = 220, L = 46, B = 28, T = 12;
  const x = (i: number) => L + (chart.categories.length === 1 ? (W - L) / 2 : (i / (chart.categories.length - 1)) * (W - L - 16));
  const y = (v: number) => T + (1 - v / max) * (H - T - B);
  const ticks = [0, 0.5, 1].map((t) => t * max);
  return (
    <div className="chart-plot">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={chart.title} onMouseLeave={() => setHover(null)}>
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={L} x2={W} y1={y(t)} y2={y(t)} className="chart-gridline" />
            <text x={L - 8} y={y(t) + 4} className="chart-axis" textAnchor="end">{Math.round(t).toLocaleString()}</text>
          </g>
        ))}
        {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} className="chart-crosshair" />}
        <polyline points={vals.map((v, i) => `${x(i)},${y(v)}`).join(" ")} fill="none" stroke={SERIES_COLORS[0]}
                  strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {vals.map((v, i) => (
          <g key={i} onMouseEnter={() => setHover(i)}>
            <rect x={x(i) - 18} y={T} width={36} height={H - T - B} fill="transparent" />
            <circle cx={x(i)} cy={y(v)} r={5} fill={SERIES_COLORS[0]} stroke="#fff" strokeWidth={2} />
            <text x={x(i)} y={H - 8} className="chart-axis" textAnchor="middle">{chart.categories[i]}</text>
          </g>
        ))}
        {hover !== null && (
          <g>
            <rect x={Math.min(x(hover) + 8, W - 130)} y={T} width={122} height={24} rx={4} className="chart-tip-svg" />
            <text x={Math.min(x(hover) + 16, W - 122)} y={T + 16} className="chart-tip-text">
              {chart.categories[hover]}: {fmt(s.values[hover], chart.unit)}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}

/** A chart card: title, legend (2+ series), the chart or a table view, the note, and an Excel download. */
export function ChartCard({ chart, xlsxUrl }: { chart: ChartSpec; xlsxUrl: string }) {
  const [table, setTable] = useState(false);
  return (
    <figure className="card chart-card">
      <figcaption>
        <div>
          <h3>{chart.title}</h3>
          {chart.unit && chart.unit !== "%" && <p className="muted small">{chart.unit}</p>}
        </div>
        <div className="chart-card__actions">
          <button className="link-button small" onClick={() => setTable(!table)}>{table ? "Chart" : "Table"}</button>
          <a className="link-button small" href={xlsxUrl} download>Excel ↓</a>
        </div>
      </figcaption>
      {chart.series.length > 1 && (
        <ul className="legend">
          {chart.series.map((s, i) => (
            <li key={s.name}><span className="legend__swatch" style={{ background: SERIES_COLORS[i % 2] }} />{s.name}</li>
          ))}
        </ul>
      )}
      {table ? (
        <table className="table">
          <thead><tr><th>{chart.kind === "line" ? "Month" : "Category"}</th>{chart.series.map((s) => <th key={s.name}>{s.name}</th>)}</tr></thead>
          <tbody>
            {chart.categories.map((c, i) => (
              <tr key={c}><td>{c}</td>{chart.series.map((s) => <td key={s.name}>{fmt(s.values[i], chart.unit)}{chart.counts && chart.series.length === 1 ? <span className="muted"> ({chart.counts[i]})</span> : null}</td>)}</tr>
            ))}
          </tbody>
        </table>
      ) : chart.kind === "line" ? (
        <LineChart chart={chart} />
      ) : (
        <HBarChart chart={chart} />
      )}
      {chart.note && <p className="chart-note">{chart.note}</p>}
    </figure>
  );
}
