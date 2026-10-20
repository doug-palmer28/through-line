export const countWords = (text: string) => (text.trim() ? text.trim().split(/\s+/).length : 0);

/** Keeps text within `limit` words (used in onChange so typing stops at the limit). */
export function clampWords(text: string, limit: number) {
  if (countWords(text) <= limit) return text;
  const words = text.trim().split(/\s+/).slice(0, limit);
  return words.join(" ");
}

/** A countdown of words left, with a bar that shrinks as you type. */
export default function WordCounter({ text, limit }: { text: string; limit: number }) {
  const left = Math.max(0, limit - countWords(text));
  const share = left / limit;
  const tone = share > 0.25 ? "ok" : share > 0.08 ? "low" : "out";
  return (
    <div className={`words words--${tone}`} aria-live="polite">
      <div className="words__bar">
        <span style={{ width: `${share * 100}%` }} />
      </div>
      <span className="words__count">
        {left} word{left === 1 ? "" : "s"} left
      </span>
    </div>
  );
}
