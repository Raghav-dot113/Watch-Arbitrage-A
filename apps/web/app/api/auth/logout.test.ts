import { describe, expect, it } from "vitest";
import { POST } from "./logout/route";

describe("POST /api/auth/logout", () => {
  it("clears the session cookie", async () => {
    const res = await POST();
    expect(res.status).toBe(200);
    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("chronoarb_session=");
    expect(setCookie).toContain("Max-Age=0");
  });
});
