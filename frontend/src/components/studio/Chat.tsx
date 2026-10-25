import { useEffect, useRef, useState } from "react";
import type { StudioSession } from "../../api";
import { stepLabel } from "./Stepper";
import Thinking from "./Thinking";
import UploadOffer from "./UploadOffer";
import WordCounter, { clampWords } from "./WordCounter";

// Phones and tablets: Enter adds a new line and the Send button sends (their keyboards can fire Enter before the
// last word is committed, which made answers look like they hadn't gone through).
const touch = typeof window !== "undefined" && window.matchMedia?.("(pointer: coarse)").matches;

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
  const [pending, setPending] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const open = session.phase === "interview" && session.current_question;

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [session.transcript.length, busy]);

  // Once the team is done: if the answer didn't make it into the conversation (an error), put it back in the box.
  useEffect(() => {
    if (busy || pending === null) return;
    const mine = session.transcript.filter((line) => line.role !== "team");
    if (mine[mine.length - 1]?.text !== pending) setText((current) => current || pending);
    setPending(null);
  }, [busy, pending, session.transcript]);

  // ...and if it turns out the team did get it (a dropped connection, then a resync), clear the box again.
  useEffect(() => {
    const mine = session.transcript.filter((line) => line.role !== "team");
    const last = mine[mine.length - 1]?.text;
    if (last) setText((current) => (current.trim() === last ? "" : current));
  }, [session.transcript]);

  const submit = () => {
    const answer = text.trim();
    if (!answer || busy) return;
    setPending(answer);
    setText("");
    onAnswer(answer);
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
        {busy && pending && (
          <div className="bubble bubble--client">
            <span className="bubble__who">You</span>
            <p>{pending}</p>
          </div>
        )}
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
              if (e.key === "Enter" && !e.shiftKey && !touch && !e.nativeEvent.isComposing) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={touch ? "Take your time. Tap Send answer when you're done." : "Take your time. Enter sends; Shift+Enter adds a new line."}
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
