import type { Session } from "./session";

const SESSION_COOKIE = "chronoarb_session";

async function json<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return null as unknown as T;
  }
  return JSON.parse(text) as T;
}

export async function fetchSession(): Promise<Session | null> {
  const res = await fetch("/api/auth/session", {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    return null;
  }
  const body = await json<{ ok?: boolean; user?: Session }>(res);
  return body?.user ?? null;
}

export async function fetchLogin(email: string): Promise<Session> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const body = await json<{ error?: string }>(res);
    throw new Error(body?.error ?? "login failed");
  }
  const body = await json<{ ok?: boolean; user?: Session }>(res);
  if (!body?.user) {
    throw new Error("login returned no user");
  }
  return body.user;
}

export async function fetchLogout(): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
}

export { SESSION_COOKIE };
