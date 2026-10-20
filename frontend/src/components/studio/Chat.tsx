import { useEffect, useRef, useState } from "react";
import type { StudioSession } from "../../api";
import { stepLabel } from "./Stepper";
import Thinking from "./Thinking";
import UploadOffer from "./UploadOffer";
import WordCounter, { clampWords } from "./WordCounter";

type Props = {
  session: StudioSession;
  busy: string | null;
  wordLimit: number;
  onAnswer: (text: string) => void;
  onUpload: (file: File) => void;
  onSkipUpload: () => void;
};

export default function Chat({ session, busy, wordLimit, onAnswer, onUpload, onSkipUpload }: Props) {
  const [text, setText] = useState("");
  const logRef = useRef<HTMLDivElement>(null);
  const open = session.phase === "interview" && session.current_question;

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [session.transcript.length, busy]);

  const submit = () => {
    if (!text.trim() || busy) return;
    onAnswer(text.trim());
    setText("");
  };

  return (
    <section className="card chat">
      <div className="chat__head">
        <div>
          <p className="eyebrow">{stepLabel("interview")}</p>
          <h3>
            {open ? `Question ${session.question_number} of ${session.questions_total}` : "Getting to know you"}
          </h3>
        </div>
        <div className="progress" title={`${session.answered} of ${session.questions_total} answered`}>
          {Array.from({ length: session.questions_total }, (_, i) => (
            <span key={i} className={`progress__step ${i < session.answered ? "is-done" : ""}`} />
          ))}
        </div>
      </div>

      <div className="chat__log" ref={logRef}>
        {session.transcript.map((line, i) => (
          <div key={i} className={`bubble bubble--${line.role}`}>
            <span className="bubble__who">{line.role === "team" ? "Your team" : "You"}</span>
            <p>{line.text}</p>
          </div>
        ))}
        {busy && <Thinking label={busy} />}
      </div>

      {!busy && (
        <UploadOffer session={session} onUpload={onUpload} onSkip={onSkipUpload} />
      )}

      {open && (
        <div className="chat__compose">
          {session.current_question?.why && <p className="why">Why we ask: {session.current_question.why}</p>}
          <textarea
            value={text}
            onChange={(e) => setText(clampWords(e.target.value, wordLimit))}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Take your time. Enter sends; Shift+Enter adds a new line."
            rows={4}
            disabled={!!busy}
          />
          <div className="chat__actions">
            <WordCounter text={text} limit={wordLimit} />
            <button className="btn btn--primary" onClick={submit} disabled={!!busy || !text.trim()}>
              Send answer
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
