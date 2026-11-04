import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import WatchesPage from "./page";

const mockUseWatchlists = vi.fn();
const mockCreateResult = {
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
};
const mockUseCreateWatchList = vi.fn(() => mockCreateResult);
const mockUseUpdateWatchList = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));
const mockUseDeleteWatchList = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));

vi.mock("../../../lib/hooks/useWatchlists", () => ({
  useWatchlists: (...args: unknown[]) => mockUseWatchlists(...args),
  useCreateWatchList: () => mockUseCreateWatchList(),
  useUpdateWatchList: () => mockUseUpdateWatchList(),
  useDeleteWatchList: () => mockUseDeleteWatchList(),
}));

const baseWatchList = {
  id: "wl_1",
  organization_id: "org_1",
  name: "My Watch List",
  created_at: "2026-08-02T16:42:19Z",
  entries: [
    { id: "e1", watch_list_id: "wl_1", reference_id: "ref_1", created_at: "2026-08-02T16:42:19Z" },
    { id: "e2", watch_list_id: "wl_1", reference_id: "ref_2", created_at: "2026-08-02T16:42:19Z" },
  ],
};

beforeEach(() => {
  vi.restoreAllMocks();
  mockUseWatchlists.mockReset();
  mockUseCreateWatchList.mockReset();
  mockUseUpdateWatchList.mockReset();
  mockUseDeleteWatchList.mockReset();
  mockUseCreateWatchList.mockReturnValue(mockCreateResult);
  mockUseUpdateWatchList.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseDeleteWatchList.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockCreateResult.mutateAsync.mockReset();
  mockCreateResult.mutateAsync.mockResolvedValue(undefined);
});

describe("WatchesPage", () => {
  it("renders watch lists with entries", () => {
    mockUseWatchlists.mockReturnValue({
      data: [baseWatchList],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<WatchesPage />);
    expect(screen.getByText("My Watch List")).toBeInTheDocument();
    expect(screen.getByText(/2 entries/)).toBeInTheDocument();
    expect(screen.getByText("ref_1")).toBeInTheDocument();
    expect(screen.getByText("ref_2")).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseWatchlists.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    render(<WatchesPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows ErrorState on error", () => {
    mockUseWatchlists.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("Failed to load"),
    });

    render(<WatchesPage />);
    expect(screen.getByText("Unable to load watch lists")).toBeInTheDocument();
  });

  it("shows empty state when no watch lists", () => {
    mockUseWatchlists.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<WatchesPage />);
    expect(screen.getByText("No watch lists")).toBeInTheDocument();
    const createButtons = screen.getAllByRole("button", {
      name: /create watch list/i,
    });
    expect(createButtons.length).toBeGreaterThanOrEqual(1);
  });
});
