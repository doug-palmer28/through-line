import { useEffect, useState } from "react";
import type { LogicModel, LogicModelStage } from "../../api";
import ListEditor from "./ListEditor";

type Props = {
  model: LogicModel;
  version: number;
  stages: LogicModelStage[];
  readOnly?: boolean;
  busy?: boolean;
  onSave?: (model: LogicModel) => Promise<void>;
  onDirtyChange?: (dirty: boolean) => void;
};

const clean = (m: LogicModel): LogicModel => {
  const trim = (xs: string[]) => xs.map((x) => x.trim()).filter(Boolean);
  return {
    ...m,
    program_name: m.program_name.trim(),
    theory_of_change: m.theory_of_change.trim(),
    inputs: trim(m.inputs),
    activities: trim(m.activities),
    outputs: trim(m.outputs),
    short_term_outcomes: trim(m.short_term_outcomes),
    long_term_outcomes: trim(m.long_term_outcomes),
    assumptions: trim(m.assumptions),
    external_factors: trim(m.external_factors),
  };
};

/** The logic model as an editable workspace. Changes are saved as a new version. */
export default function LogicModelEditor({ model, version, stages, readOnly, busy, onSave, onDirtyChange }: Props) {
  const [work, setWork] = useState(model);
  useEffect(() => setWork(model), [version]); // reset only when a new version arrives
  const dirty = !readOnly && JSON.stringify(clean(work)) !== JSON.stringify(clean(model));
  useEffect(() => onDirtyChange?.(dirty), [dirty, onDirtyChange]);
  const set = <K extends keyof LogicModel>(key: K, value: LogicModel[K]) => setWork({ ...work, [key]: value });

  return (
    <section className="card lm">
      <div className="lm__head">
        <div>
          <p className="eyebrow">Logic model · version {version}</p>
          {readOnly ? (
            <h2>{work.program_name}</h2>
          ) : (
            <input className="lm__title" value={work.program_name} onChange={(e) => set("program_name", e.target.value)} />
          )}
        </div>
        {!readOnly && dirty && (
          <div className="lm__save">
            <span className="muted small">Unsaved changes</span>
            <button className="link-button" onClick={() => setWork(model)}>
              Undo
            </button>
            <button className="btn btn--primary btn--small" disabled={busy} onClick={() => onSave?.(clean(work))}>
              Save changes
            </button>
          </div>
        )}
      </div>

      <div className="lm__toc">
        <span className="eyebrow">Theory of change</span>
        {readOnly ? (
          <p>{work.theory_of_change}</p>
        ) : (
          <textarea rows={3} value={work.theory_of_change} onChange={(e) => set("theory_of_change", e.target.value)} />
        )}
      </div>

      <div className="lm__grid">
        {stages.map((stage, i) => (
          <div key={stage.key} className={`lm__col lm__col--${i}`}>
            <h4>{stage.label}</h4>
            <p className="lm__hint">{stage.hint}</p>
            <ListEditor items={work[stage.key]} readOnly={readOnly} onChange={(items) => set(stage.key, items)} />
          </div>
        ))}
      </div>

      <div className="lm__extras">
        <div>
          <h4>Assumptions</h4>
          <ListEditor items={work.assumptions} readOnly={readOnly} onChange={(items) => set("assumptions", items)} />
        </div>
        <div>
          <h4>External factors</h4>
          <ListEditor
            items={work.external_factors}
            readOnly={readOnly}
            onChange={(items) => set("external_factors", items)}
          />
        </div>
      </div>
    </section>
  );
}

export { clean as cleanLogicModel };
