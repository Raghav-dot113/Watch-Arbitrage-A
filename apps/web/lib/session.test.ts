import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  signSession,
  verifySession,
  type Session,
} from "./session";

const env = process.env;

beforeEach(() => {
  env.CHRONOARB_WEB_SESSION_SECRET = "test-secret";
});

afterEach(() => {
  env.CHRONOARB_WEB_SESSION_SECRET = env.CHRONOARB_WEB_SESSION_SECRET;
});

describe("signSession / verifySession", () => {
  it("round-trips a valid session", () => {
    const session: Session = {
      userId: "dev|user@example.com",
      email: "user@example.com",
      name: "user",
      orgId: "org_dev",
      orgName: "Dev Organization",
      role: "dealer",
    };
    const token = signSession(session);
    const decoded = verifySession(token);
    expect(decoded).not.toBeNull();
    expect(decoded?.userId).toBe(session.userId);
    expect(decoded?.email).toBe(session.email);
    expect(decoded?.role).toBe("dealer");
    expect(typeof decoded?.iat).toBe("number");
  });

  it("rejects a tampered signature", () => {
    const token = signSession({ userId: "a", email: "a@b.com" });
    const [header, payload, sig] = token.split(".");
    if (typeof sig !== "string") {
      throw new Error("unexpected token shape");
    }
    const tampered = `${header}.${payload}.${sig.replace(/./g, "a")}`;
    expect(verifySession(tampered)).toBeNull();
  });

  it("rejects a malformed token", () => {
    expect(verifySession("not.a.token")).toBeNull();
    expect(verifySession("")).toBeNull();
    expect(verifySession("a.b")).toBeNull();
  });

  it("rejects a token signed with a different secret", () => {
    const token = signSession({ userId: "a", email: "a@b.com" });
    const original = env.CHRONOARB_WEB_SESSION_SECRET;
    env.CHRONOARB_WEB_SESSION_SECRET = "other-secret";
    expect(verifySession(token)).toBeNull();
    env.CHRONOARB_WEB_SESSION_SECRET = original;
  });
});
