import type { PrivacyReport } from "../api";
import { when } from "../format";

/** The result of the three-layer privacy check (code scrub → Privacy Reviewer → code scan). */
export default function PrivacyPanel({ privacy }: { privacy: PrivacyReport }) {
  const fixes = privacy.agent_findings.length + privacy.code_findings.length;
  return (
    <div className={`privacy ${privacy.clean ? "privacy--clean" : "privacy--warn"}`}>
      <strong>{privacy.clean ? "Privacy check passed" : "Privacy check: please review"}</strong>
      {privacy.checked_at && <span className="muted small"> · checked {when(privacy.checked_at)}</span>}
      <p className="small">
        {privacy.agent_summary}{" "}
        {fixes > 0 ? `${fixes} item${fixes === 1 ? "" : "s"} fixed automatically.` : "Nothing needed fixing."}
        {privacy.quotes_scrubbed_before_agent > 0 &&
          ` ${privacy.quotes_scrubbed_before_agent} contact detail${privacy.quotes_scrubbed_before_agent === 1 ? "" : "s"} removed from quotes before the AI saw them.`}
      </p>
      {privacy.agent_findings.length > 0 && (
        <ul className="small">
          {privacy.agent_findings.map((f, i) => <li key={i}><em>{f.issue}</em> in {f.where}: replaced with “{f.replacement}”</li>)}
        </ul>
      )}
      {(privacy.unresolved ?? []).length > 0 && (
        <p className="small"><strong>Please fix by hand:</strong> {privacy.unresolved!.join(", ")} (the flagged words include a live number).</p>
      )}
    </div>
  );
}
