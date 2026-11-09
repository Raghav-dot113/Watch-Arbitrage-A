import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "./login/route";

const developmentToken = {
  access_token: "dev-api-token",
  user_id: "usr_demo_dealer",
  email: "dealer@example.com",
  display_name: "Demo Dealer",
  organization_id: "org_demo",
  organization_name: "ChronoArb Demo",
  role: "dealer",
};

function jsonBody(email: string): Request {
  return new Request("http://localhost:3000/api/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

beforeEach(() => {
  vi.stubEnv("NODE_ENV", "development");
  vi.stubEnv("CHRONOARB_AUTH_MODE", "dev");
  vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://api.test");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      Response.json({ data: developmentToken }),
    ),
  );
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("POST /api/auth/login", () => {
  it("issues an API-backed session for a seeded local account", async () => {
    const res = await POST(jsonBody("dealer@example.com"));
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toMatchObject({
      ok: true,
      user: {
        email: "dealer@example.com",
        orgId: "org_demo",
        apiToken: "dev-api-token",
      },
    });
    expect(fetch).toHaveBeenCalledWith(
      "http://api.test/api/v1/identity/dev-token",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "dealer@example.com" }),
      }),
    );
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
    expect(session?.apiToken).toBe("dev-api-token");
  });

  it("returns an explicit error when the API has no matching demo user", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json({ detail: "No local demo account matches that email" }, { status: 401 }),
      ),
    );

    const response = await POST(jsonBody("unknown@example.com"));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      error: "No local demo account matches that email.",
    });
  });

  it("disables development login outside development mode", async () => {
    vi.stubEnv("NODE_ENV", "production");

    const response = await POST(jsonBody("dealer@example.com"));

    expect(response.status).toBe(404);
    expect(fetch).not.toHaveBeenCalled();
  });
});
