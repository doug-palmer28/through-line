import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useApi } from "../useApi";

/** Staff sign in / create account. New accounts either start an organization or join one with an invite code. */
export default function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { setMe } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/logic-model";
  const [form, setForm] = useState({ username: "", password: "", display_name: "", org_name: "", invite_code: "", access_code: "" });
  const needsCode = useApi(api.health).data?.signup_code_required ?? false;
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me =
        mode === "login"
          ? await api.login(form.username, form.password)
          : await api.signup({
              username: form.username,
              password: form.password,
              display_name: form.display_name,
              ...(joining ? { invite_code: form.invite_code } : { org_name: form.org_name, access_code: form.access_code }),
            });
      setMe(me);
      navigate(mode === "signup" ? "/logic-model" : from, { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stage stage--narrow">
      <form className="card auth" onSubmit={submit}>
        <p className="eyebrow">Staff portal</p>
        <h2>{mode === "login" ? "Sign in" : "Create your account"}</h2>
        {mode === "signup" && (
          <p className="muted small">
            Your logic model, metrics, surveys and data are saved to your organization's account.
          </p>
        )}

        {mode === "signup" && (
          <>
            <div className="segmented" role="tablist">
              <button type="button" className={!joining ? "is-on" : ""} onClick={() => setJoining(false)}>
                New organization
              </button>
              <button type="button" className={joining ? "is-on" : ""} onClick={() => setJoining(true)}>
                Join my team
              </button>
            </div>
            {joining ? (
              <label className="field">
                <span>Invite code (from your organization's admin)</span>
                <input value={form.invite_code} onChange={set("invite_code")} required autoComplete="off" />
              </label>
            ) : (
              <>
                <label className="field">
                  <span>Organization name</span>
                  <input value={form.org_name} onChange={set("org_name")} required maxLength={120} />
                </label>
                {needsCode && (
                  <label className="field">
                    <span>Access code (from Through Line)</span>
                    <input value={form.access_code} onChange={set("access_code")} required autoComplete="off" maxLength={100} />
                  </label>
                )}
              </>
            )}
            <label className="field">
              <span>Your name (shown to your team)</span>
              <input value={form.display_name} onChange={set("display_name")} required maxLength={80} />
            </label>
          </>
        )}

        <label className="field">
          <span>Username</span>
          <input value={form.username} onChange={set("username")} required autoComplete="username" maxLength={40} />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={form.password}
            onChange={set("password")}
            required
            minLength={mode === "signup" ? 10 : undefined}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
          />
          {mode === "signup" && <small className="muted">At least 10 characters, with a capital letter and a number.</small>}
        </label>

        {error && <p className="alert">{error}</p>}
        <button className="btn btn--primary" disabled={busy}>
          {busy ? "One moment…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
        <p className="small muted">
          {mode === "login" ? (
            <>
              New here? <Link to="/signup">Create an account</Link>
            </>
          ) : (
            <>
              Already have an account? <Link to="/login">Sign in</Link>
            </>
          )}
          {" · "}
          <Link to="/participant">I'm a participant</Link>
        </p>
        <p className="privacy small">
          <strong>Security:</strong> passwords and usernames are stored only as one-way hashes. Sign-in uses a secure,
          HttpOnly cookie, and repeated wrong passwords lock the account for 15 minutes.
        </p>
      </form>
    </div>
  );
}
