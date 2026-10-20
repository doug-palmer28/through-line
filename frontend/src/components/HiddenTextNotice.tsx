import type { SourceInfo } from "../api";

/** Tells staff when a document had text a person can't see (white, tiny, off-page…), which the AI never read. */
export default function HiddenTextNotice({ sources }: { sources: SourceInfo[] }) {
  const flagged = sources.filter((s) => (s.hidden ?? []).length > 0);
  if (!flagged.length) return null;
  return (
    <div className="notice hidden-notice small">
      <strong>We skipped text you can't see.</strong> The AI only reads what a person would see on the page.
      <ul>
        {flagged.map((s) => (
          <li key={s.label}>
            {s.label}: {s.hidden!.map((h) => `${h.chars.toLocaleString()} characters of ${h.reason}`).join("; ")}
          </li>
        ))}
      </ul>
      <span className="muted">If that text matters, make it visible in the document and upload it again.</span>
    </div>
  );
}
