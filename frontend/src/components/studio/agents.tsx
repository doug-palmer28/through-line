import type { AgentKey } from "../../api";

// Each agent is a shape and a color, not a person.
type Shape = "circle" | "triangle" | "square" | "diamond" | "hexagon";

export const AGENTS: Record<AgentKey, { name: string; shape: Shape; color: string }> = {
  boss: { name: "Team Lead", shape: "circle", color: "var(--red)" },
  sector_expert: { name: "Sector Expert", shape: "triangle", color: "var(--yellow)" },
  client_advocate: { name: "Client Advocate", shape: "square", color: "var(--blue)" },
  evaluation_specialist: { name: "Evaluation Specialist", shape: "diamond", color: "var(--green)" },
  funder_researcher: { name: "Funder Researcher", shape: "hexagon", color: "var(--purple)" },
};

export const agentName = (key: AgentKey | null | undefined) => (key ? AGENTS[key]?.name ?? key : "");

/** An agent's shape as an inline SVG icon. */
export function AgentIcon({ agent, size = 16 }: { agent: AgentKey; size?: number }) {
  const { shape, color } = AGENTS[agent];
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" aria-hidden="true" className="agent-icon">
      <ShapePath shape={shape} cx={10} cy={10} r={9} fill={color} />
    </svg>
  );
}

/** Draws a shape centred on (cx, cy) with "radius" r. Shared by icons and the huddle diagram. */
export function ShapePath({
  shape,
  cx,
  cy,
  r,
  fill,
  className,
}: {
  shape: Shape;
  cx: number;
  cy: number;
  r: number;
  fill: string;
  className?: string;
}) {
  if (shape === "circle") return <circle cx={cx} cy={cy} r={r} fill={fill} className={className} />;
  if (shape === "square")
    return <rect x={cx - r * 0.85} y={cy - r * 0.85} width={r * 1.7} height={r * 1.7} fill={fill} className={className} />;
  if (shape === "triangle")
    return (
      <polygon
        points={`${cx},${cy - r} ${cx + r},${cy + r * 0.8} ${cx - r},${cy + r * 0.8}`}
        fill={fill}
        className={className}
      />
    );
  if (shape === "hexagon") {
    const pts = Array.from({ length: 6 }, (_, i) => {
      const a = (Math.PI / 3) * i;
      return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
    }).join(" ");
    return <polygon points={pts} fill={fill} className={className} />;
  }
  return <polygon points={`${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`} fill={fill} className={className} />;
}
