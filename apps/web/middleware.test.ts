import { describe, expect, it, afterAll } from "vitest";
import { proxy } from "./proxy";
import { NextRequest } from "next/server";
import { signSession } from "./lib/session";

const origSecret = process.env.CHRONOARB_WEB_SESSION_SECRET;
process.env.CHRONOARB_WEB_SESSION_SECRET = "test-secret";

function request(pathname: string, token?: string): NextRequest {
  return new NextRequest(`http://localhost:3000${pathname}`, {
    headers: token ? { cookie: `chronoarb_session=${token}` } : {},
  });
}

const validToken = signSession({
  userId: "dev|dealer@example.com",
  email: "dealer@example.com",
  name: "dealer",
  orgId: "org_dev",
  orgName: "Dev Organization",
  role: "dealer",
});

describe("middleware route protection", () => {
  it("redirects to login when accessing a protected route without a session", async () => {
    const res = await proxy(request("/opportunities"));
    expect(res.status).toBe(302);
    const location = res.headers.get("location") ?? "";
    expect(location).toContain("/login");
    expect(location).toContain("callbackUrl=%2Fopportunities");
  });

  it("redirects to login for settings sub-routes", async () => {
    const res = await proxy(request("/settings/organization"));
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toContain("/login");
  });

  it("lets a valid session through on a protected route", async () => {
    const res = await proxy(request("/opportunities", validToken));
    expect(res.status).toBe(200);
  });

  it("lets a valid session through on settings routes", async () => {
    const res = await proxy(request("/settings/billing", validToken));
    expect(res.status).toBe(200);
  });

  it("lets the login page through without a session", async () => {
    const res = await proxy(request("/login"));
    expect(res.status).toBe(200);
  });

  it("lets api routes through without a session", async () => {
    const res = await proxy(request("/api/auth/session"));
    expect(res.status).toBe(200);
  });

  afterAll(() => {
    process.env.CHRONOARB_WEB_SESSION_SECRET = origSecret;
  });
});
