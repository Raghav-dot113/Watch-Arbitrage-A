"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchSession, fetchLogin, fetchLogout } from "../lib/auth-client";
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

  const refresh = async () => {
    setIsLoading(true);
    try {
      setUser(await fetchSession());
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const login = async (email: string) => {
    const session = await fetchLogin(email);
    setUser(session);
  };

  const logout = async () => {
    await fetchLogout();
    setUser(null);
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
