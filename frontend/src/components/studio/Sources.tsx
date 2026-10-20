import type { AlignmentNote, Citation, Research } from "../../api";

const sortById = (a: Citation, b: Citation) => Number(a.id.slice(1)) - Number(b.id.slice(1));

/** Inline citation chips like [S3]. Hover for the title; click to open verified links. */
export function SourceChips({ ids, sources }: { ids: string[]; sources: Citation[] }) {
  const known = ids.map((id) => sources.find((s) => s.id === id)).filter(Boolean) as Citation[];
  if (known.length === 0) return null;
  return (
    <span className="cites">
      {known.map((c) =>
        c.url ? (
          <a
            key={c.id}
            className={`cite ${c.verified ? "is-verified" : ""}`}
            href={c.url}
            target="_blank"
            rel="noreferrer"
            title={`${c.title}, ${c.publisher}`}
          >
            {c.id}
          </a>
        ) : (
          <span key={c.id} className="cite" title={`${c.title}, ${c.publisher} (unverified)`}>
            {c.id}
          </span>
        ),
      )}
    </span>
  );
}

/** The full list of sources, with a clear verified/unverified status. */
export function SourcesList({ sources, title = "Sources" }: { sources: Citation[]; title?: string }) {
  if (sources.length === 0) return null;
  return (
    <div className="sources">
      <span className="eyebrow">{title}</span>
      <ol>
        {[...sources].sort(sortById).map((c) => (
          <li key={c.id}>
            <span className="sources__id">{c.id}</span>
            <div>
              {c.url ? (
                <a href={c.url} target="_blank" rel="noreferrer">
                  {c.title}
                </a>
              ) : (
                <strong>{c.title}</strong>
              )}{" "}
              <span className="muted">· {c.publisher}</span>{" "}
              <span className={`badge ${c.verified ? "badge--ok" : "badge--warn"}`}>
                {c.verified ? "verified link" : "unverified: check before citing"}
              </span>
              <p className="small muted">{c.note}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** "How this lines up with funders": the team's alignment notes plus the funder research behind them. */
export function AlignmentCard({
  alignment,
  sources,
  research,
}: {
  alignment: AlignmentNote[];
  sources: Citation[];
  research: Research | null;
}) {
  const all = research ? [...research.sources] : sources;
  if (alignment.length === 0 && !research) return null;
  return (
    <section className="card alignment">
      <p className="eyebrow">Research-backed</p>
      <h3>How this lines up with funders</h3>
      {research?.mode === "knowledge" && (
        <p className="small notice">
          Live web search wasn't available, so these points come from the team's general knowledge. Check sources before
          citing them.
        </p>
      )}
      {alignment.length > 0 && (
        <ul className="alignment__notes">
          {alignment.map((a, i) => (
            <li key={i}>
              {a.note} <SourceChips ids={a.source_ids} sources={all} />
            </li>
          ))}
        </ul>
      )}
      {research && research.funder_priorities.length > 0 && (
        <details>
          <summary>What funders in this field look for ({research.funder_priorities.length})</summary>
          <ul className="funders">
            {research.funder_priorities.map((f, i) => (
              <li key={i}>
                <strong>{f.funder}</strong> <span className="chip">{f.funder_type}</span>
                <p className="small">
                  {f.what_they_want} <SourceChips ids={f.source_ids} sources={all} />
                </p>
              </li>
            ))}
          </ul>
        </details>
      )}
      <details>
        <summary>Sources ({all.length})</summary>
        <SourcesList sources={all} title="" />
      </details>
    </section>
  );
}
