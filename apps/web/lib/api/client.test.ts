import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "@chronoarb/api-client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ApiClient", () => {
  it("calls the default fetch implementation with its global receiver", async () => {
    const fetchMock = vi.fn(function (this: typeof globalThis) {
      expect(this).toBe(globalThis);
      return Promise.resolve(
        new Response(JSON.stringify({ data: { status: "ok" }, meta: null }), {
          headers: { "content-type": "application/json" },
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const client = new ApiClient({ baseUrl: "http://localhost:8000" });

    await expect(client.get("/health")).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
