import { Link } from "react-router-dom";
import { useAuth } from "../auth";

const AREAS = [
  {
    to: "/logic-model",
    color: "red",
    step: "01",
    title: "Logic Model",
    body: "Work with a small team of AI agents to set out your theory of change, build your logic model, and choose the few metrics that matter most.",
  },
  {
    to: "/tools",
    color: "blue",
    step: "02",
    title: "Survey Tools",
    body: "Build and send out surveys and staff assessments, before and after your program. Participants are known only by a code, never by name.",
  },
  {
    to: "/dashboard",
    color: "yellow",
    step: "03",
    title: "Dashboard",
    body: "See your results in clear charts and headline numbers, alongside approved testimonials, ready for a funder or impact report.",
  },
];

export default function Home() {
  const { me } = useAuth();
  return (
    <>
      <section className="hero">
        <div className="hero__text">
          <p className="eyebrow">Nonprofit impact toolkit</p>
          <h1>
            From mission
            <br />
            to evidence
            <br />
            to story.
          </h1>
          <p className="lede">
            Through Line helps small nonprofits say clearly what change they create, measure it, and share it,
            without needing an evaluation team.
          </p>
          <div className="hero__ctas">
            {me ? (
              <Link className="btn btn--primary" to="/logic-model">Continue: {me.org.name} →</Link>
            ) : (
              <>
                <Link className="btn btn--primary" to="/signup">Create a staff account</Link>
                <Link className="btn btn--ghost" to="/login">Sign in</Link>
                <Link className="link-button" to="/participant">I'm a participant →</Link>
              </>
            )}
          </div>
        </div>
        <div className="hero__art" aria-hidden="true">
          <span className="hero__circle" />
          <span className="hero__square" />
          <span className="hero__triangle" />
          <span className="hero__bar" />
        </div>
      </section>

      <section className="areas">
        {AREAS.map((area) => (
          <Link key={area.to} to={area.to} className={`area area--${area.color}`}>
            <span className="area__step">{area.step}</span>
            <h2>{area.title}</h2>
            <p>{area.body}</p>
            <span className="area__go">Open →</span>
          </Link>
        ))}
      </section>
    </>
  );
}
