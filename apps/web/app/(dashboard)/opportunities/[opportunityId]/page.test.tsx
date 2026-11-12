import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen, fireEvent } from "@testing-library/react";
import { Suspense } from "react";
import OpportunityDetailPage from "./page";

const mockPush = vi.fn();
const mockUseOpportunity = vi.fn();
const mockRecordFeedback = vi.fn();
const mockRecordTradeOutcome = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("../../../../lib/hooks/useOpportunities", () => ({
  useOpportunity: (...args: unknown[]) => mockUseOpportunity(...args),
  useRecordFeedback: () => ({ mutateAsync: mockRecordFeedback, isPending: false }),
  useRecordTradeOutcome: () => ({ mutateAsync: mockRecordTradeOutcome, isPending: false }),
}));

const baseOpportunity = {
  id: "opp_1",
  organization_id: "org_1",
  listing_id: "listing_1",
  valuation_id: "val_1",
  material_version: 1,
  score: "85.5",
  state: "published",
  positive_factors: null,
  negative_factors: null,
  published_at: "2026-08-02T16:42:19Z",
  state_changed_at: "2026-08-02T16:42:19Z",
  created_at: "2026-08-02T16:42:19Z",
  valuation: {
    id: "val_1",
    listing_id: "listing_1",
    model_version: "v1",
    config_version: "c1",
    cost_assumptions_version: "ca1",
    expected_exit_price: "15000.00",
    exit_price_currency: "USD",
    all_in_acquisition: "11150.00",
    expected_net_resale: "14500.00",
    expected_net_profit: "3350.00",
    roi: "30.0",
    low_estimate: "13000.00",
    high_estimate: "16000.00",
    confidence: "0.75",
    comparable_count: 12,
    sample_dispersion: null,
    cost_breakdown: null,
    created_at: "2026-08-02T16:42:19Z",
  },
};

beforeEach(() => {
  mockPush.mockReset();
  mockUseOpportunity.mockReset();
  mockRecordFeedback.mockReset();
  mockRecordTradeOutcome.mockReset();
  mockRecordFeedback.mockResolvedValue(undefined);
  mockRecordTradeOutcome.mockResolvedValue(undefined);
});

async function renderPage(opportunityId: string): Promise<void> {
  await act(async () => {
    render(
      <Suspense fallback={<div>Loading route parameters</div>}>
        <OpportunityDetailPage
          params={Promise.resolve({ opportunityId })}
        />
      </Suspense>,
    );
    await Promise.resolve();
  });
}

describe("OpportunityDetailPage", () => {
  it("renders opportunity detail header and back button", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    expect(screen.getByText("Opportunity detail")).toBeInTheDocument();
    expect(screen.getAllByText(/opp_1/)).toHaveLength(2);
    expect(screen.getByRole("button", { name: /back to feed/i })).toBeInTheDocument();
  });

  it("shows LoadingState while loading", async () => {
    mockUseOpportunity.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getAllByText("Loading opportunity")).toHaveLength(2);
  });

  it("shows ErrorState on error", async () => {
    mockUseOpportunity.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("boom"),
    });

    await renderPage("opp_1");
    expect(screen.getByText("Unable to load opportunity")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("shows not found when data is null", async () => {
    mockUseOpportunity.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("missing");
    expect(screen.getByText("Opportunity not found")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /back to feed/i })).toBeInTheDocument();
  });

  it("renders cost waterfall valuation metrics", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    expect(screen.getByText("$11,150.00")).toBeInTheDocument();
    expect(screen.getByText("$15,000.00")).toBeInTheDocument();
    expect(screen.getByText("$3,350.00")).toBeInTheDocument();
    expect(screen.getByText("30.00%")).toBeInTheDocument();
    expect(screen.getByText("0.75%")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Published")).toBeInTheDocument();
  });

  it("renders back to feed link", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    const link = screen.getByRole("link", { name: /back to feed/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/opportunities");
  });

  it("renders decision action buttons", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    expect(screen.getByRole("button", { name: /contacted/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dismissed/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /purchased/i })).toBeInTheDocument();
  });

  it("records contacted feedback when Contacted button is clicked", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    const contactedButton = screen.getByRole("button", { name: /contacted/i });
    fireEvent.click(contactedButton);
    await vi.waitFor(() => {
      expect(mockRecordFeedback).toHaveBeenCalledWith({ decision: "contacted" });
    });
  });

  it("records dismissed feedback when Dismissed button is clicked", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    const dismissedButton = screen.getByRole("button", { name: /dismissed/i });
    fireEvent.click(dismissedButton);
    await vi.waitFor(() => {
      expect(mockRecordFeedback).toHaveBeenCalledWith({ decision: "dismissed" });
    });
  });

  it("opens outcome dialog when Purchased button is clicked", async () => {
    mockUseOpportunity.mockReturnValue({
      data: baseOpportunity,
      isLoading: false,
      isError: false,
      error: null,
    });

    await renderPage("opp_1");
    const purchasedButton = screen.getByRole("button", { name: /purchased/i });
    fireEvent.click(purchasedButton);
    await vi.waitFor(() => {
      expect(mockRecordFeedback).toHaveBeenCalledWith({ decision: "purchased" });
    });
    await vi.waitFor(() => {
      expect(screen.getByRole("dialog", { name: /record trade outcome/i })).toBeInTheDocument();
    });
  });
});
