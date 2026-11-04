import { describe, expect, it } from "vitest";
import { POST } from "./login/route";

function jsonBody(email: string): Request {
  return new Request("http://localhost:3000/api/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

describe("POST /api/auth/login", () => {
  it("issues a session cookie for a valid email", async () => {
    const res = await POST(jsonBody("dealer@example.com"));
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toMatchObject({
      ok: true,
      user: {
        email: "dealer@example.com",
        orgId: "org_dev",
      },
    });
    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("chronoarb_session=");
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("Path=/");
  });

  it("returns 400 when email is missing", async () => {
    const res = await POST(
      new Request("http://localhost:3000/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({}),
      })
    );
    expect(res.status).toBe(400);
  });

  it("returns 400 when email is empty", async () => {
    const res = await POST(jsonBody(""));
    expect(res.status).toBe(400);
  });

  it("returns 400 for invalid json", async () => {
    const res = await POST(
      new Request("http://localhost:3000/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "not-json",
      })
    );
    expect(res.status).toBe(400);
  });
});

describe("session cookie round-trip", () => {
  it("cookie set by login is verifiable", async () => {
    const res = await POST(jsonBody("dealer@example.com"));
    const setCookie = res.headers.get("set-cookie") ?? "";
    const cookieValue = setCookie.split(";")[0]?.split("=")[1] ?? "";
    const { verifySession } = await import("../../../lib/session");
    const session = verifySession(cookieValue);
    expect(session).not.toBeNull();
    expect(session?.email).toBe("dealer@example.com");
  });
});
