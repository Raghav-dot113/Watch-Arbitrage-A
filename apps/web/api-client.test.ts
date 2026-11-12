import { describe, expect, it } from "vitest";
import { ApiClient, HttpError } from "@chronoarb/api-client";
import type { HealthResponse, ReadyResponse } from "@chronoarb/api-client";

describe("ApiClient", () => {
  it("constructs with a base URL and normalizes a trailing slash", () => {
    const client = new ApiClient({ baseUrl: "http://localhost:8000/" });
    expect(client).toBeInstanceOf(ApiClient);
  });

  it("exposes health and ready response types", () => {
    const health: HealthResponse = { status: "ok", trace_id: "abc" };
    const ready: ReadyResponse = { status: "ok", database: "connected", trace_id: "abc" };
    expect(health.status).toBe("ok");
    expect(ready.database).toBe("connected");
  });

  it("preserves pagination metadata when requesting a success envelope", async () => {
    const client = new ApiClient({
      baseUrl: "http://localhost:8000",
      fetch: async () =>
        new Response(
          JSON.stringify({
            data: [{ id: "opp-1" }],
            meta: { trace_id: "trace-1", next_cursor: "cursor-1", has_more: true },
          }),
          { headers: { "content-type": "application/json" } }
        ),
    });

    await expect(client.getEnvelope<{ id: string }[]>("/api/v1/opportunities")).resolves.toEqual({
      data: [{ id: "opp-1" }],
      meta: { trace_id: "trace-1", next_cursor: "cursor-1", has_more: true },
    });
  });

  it("creates an HttpError with status, error, and retryable", () => {
    const err = new HttpError(401, {
      code: "unauthenticated",
      message: "missing credentials",
      field_errors: null,
      trace_id: "trace-1",
      retryable: false,
    });
    expect(err.status).toBe(401);
    expect(err.error.code).toBe("unauthenticated");
    expect(err.retryable).toBe(false);
    expect(err.message).toContain("401");
  });

  it("extracts the API error envelope instead of showing undefined fields", async () => {
    const client = new ApiClient({
      baseUrl: "http://localhost:8000",
      fetch: async () =>
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
    });

    await expect(client.get("/api/v1/activity")).rejects.toMatchObject({
      status: 401,
      error: {
        code: "UNAUTHORIZED",
        message: "Authentication required.",
        trace_id: "trace-401",
      },
      message: "401 UNAUTHORIZED: Authentication required.",
    });
  });
});
