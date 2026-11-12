import { describe, expect, it } from "vitest";
import { GET } from "./session/route";
import { NextRequest } from "next/server";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  vi.stubEnv("NODE_ENV", "development");
  vi.stubEnv("CHRONOARB_AUTH_MODE", "dev");
  vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://api.test");
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

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

  it("refreshes an expired API token and rotates the session cookie", async () => {
    const { signSession } = await import("../../../lib/session");
    const token = signSession({
      userId: "usr_old",
      email: "dealer@example.com",
      name: "Old name",
      orgId: "org_old",
      role: "dealer",
      apiToken: "expired-api-token",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json({
          data: {
            access_token: "fresh-api-token",
            user_id: "usr_fresh",
            email: "dealer@example.com",
            display_name: "Dealer",
            organization_id: "org_fresh",
            organization_name: "Fresh Organization",
            role: "owner",
          },
        }),
      ),
    );

    const response = await GET(
      new NextRequest("http://localhost:3000/api/auth/session?refresh=1", {
        headers: { cookie: `chronoarb_session=${token}` },
      }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      user: {
        userId: "usr_fresh",
        apiToken: "fresh-api-token",
        orgId: "org_fresh",
      },
    });
    expect(fetch).toHaveBeenCalledWith(
      "http://api.test/api/v1/identity/dev-token",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "dealer@example.com" }),
      }),
    );
    expect(response.headers.get("set-cookie")).toContain("chronoarb_session=");
  });
});
