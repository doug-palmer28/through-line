export default function Thinking({ label }: { label: string }) {
  return (
    <div className="thinking" role="status">
      <span className="thinking__shapes" aria-hidden="true">
        <span className="shape shape--circle" />
        <span className="shape shape--square" />
        <span className="shape shape--triangle" />
      </span>
      {label}
    </div>
  );
}
