import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "@chronoarb/api-client";
import {
  apiClient,
  setAuthOrganizationId,
  setAuthToken,
} from "./client";

afterEach(() => {
  setAuthToken(null);
  setAuthOrganizationId(null);
  vi.unstubAllGlobals();
});

beforeEach(() => {
  setAuthToken(null);
  setAuthOrganizationId(null);
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

  it("adds the selected organization to authenticated requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ data: [], meta: { trace_id: "trace-1" } }),
    );
    vi.stubGlobal("fetch", fetchMock);
    setAuthToken("api-token");
    setAuthOrganizationId("org-1");

    await apiClient.getEnvelope("/api/v1/activity", {
      headers: { Authorization: "Bearer api-token" },
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).get("X-Organization-ID")).toBe("org-1");
  });

  it("refreshes the API session and retries one unauthorized request", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json(
          {
            error: {
              code: "UNAUTHORIZED",
              message: "Authentication required.",
              field_errors: {},
              trace_id: "trace-401",
              retryable: false,
            },
          },
          { status: 401 },
        ),
      )
      .mockResolvedValueOnce(
        Response.json({
          ok: true,
          user: { apiToken: "refreshed-token", orgId: "org-2" },
        }),
      )
      .mockResolvedValueOnce(
        Response.json({ data: [], meta: { trace_id: "trace-2" } }),
      );
    vi.stubGlobal("fetch", fetchMock);
    setAuthToken("expired-token");
    setAuthOrganizationId("org-1");

    await expect(
      apiClient.getEnvelope("/api/v1/activity", {
        headers: { Authorization: "Bearer expired-token" },
      }),
    ).resolves.toMatchObject({ data: [] });

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/auth/session?refresh=1",
      expect.objectContaining({ cache: "no-store" }),
    );
    const [, retryInit] = fetchMock.mock.calls[2] as [string, RequestInit];
    const retryHeaders = new Headers(retryInit.headers);
    expect(retryHeaders.get("Authorization")).toBe("Bearer refreshed-token");
    expect(retryHeaders.get("X-Organization-ID")).toBe("org-2");
  });
});
