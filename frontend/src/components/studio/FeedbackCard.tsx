import { useState } from "react";
import WordCounter, { clampWords } from "./WordCounter";

type Props = {
  roundsLeft: number;
  wordLimit: number;
  busy: boolean;
  placeholder: string;
  onSend: (text: string) => void;
};

/** "Ask the team for changes", with a word countdown and limited rounds. */
export default function FeedbackCard({ roundsLeft, wordLimit, busy, placeholder, onSend }: Props) {
  const [text, setText] = useState("");
  const out = roundsLeft <= 0;
  return (
    <section className="card feedback">
      <h3>Ask the team for changes</h3>
      <p className="muted small">
        {out
          ? "You've used both rounds. You can still edit directly."
          : `${roundsLeft} round${roundsLeft === 1 ? "" : "s"} left. Small fixes are quicker to edit directly.`}
      </p>
      <textarea
        rows={4}
        value={text}
        disabled={busy || out}
        placeholder={placeholder}
        onChange={(e) => setText(clampWords(e.target.value, wordLimit))}
      />
      <div className="feedback__actions">
        <WordCounter text={text} limit={wordLimit} />
        <button
          className="btn btn--secondary"
          disabled={busy || out || !text.trim()}
          onClick={() => {
            onSend(text.trim());
            setText("");
          }}
        >
          Send to team
        </button>
      </div>
    </section>
  );
}
