import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "@chronoarb/api-client";
import { apiClient } from "./client";

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

  it("sends API requests without authentication headers", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({ data: [], meta: { trace_id: "t1" } }));
    vi.stubGlobal("fetch", fetchMock);

    await apiClient.getEnvelope("/api/v1/activity");

    expect(fetchMock).toHaveBeenCalledOnce();
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBeNull();
    expect(headers.get("X-Organization-ID")).toBeNull();
  });
});
