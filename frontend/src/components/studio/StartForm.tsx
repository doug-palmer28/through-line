import { useState } from "react";

type Props = { busy: boolean; defaultOrgName?: string; onStart: (form: FormData) => void };

export default function StartForm({ busy, defaultOrgName = "", onStart }: Props) {
  const [orgName, setOrgName] = useState(defaultOrgName);
  const [website, setWebsite] = useState("");
  const [files, setFiles] = useState<File[]>([]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const form = new FormData();
    form.append("org_name", orgName.trim());
    if (website.trim()) form.append("website_url", website.trim());
    files.forEach((f) => form.append("files", f));
    onStart(form);
  };

  return (
    <form className="card start" onSubmit={submit}>
      <p className="eyebrow">Step 1 · Share</p>
      <h2>Help your team get up to speed</h2>
      <p className="muted">
        Anything you already have helps: a deck, an old logic model, a grant proposal, an annual report, or your website.
        All of it is optional.
      </p>

      <label className="field">
        <span>Organization name</span>
        <input value={orgName} onChange={(e) => setOrgName(e.target.value)} required maxLength={120} autoFocus />
      </label>

      <label className="field">
        <span>Website (optional)</span>
        <input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://www.example.org" />
      </label>

      <label className="field">
        <span>Documents (optional, up to 5: PDF, Word, PowerPoint, text)</span>
        <input
          type="file"
          multiple
          accept=".pdf,.docx,.pptx,.txt,.md"
          onChange={(e) => setFiles(Array.from(e.target.files ?? []).slice(0, 5))}
        />
      </label>
      {files.length > 0 && (
        <ul className="file-list">
          {files.map((f) => (
            <li key={f.name}>{f.name}</li>
          ))}
        </ul>
      )}

      <p className="privacy">
        <strong>Privacy:</strong> files and website text are read in memory and never saved. What you type is saved so
        you can come back. The team's working notes are deleted when you finish.
      </p>

      <button className="btn btn--primary" disabled={busy || !orgName.trim()}>
        {busy ? "Reading…" : "Meet your team"}
      </button>
    </form>
  );
}
