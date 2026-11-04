import { createHmac, timingSafeEqual } from "node:crypto";

const SESSION_COOKIE = "chronoarb_session";
const SESSION_MAX_AGE = 7 * 24 * 60 * 60;

export interface Session {
  userId: string;
  email: string;
  name?: string | null;
  orgId?: string | null;
  orgName?: string | null;
  role?: string | null;
}

export type SessionPayload = Session & { iat: number; exp?: number };

function sessionSecret(): string {
  return process.env.CHRONOARB_WEB_SESSION_SECRET ?? "dev-secret-change-me";
}

function base64url(input: string): string {
  return Buffer.from(input, "utf8")
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function base64urlObj(obj: unknown): string {
  return base64url(JSON.stringify(obj));
}

function base64urlDecode(input: string): Buffer {
  let base64 = input.replace(/-/g, "+").replace(/_/g, "/");
  while (base64.length % 4 !== 0) {
    base64 += "=";
  }
  return Buffer.from(base64, "base64");
}

export function signSession(session: Session): string {
  const header = base64urlObj({ alg: "HS256", typ: "JWT" });
  const payload = base64urlObj({ ...session, iat: Math.floor(Date.now() / 1000) });
  const signature = createHmac("sha256", sessionSecret())
    .update(`${header}.${payload}`)
    .digest("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  return `${header}.${payload}.${signature}`;
}

export function verifySession(token: string): SessionPayload | null {
  const parts = token.split(".");
  if (parts.length !== 3) {
    return null;
  }
  const [headerB64, payloadB64, sigB64] = parts;
  if (
    typeof headerB64 !== "string" ||
    typeof payloadB64 !== "string" ||
    typeof sigB64 !== "string"
  ) {
    return null;
  }
  const expected = createHmac("sha256", sessionSecret())
    .update(`${headerB64}.${payloadB64}`)
    .digest("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  if (sigB64.length !== expected.length) {
    return null;
  }
  if (
    !timingSafeEqual(Buffer.from(sigB64, "ascii"), Buffer.from(expected, "ascii"))
  ) {
    return null;
  }

  let payload: SessionPayload;
  try {
    payload = JSON.parse(base64urlDecode(payloadB64).toString("utf-8"));
  } catch {
    return null;
  }

  if (payload.exp && Date.now() > payload.exp * 1000) {
    return null;
  }

  return payload;
}

export function getSessionCookieOptions(): {
  httpOnly: boolean;
  secure: boolean;
  sameSite: "lax";
  path: string;
  maxAge: number;
} {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  };
}

export { SESSION_COOKIE };
