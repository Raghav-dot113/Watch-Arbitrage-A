import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import OpportunitiesPage from "./page";

const mockPush = vi.fn();
const mockUseOpportunities = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("../../../lib/hooks/useOpportunities", () => ({
  useOpportunities: (...args: unknown[]) => mockUseOpportunities(...args),
}));

const baseOpportunity = {
  id: "opp_1",
  state: "published",
  score: "85.5",
  created_at: "2026-08-02T16:42:19Z",
  valuation: {
    expected_net_profit: "2500.00",
    roi: "32.4",
  },
};

beforeEach(() => {
  mockPush.mockReset();
  mockUseOpportunities.mockReset();
});

describe("OpportunitiesPage", () => {
  it("renders the page header", () => {
    mockUseOpportunities.mockReturnValue({
      data: { data: [], meta: { trace_id: "t1", next_cursor: null, has_more: false } },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByText("Opportunities")).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseOpportunities.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getAllByText("Loading opportunities")).toHaveLength(2);
  });

  it("shows ErrorState on error", () => {
    mockUseOpportunities.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("boom"),
    });

    render(<OpportunitiesPage />);
    expect(screen.getByText("Unable to load opportunities")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("shows EmptyState when no opportunities", () => {
    mockUseOpportunities.mockReturnValue({
      data: { data: [], meta: { trace_id: "t1", next_cursor: null, has_more: false } },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByText("No opportunities")).toBeInTheDocument();
  });

  it("renders opportunity rows in the data table", () => {
    mockUseOpportunities.mockReturnValue({
      data: {
        data: [baseOpportunity],
        meta: { trace_id: "t1", next_cursor: null, has_more: false },
      },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    const row = screen.getByTestId("opportunity-row-0");
    expect(row).toBeInTheDocument();
    expect(row).toHaveTextContent("opp_1");
    expect(row).toHaveTextContent("Published");
    expect(row).toHaveTextContent("$2,500.00");
  });

  it("navigates to opportunity detail on row click", () => {
    mockUseOpportunities.mockReturnValue({
      data: {
        data: [baseOpportunity],
        meta: { trace_id: "t1", next_cursor: null, has_more: false },
      },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    const row = screen.getByTestId("opportunity-row-0") as HTMLElement;
    fireEvent.click(row);
    expect(mockPush).toHaveBeenCalledWith("/opportunities/opp_1");
  });
});
