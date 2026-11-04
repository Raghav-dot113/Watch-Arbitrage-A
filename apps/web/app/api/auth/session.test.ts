import { describe, expect, it } from "vitest";
import { GET } from "./session/route";
import { NextRequest } from "next/server";

function requestWithCookie(token?: string): NextRequest {
  return new NextRequest("http://localhost:3000/api/auth/session", {
    headers: token ? { cookie: `chronoarb_session=${token}` } : {},
  });
}

describe("GET /api/auth/session", () => {
  it("returns 401 when no session cookie", async () => {
    const res = await GET(requestWithCookie());
    expect(res.status).toBe(401);
  });

  it("returns 401 when session cookie is invalid", async () => {
    const res = await GET(requestWithCookie("garbage.token.value"));
    expect(res.status).toBe(401);
  });

  it("returns 200 and user when session is valid", async () => {
    const { signSession } = await import("../../../lib/session");
    const token = signSession({
      userId: "dev|dealer@example.com",
      email: "dealer@example.com",
      name: "dealer",
      orgId: "org_dev",
      orgName: "Dev Organization",
      role: "dealer",
    });
    const res = await GET(requestWithCookie(token));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(body.user.email).toBe("dealer@example.com");
    expect(body.user.role).toBe("dealer");
  });
});
