import type { AgentKey } from "../../api";
import { AGENTS, AgentIcon } from "./agents";

const STEPS = [
  {
    title: "Share what you have",
    body: "Add your website, a deck, an old logic model, or a grant report. It's all optional. Files are read, never saved.",
    time: "2 min",
  },
  {
    title: "Answer five questions",
    body: "Your team asks one question at a time. Take as long as you need; answers are up to 200 words.",
    time: "10–20 min",
  },
  {
    title: "Shape your logic model",
    body: "The team drafts it. Edit any line directly, or tell the team what to change (two rounds). Approve when it feels right.",
    time: "10 min",
  },
  {
    title: "Choose your metrics",
    body: "The team proposes 3–5 measures backed by research, each with several cited questions to choose from. Pick, edit, and approve.",
    time: "10 min",
  },
  {
    title: "Download",
    body: "Take home an editable PowerPoint with your logic model and measurement plan.",
    time: "1 min",
  },
];

export default function Tutorial({ onClose, starting }: { onClose: () => void; starting: boolean }) {
  return (
    <section className="tutorial card">
      <p className="eyebrow">How this works</p>
      <h2>Build your logic model with a small AI team</h2>
      <p className="muted">
        Five agents work with you. They research what funders in your field look for, and every draft is reviewed by the
        whole team before you see it. You'll always see who's talking to whom and what they're working on.
      </p>

      <ul className="tutorial__team">
        {(Object.keys(AGENTS) as AgentKey[]).map((key) => (
          <li key={key}>
            <AgentIcon agent={key} size={18} />
            <span>{AGENTS[key].name}</span>
          </li>
        ))}
      </ul>

      <ol className="tutorial__steps">
        {STEPS.map((step, i) => (
          <li key={step.title}>
            <span className="tutorial__num">{i + 1}</span>
            <div>
              <strong>{step.title}</strong>
              <p>{step.body}</p>
            </div>
            <span className="tutorial__time">{step.time}</span>
          </li>
        ))}
      </ol>

      <p className="muted small">
        You can leave and come back: your session stays open for 7 days in this browser. Nothing the team drafts is final
        until you approve it.
      </p>
      <button className="btn btn--primary" onClick={onClose}>
        {starting ? "Let's begin" : "Back to my work"}
      </button>
    </section>
  );
}
