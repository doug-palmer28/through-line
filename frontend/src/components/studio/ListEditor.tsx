/** An editable list of short phrases: edit in place, remove, add. Read-only mode renders a plain list. */
export default function ListEditor({
  items,
  onChange,
  readOnly,
  addLabel = "Add",
}: {
  items: string[];
  onChange: (items: string[]) => void;
  readOnly?: boolean;
  addLabel?: string;
}) {
  if (readOnly) {
    return (
      <ul className="plain-list">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    );
  }
  return (
    <div className="list-editor">
      {items.map((item, i) => (
        <div key={i} className="list-editor__row">
          <textarea
            rows={1}
            value={item}
            onChange={(e) => onChange(items.map((x, j) => (j === i ? e.target.value : x)))}
          />
          <button
            className="icon-button"
            aria-label="Remove"
            title="Remove"
            onClick={() => onChange(items.filter((_, j) => j !== i))}
          >
            ×
          </button>
        </div>
      ))}
      <button className="link-button" onClick={() => onChange([...items, ""])}>
        + {addLabel}
      </button>
    </div>
  );
}
