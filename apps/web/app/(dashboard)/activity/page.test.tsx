import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ActivityPage from "./page";

const mockUseActivity = vi.fn();
const mockUseTradeOutcomes = vi.fn();

vi.mock("../../../lib/hooks/useActivity", () => ({
  useActivity: (...args: unknown[]) => mockUseActivity(...args),
  useTradeOutcomes: (...args: unknown[]) => mockUseTradeOutcomes(...args),
}));

const baseActivity = {
  id: "act_1",
  event_type: "feedback" as const,
  user_id: "u1",
  opportunity_id: "opp_1",
  reference_id: "ref_1",
  decision: "contacted",
  notes: "Seller contacted",
  acquisition_price: null,
  acquisition_currency: null,
  resale_price: null,
  resale_currency: null,
  actual_profit: null,
  days_to_sell: null,
  created_at: "2026-08-02T16:42:19Z",
};

const baseOutcome = {
  id: "to_1",
  organization_id: "org_1",
  user_id: "u1",
  opportunity_id: "opp_1",
  reference_id: "ref_1",
  acquisition_price: "11000.00",
  acquisition_currency: "USD",
  resale_price: "15000.00",
  resale_currency: "USD",
  actual_profit: "4000.00",
  days_to_sell: 5,
  created_at: "2026-08-02T16:42:19Z",
};

beforeEach(() => {
  vi.restoreAllMocks();
  mockUseActivity.mockReset();
  mockUseTradeOutcomes.mockReset();
  mockUseActivity.mockReturnValue({
    data: [baseActivity],
    isLoading: false,
    isError: false,
    error: null,
  });
  mockUseTradeOutcomes.mockReturnValue({
    data: [baseOutcome],
    isLoading: false,
  });
});

describe("ActivityPage", () => {
  it("renders activity items", () => {
    render(<ActivityPage />);
    expect(screen.getByText("Activity Feed")).toBeInTheDocument();
    expect(screen.getByText("Feedback")).toBeInTheDocument();
    expect(screen.getByText("contacted")).toBeInTheDocument();
    expect(screen.getByText("Seller contacted")).toBeInTheDocument();
  });

  it("renders trade outcomes section", () => {
    render(<ActivityPage />);
    expect(screen.getByText("Trade Outcomes")).toBeInTheDocument();
    expect(screen.getByText(/11000\.00/)).toBeInTheDocument();
    expect(screen.getByText(/15000\.00/)).toBeInTheDocument();
    expect(screen.getByText(/4000\.00/)).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseActivity.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    render(<ActivityPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows ErrorState on error", () => {
    mockUseActivity.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("Failed to load"),
    });

    render(<ActivityPage />);
    expect(screen.getByText("Unable to load activity")).toBeInTheDocument();
  });

  it("shows empty state when no activity", () => {
    mockUseActivity.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });
    mockUseTradeOutcomes.mockReturnValue({
      data: [],
      isLoading: false,
    });

    render(<ActivityPage />);
    expect(screen.getByText("No activity")).toBeInTheDocument();
    expect(screen.getByText("No trade outcomes")).toBeInTheDocument();
  });
});
