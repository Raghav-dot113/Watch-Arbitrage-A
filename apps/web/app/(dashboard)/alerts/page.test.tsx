import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import AlertsPage from "./page";

const mockUseAlertRules = vi.fn();
const mockUseAlertDeliveries = vi.fn();
const mockCreateResult = {
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
};
const mockUseCreateAlertRule = vi.fn(() => mockCreateResult);
const mockUseUpdateAlertRule = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));
const mockUseDeleteAlertRule = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));
const mockUseRequestAlertTest = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue({ event_id: "evt_1", status: "pending" }),
  isPending: false,
}));

vi.mock("../../../lib/hooks/useAlerts", () => ({
  useAlertRules: (...args: unknown[]) => mockUseAlertRules(...args),
  useAlertDeliveries: (...args: unknown[]) => mockUseAlertDeliveries(...args),
  useCreateAlertRule: () => mockUseCreateAlertRule(),
  useUpdateAlertRule: () => mockUseUpdateAlertRule(),
  useDeleteAlertRule: () => mockUseDeleteAlertRule(),
  useRequestAlertTest: () => mockUseRequestAlertTest(),
}));

const baseAlertRule = {
  id: "ar_1",
  organization_id: "org_1",
  created_by: "u1",
  name: "High profit watches",
  filters: { reference_ids: ["ref_1"], min_profit: "100.00", max_acquisition: null, conditions: null },
  channels: ["in_app"],
  cooldown_minutes: 60,
  is_enabled: true,
  created_at: "2026-08-02T16:42:19Z",
  updated_at: "2026-08-02T16:42:19Z",
};

const baseDelivery = {
  id: "ad_1",
  rule_id: "ar_1",
  opportunity_id: "opp_1",
  material_version: 1,
  channel: "in_app",
  delivery_status: "sent",
  created_at: "2026-08-02T16:42:19Z",
};

beforeEach(() => {
  vi.restoreAllMocks();
  mockUseAlertRules.mockReset();
  mockUseAlertDeliveries.mockReset();
  mockUseCreateAlertRule.mockReset();
  mockUseUpdateAlertRule.mockReset();
  mockUseDeleteAlertRule.mockReset();
  mockUseRequestAlertTest.mockReset();
  mockCreateResult.mutateAsync.mockReset();
  mockCreateResult.mutateAsync.mockResolvedValue(undefined);
  mockUseAlertRules.mockReturnValue({
    data: [baseAlertRule],
    isLoading: false,
    isError: false,
    error: null,
  });
  mockUseAlertDeliveries.mockReturnValue({
    data: [baseDelivery],
    isLoading: false,
  });
  mockUseCreateAlertRule.mockReturnValue(mockCreateResult);
  mockUseUpdateAlertRule.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseDeleteAlertRule.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseRequestAlertTest.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ event_id: "evt_1", status: "pending" }),
    isPending: false,
  });
});

describe("AlertsPage", () => {
  it("renders alert rules with channels and status", () => {
    render(<AlertsPage />);
    expect(screen.getByText("High profit watches")).toBeInTheDocument();
    expect(screen.getByText(/In-app/)).toBeInTheDocument();
    expect(screen.getByText(/60 min/)).toBeInTheDocument();
    expect(screen.getByText(/Enabled/)).toBeInTheDocument();
  });

  it("renders recent deliveries", () => {
    render(<AlertsPage />);
    expect(screen.getByText("Recent Deliveries")).toBeInTheDocument();
    expect(screen.getByText(/opp_1/)).toBeInTheDocument();
    expect(screen.getByText("sent")).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseAlertRules.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    render(<AlertsPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows ErrorState on error", () => {
    mockUseAlertRules.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("Failed to load"),
    });

    render(<AlertsPage />);
    expect(screen.getByText("Unable to load alert rules")).toBeInTheDocument();
  });

  it("shows empty state when no alert rules", () => {
    mockUseAlertRules.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<AlertsPage />);
    expect(screen.getByText("No alert rules")).toBeInTheDocument();
    const createButtons = screen.getAllByRole("button", {
      name: /create alert rule/i,
    });
    expect(createButtons.length).toBeGreaterThanOrEqual(1);
  });
});
