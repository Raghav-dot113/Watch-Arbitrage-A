"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { fetchSession, fetchLogin, fetchLogout } from "../lib/auth-client";
import { setAuthToken } from "../lib/api/client";
import type { Session } from "../lib/session";

interface AuthContextType {
  user: Session | null;
  isLoading: boolean;
  login: (email: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const applySession = useCallback((session: Session | null) => {
    setAuthToken(session?.apiToken ?? null);
    setUser(session);
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      applySession(await fetchSession());
    } catch {
      applySession(null);
    } finally {
      setIsLoading(false);
    }
  }, [applySession]);

  useEffect(() => {
    let active = true;
    void fetchSession()
      .then((session) => {
        if (active) applySession(session);
      })
      .catch(() => {
        if (active) applySession(null);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [applySession]);

  const login = async (email: string) => {
    const session = await fetchLogin(email);
    setAuthToken(session.apiToken ?? null);
    setUser(session);
  };

  const logout = async () => {
    try {
      await fetchLogout();
    } finally {
      setAuthToken(null);
      setUser(null);
    }
  };

  const value: AuthContextType = { user, isLoading, login, logout, refresh };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
