import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useApi } from "../useApi";

const NAV = [
  { to: "/logic-model", label: "Logic Model", color: "red" },
  { to: "/tools", label: "Survey Tools", color: "blue" },
  { to: "/dashboard", label: "Dashboard", color: "yellow" },
  { to: "/report", label: "Impact Report", color: "green" },
  { to: "/grants", label: "Grants", color: "purple" },
];

function BackendStatus() {
  const { data, error } = useApi(api.health);
  if (error) return <span className="status status--down">Backend offline</span>;
  if (!data) return <span className="status">Connecting…</span>;
  return (
    <span className="status status--up" title={`Agents run on ${data.model}`}>
      {data.model}
    </span>
  );
}

/** Admins can bring in a colleague: the code is shown once and works for 7 days. */
function InviteButton() {
  const [code, setCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (code) return <span className="invite" title="Share this with a colleague. It's shown only once.">Invite code: <code>{code}</code> (7 days)</span>;
  return (
    <button className="link-button small" title={error ?? "Create a sign-up code for a colleague"} onClick={async () => {
      try { setCode((await api.invite()).invite_code); } catch (e) { setError((e as Error).message); }
    }}>Invite a colleague</button>
  );
}

export default function Layout() {
  const { me, signOut } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="shell">
      <header className="topbar">
        <NavLink to="/" className="brand" aria-label="Through Line home">
          <span className="brand__mark" aria-hidden="true">
            <span className="shape shape--circle" />
            <span className="shape shape--square" />
            <span className="shape shape--triangle" />
          </span>
          <span className="brand__name">Through Line</span>
        </NavLink>
        {me ? (
          <nav className="nav">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} className={`nav__link nav__link--${item.color}`}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        ) : (
          <nav className="nav nav--public">
            <Link className="nav__link" to="/participant">
              Participant sign-in
            </Link>
            <Link className="nav__link" to="/login">
              Staff sign in
            </Link>
          </nav>
        )}
        {me && (
          <div className="account">
            <span className="account__org">{me.org.name}</span>
            <span className="account__user">{me.user.display_name}</span>
            <Link className="link-button small" to="/usage">AI usage</Link>
            {me.user.role === "admin" && <InviteButton />}
            <button
              className="link-button small"
              onClick={async () => {
                await signOut();
                navigate("/");
              }}
            >
              Sign out
            </button>
          </div>
        )}
        <BackendStatus />
      </header>

      <main className="main">
        <Outlet />
      </main>

      <footer className="footer">
        Through Line is a class project for AI Foundations at Yale. It uses synthetic data only, not real nonprofit or
        participant information.
      </footer>
    </div>
  );
}
