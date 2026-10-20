import { useRef } from "react";
import type { StudioSession } from "../../api";

type Props = { session: StudioSession; onUpload: (file: File) => void; onSkip: () => void };

/** The team's optional request for a document, or a quiet "add a document" link. */
export default function UploadOffer({ session, onUpload, onSkip }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  if (session.uploads_left <= 0) return null;

  const picker = (
    <input
      ref={fileRef}
      type="file"
      accept=".pdf,.docx,.pptx,.txt,.md"
      hidden
      onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) onUpload(file);
        e.target.value = "";
      }}
    />
  );

  if (session.upload_request) {
    return (
      <div className="upload-offer">
        <div>
          <p className="eyebrow">Optional · your team asks</p>
          <p>{session.upload_request}</p>
        </div>
        <div className="upload-offer__actions">
          <button className="btn btn--secondary" onClick={() => fileRef.current?.click()}>
            Add a file
          </button>
          <button className="link-button" onClick={onSkip}>
            Skip
          </button>
        </div>
        {picker}
      </div>
    );
  }

  return (
    <p className="add-doc">
      <button className="link-button" onClick={() => fileRef.current?.click()}>
        + Add a document
      </button>{" "}
      <span className="muted small">(optional, {session.uploads_left} left; read, never saved)</span>
      {picker}
    </p>
  );
}
