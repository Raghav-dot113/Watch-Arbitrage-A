import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { QueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";

vi.mock("../api", () => ({
  listOpportunities: vi.fn(),
  getMe: vi.fn(),
  getHealth: vi.fn(),
}));

import { listOpportunities, getMe, getHealth } from "../api";
import { useOpportunities } from "./useOpportunities";
import { useIdentity } from "./useIdentity";
import { useHealth } from "./useHealth";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, gcTime: 0 },
  },
});

function wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.resetAllMocks();
  queryClient.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useOpportunities", () => {
  it("calls listOpportunities with params", async () => {
    const expected = {
      data: [{ id: "opp_1", state: "published" } as unknown as import("../api").Opportunity],
      meta: { trace_id: "t1", next_cursor: null, has_more: false },
    };
    vi.mocked(listOpportunities).mockResolvedValue(expected);

    const { result } = renderHook(() => useOpportunities({ limit: "20" }), {
      wrapper,
    });

    await act(async () => {
      await queryClient.fetchQuery({
        queryKey: ["opportunities", { limit: "20" }],
        queryFn: () => listOpportunities({ limit: "20" }),
      });
    });

    expect(vi.mocked(listOpportunities)).toHaveBeenCalledWith({ limit: "20" });
  });
});

describe("useIdentity", () => {
  it("calls getMe", async () => {
    const expected = {
      user: {
        id: "u1",
        email: "a@b.com",
        display_name: "A",
        created_at: "2026-08-02T16:42:19Z",
        updated_at: null,
      },
      memberships: [],
      organizations: [],
    } as any;
    vi.mocked(getMe).mockResolvedValue(expected);

    const { result } = renderHook(() => useIdentity(), { wrapper });

    await act(async () => {
      await queryClient.fetchQuery({
        queryKey: ["me"],
        queryFn: () => getMe(),
      });
    });

    expect(vi.mocked(getMe)).toHaveBeenCalled();
  });
});

describe("useHealth", () => {
  it("calls getHealth", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok", trace_id: "t1" });

    const { result } = renderHook(() => useHealth(), { wrapper });

    await act(async () => {
      await queryClient.fetchQuery({
        queryKey: ["health"],
        queryFn: () => getHealth(),
      });
    });

    expect(vi.mocked(getHealth)).toHaveBeenCalled();
  });
});
