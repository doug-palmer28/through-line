import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, type Me } from "./api";

type AuthState = {
  me: Me | null;
  checked: boolean; // finished asking the server who we are
  refresh: () => Promise<void>;
  setMe: (me: Me | null) => void;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

/** Staff sign-in state. The token itself lives in an HttpOnly cookie that scripts can't read. */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [checked, setChecked] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setMe(await api.me());
    } catch {
      setMe(null);
    } finally {
      setChecked(true);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signOut = useCallback(async () => {
    await api.logout().catch(() => undefined);
    setMe(null);
  }, []);

  return <AuthContext.Provider value={{ me, checked, refresh, setMe, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

/** Staff-only pages: send signed-out visitors to the sign-in page, then back. */
export function RequireStaff({ children }: { children: React.ReactNode }) {
  const { me, checked } = useAuth();
  const location = useLocation();
  if (!checked) return <p className="muted">Checking your sign-in…</p>;
  if (!me) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <>{children}</>;
}
