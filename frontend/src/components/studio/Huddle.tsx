import { useEffect, useRef, useState } from "react";
import { api, type AgentKey, type FeedEvent } from "../../api";
import { AGENTS, AgentIcon, ShapePath, agentName } from "./agents";

// Where each agent sits in the huddle diagram (viewBox 0 0 320 240). The Team Lead is in the middle.
const POS: Record<AgentKey, { x: number; y: number }> = {
  boss: { x: 160, y: 116 },
  sector_expert: { x: 56, y: 40 },
  client_advocate: { x: 264, y: 40 },
  evaluation_specialist: { x: 56, y: 186 },
  funder_researcher: { x: 264, y: 186 },
};
const SPECIALISTS: AgentKey[] = ["sector_expert", "client_advocate", "evaluation_specialist", "funder_researcher"];
const LABEL_DY: Record<AgentKey, number> = {
  boss: 36, sector_expert: 30, client_advocate: 30, evaluation_specialist: 32, funder_researcher: 32,
};

type Props = {
  sessionId: string;
  working: boolean; // poll while the team is working
  title?: string;
  large?: boolean;
};

/** Live view of the agent team: who is talking to whom, and a running summary of what they're discussing. */
export default function Huddle({ sessionId, working, title = "Team huddle", large = false }: Props) {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const lastSeq = useRef(0);
  const logRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    lastSeq.current = 0;
    setEvents([]);
  }, [sessionId]);

  // Poll the feed while the team works; fetch once more when it stops.
  useEffect(() => {
    let cancelled = false;
    const pull = async () => {
      try {
        const { events: fresh } = await api.feed(sessionId, lastSeq.current);
        if (cancelled || fresh.length === 0) return;
        lastSeq.current = fresh[fresh.length - 1].seq;
        setEvents((prev) => [...prev, ...fresh].slice(-80));
      } catch {
        /* the next poll will try again */
      }
    };
    pull();
    if (!working) return () => void (cancelled = true);
    const timer = setInterval(pull, 700);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [sessionId, working]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  const latest = events[events.length - 1];
  const speaking = working ? latest?.agent : undefined;
  // For each specialist: is a question travelling to them, or an answer travelling back?
  const traffic = SPECIALISTS.flatMap((s) => {
    if (!working || !latest) return [];
    const ask = [...events].reverse().find((e) => e.kind === "ask" && e.to === s);
    const reply = [...events].reverse().find((e) => e.kind === "reply" && e.agent === s);
    if (ask && (!reply || ask.seq > reply.seq)) return [{ specialist: s, from: "boss" as AgentKey, to: s, seq: ask.seq }];
    if (reply && latest.seq - reply.seq < 3) return [{ specialist: s, from: s, to: "boss" as AgentKey, seq: reply.seq }];
    return [];
  });
  const busyLinks = new Set(traffic.map((t) => t.specialist));

  return (
    <section className={`huddle ${large ? "huddle--large" : ""}`}>
      <div className="huddle__head">
        <h3>{title}</h3>
        <span className={`huddle__status ${working ? "is-live" : ""}`}>{working ? "Working" : "Waiting for you"}</span>
      </div>

      <svg className="huddle__map" viewBox="0 0 320 240" role="img" aria-label="Agent team connections">
        {SPECIALISTS.map((s) => {
          const active = busyLinks.has(s);
          return (
            <line
              key={s}
              x1={POS.boss.x}
              y1={POS.boss.y}
              x2={POS[s].x}
              y2={POS[s].y}
              className={`huddle__link ${active ? "is-active" : ""}`}
              style={active ? { stroke: AGENTS[s].color } : undefined}
            />
          );
        })}

        {traffic.map((t) => (
          <circle key={`${t.seq}-${t.from}`} r="5" className="huddle__packet" fill={AGENTS[t.from].color}>
            <animateMotion
              dur="1.1s"
              repeatCount="indefinite"
              path={`M${POS[t.from].x},${POS[t.from].y} L${POS[t.to].x},${POS[t.to].y}`}
            />
          </circle>
        ))}

        {(Object.keys(POS) as AgentKey[]).map((a) => (
          <g key={a} className={`huddle__node ${speaking === a ? "is-speaking" : ""}`}>
            {speaking === a && <circle cx={POS[a].x} cy={POS[a].y} r={28} className="huddle__pulse" fill={AGENTS[a].color} />}
            <ShapePath shape={AGENTS[a].shape} cx={POS[a].x} cy={POS[a].y} r={a === "boss" ? 20 : 15} fill={AGENTS[a].color} />
            <text x={POS[a].x} y={POS[a].y + LABEL_DY[a]} className="huddle__label">
              {AGENTS[a].name}
            </text>
          </g>
        ))}
      </svg>

      <ol className="huddle__log" ref={logRef} aria-live="polite">
        {events.length === 0 && <li className="huddle__empty">The team's conversation will appear here as they work.</li>}
        {events.map((e) => (
          <li key={e.seq} className={`huddle__line huddle__line--${e.kind}`}>
            <AgentIcon agent={e.agent} size={12} />
            <span>
              <strong>
                {agentName(e.agent)}
                {e.to ? ` → ${agentName(e.to)}` : ""}
              </strong>{" "}
              {e.kind === "note" ? `noted: ${e.text}` : e.text}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
