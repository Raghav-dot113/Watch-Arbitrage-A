import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import WatchesPage from "./page";

vi.mock("../../../components/bryntum/ChronoArbGrid", async () => {
  const { MockChronoArbGrid } = await import("../../../test-utils/ChronoArbGridMock");
  return { ChronoArbGrid: MockChronoArbGrid };
});

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

function openCreateDialog() {
  const createButton = screen.getAllByRole("button", {
    name: /create watch list/i,
  })[0];
  if (!createButton) {
    throw new Error("Create watch list button not found");
  }
  fireEvent.click(createButton);
}

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
    expect(screen.getByText(/ref_1/)).toBeInTheDocument();
    expect(screen.getByText(/ref_2/)).toBeInTheDocument();
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

  it("opens the create dialog from the empty state", () => {
    mockUseWatchlists.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<WatchesPage />);
    openCreateDialog();

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Create Watch List")).toBeInTheDocument();
  });

  it("creates a watch list with a name and no reference IDs", async () => {
    mockUseWatchlists.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<WatchesPage />);
    openCreateDialog();
    fireEvent.change(screen.getByRole("textbox", { name: /^name/i }), {
      target: { value: "  My New List  " },
    });
    fireEvent.submit(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() =>
      expect(mockCreateResult.mutateAsync).toHaveBeenCalledWith({
        name: "My New List",
        reference_ids: [],
      }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
  });

  it("shows the API error and keeps the dialog open when create fails", async () => {
    mockUseWatchlists.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });
    mockCreateResult.mutateAsync.mockRejectedValueOnce(
      new Error(
        "Reference IDs must be unique and identify active catalog references",
      ),
    );

    render(<WatchesPage />);
    openCreateDialog();
    fireEvent.change(screen.getByRole("textbox", { name: /^name/i }), {
      target: { value: "My List" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: /reference ids/i }), {
      target: { value: "missing-ref" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /^create$/i }));

    expect(
      await screen.findByText(
        "Reference IDs must be unique and identify active catalog references",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(mockCreateResult.mutateAsync).toHaveBeenCalledWith({
      name: "My List",
      reference_ids: ["missing-ref"],
    });
  });

  it("validates that a name is required before creating", async () => {
    mockUseWatchlists.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<WatchesPage />);
    openCreateDialog();
    fireEvent.change(screen.getByRole("textbox", { name: /^name/i }), {
      target: { value: "   " },
    });
    fireEvent.submit(screen.getByRole("button", { name: /^create$/i }));

    expect(
      await screen.findByText("Enter a name for this watch list."),
    ).toBeInTheDocument();
    expect(mockCreateResult.mutateAsync).not.toHaveBeenCalled();
  });
});
