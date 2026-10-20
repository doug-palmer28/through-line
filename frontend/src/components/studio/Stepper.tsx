export type StageId = "tutorial" | "share" | "interview" | "logic" | "metrics" | "done";

export const STEPS: { id: StageId; label: string }[] = [
  { id: "tutorial", label: "How it works" },
  { id: "share", label: "Share" },
  { id: "interview", label: "Five questions" },
  { id: "logic", label: "Logic model" },
  { id: "metrics", label: "Metrics" },
  { id: "done", label: "Download" },
];

/** "Step 4 · Logic model": headings take their number from the stepper, so the two always match. */
export function stepLabel(id: StageId): string {
  const i = STEPS.findIndex((s) => s.id === id);
  return `Step ${i + 1} · ${STEPS[i].label}`;
}

export default function Stepper({ current, onHelp }: { current: StageId; onHelp: () => void }) {
  const index = STEPS.findIndex((s) => s.id === current);
  return (
    <nav className="stepper" aria-label="Progress">
      <ol>
        {STEPS.map((step, i) => (
          <li key={step.id} className={i < index ? "is-done" : i === index ? "is-current" : ""}>
            <span className="stepper__dot">{i < index ? "✓" : i + 1}</span>
            <span className="stepper__label">{step.label}</span>
          </li>
        ))}
      </ol>
      {current !== "tutorial" && (
        <button className="link-button" onClick={onHelp}>
          How this works
        </button>
      )}
    </nav>
  );
}
