import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AdminPage from "./page";

const mockUseSources = vi.fn();
const mockUseUpdateSource = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));
const mockUseFeatureFlags = vi.fn();
const mockUseUpdateFeatureFlag = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));
const mockUseAuditEvents = vi.fn();
const mockUseUnmatchedListings = vi.fn();
const mockUseResolveUnmatchedListing = vi.fn(() => ({
  mutateAsync: vi.fn().mockResolvedValue(undefined),
  isPending: false,
}));
const mockUseDuplicateGroups = vi.fn();

vi.mock("../../../lib/hooks/useAdmin", () => ({
  useSources: (...args: unknown[]) => mockUseSources(...args),
  useUpdateSource: () => mockUseUpdateSource(),
  useFeatureFlags: (...args: unknown[]) => mockUseFeatureFlags(...args),
  useUpdateFeatureFlag: () => mockUseUpdateFeatureFlag(),
  useAuditEvents: (...args: unknown[]) => mockUseAuditEvents(...args),
  useUnmatchedListings: (...args: unknown[]) => mockUseUnmatchedListings(...args),
  useResolveUnmatchedListing: () => mockUseResolveUnmatchedListing(),
  useDuplicateGroups: (...args: unknown[]) => mockUseDuplicateGroups(...args),
}));

const baseSource = {
  id: "src_1",
  source_key: "ebay",
  display_name: "eBay",
  adapter_version: "1.0.0",
  access_mode: "public",
  is_enabled: true,
  health_status: "unknown",
  last_fetched_at: null,
};

const baseFlag = {
  id: "flag_1",
  key: "new_ui",
  description: "New UI flag",
  enabled: true,
  organization_ids: null,
  rollout_pct: 100,
  expires_at: null,
  created_at: "2026-08-02T16:42:19Z",
};

const baseAuditEvent = {
  id: "audit_1",
  organization_id: "org_1",
  user_id: "user_1",
  action: "admin.source_enabled",
  resource_type: "source",
  resource_id: "src_1",
  details: { is_enabled: true },
  trace_id: "trace_1",
  created_at: "2026-08-02T16:42:19Z",
};

const baseUnmatched = {
  id: "unmatched_1",
  reference_id: "ref_1",
  source_key: "ebay",
  title: "Vintage Watch",
  external_url: "https://ebay.com/item/1",
  match_method: null,
  observation_at: "2026-08-02T16:42:19Z",
};

const baseDuplicate = {
  id: "dup_1",
  representative_id: "listing_1",
  method: "fuzzy_match",
  confidence: "0.95",
  listing_ids: ["listing_1", "listing_2"],
  created_at: "2026-08-02T16:42:19Z",
};

beforeEach(() => {
  vi.restoreAllMocks();
  mockUseSources.mockReset();
  mockUseUpdateSource.mockReset();
  mockUseFeatureFlags.mockReset();
  mockUseUpdateFeatureFlag.mockReset();
  mockUseAuditEvents.mockReset();
  mockUseUnmatchedListings.mockReset();
  mockUseResolveUnmatchedListing.mockReset();
  mockUseDuplicateGroups.mockReset();

  mockUseSources.mockReturnValue({
    data: [baseSource],
    isLoading: false,
  });
  mockUseUpdateSource.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseFeatureFlags.mockReturnValue({
    data: [baseFlag],
    isLoading: false,
  });
  mockUseUpdateFeatureFlag.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseAuditEvents.mockReturnValue({
    data: [baseAuditEvent],
    isLoading: false,
  });
  mockUseUnmatchedListings.mockReturnValue({
    data: [baseUnmatched],
    isLoading: false,
  });
  mockUseResolveUnmatchedListing.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseDuplicateGroups.mockReturnValue({
    data: [baseDuplicate],
    isLoading: false,
  });
});

describe("AdminPage", () => {
  it("renders admin console header", () => {
    render(<AdminPage />);
    expect(screen.getByText("Admin Console")).toBeInTheDocument();
    expect(screen.getByText("Data Sources")).toBeInTheDocument();
    expect(screen.getByText("Feature Flags")).toBeInTheDocument();
    expect(screen.getByText("Audit Events")).toBeInTheDocument();
    expect(screen.getByText("Unmatched Listings")).toBeInTheDocument();
    expect(screen.getByText("Duplicate Groups")).toBeInTheDocument();
  });

  it("renders sources tab by default", () => {
    render(<AdminPage />);
    expect(screen.getByText("eBay")).toBeInTheDocument();
    expect(screen.queryByText("EBAY")).not.toBeInTheDocument();
    expect(screen.getByText(/1\.0\.0/)).toBeInTheDocument();
  });

  it("shows enable/disable button for sources", () => {
    render(<AdminPage />);
    const toggleButton = screen.getByRole("button", { name: /disable/i });
    expect(toggleButton).toBeInTheDocument();
  });

  it("opens source toggle dialog and calls updateSource", async () => {
    const mutateAsync = mockUseUpdateSource().mutateAsync;
    render(<AdminPage />);

    fireEvent.click(screen.getByRole("button", { name: /disable/i }));

    expect(screen.getByText("Disable Source")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /disable/i }));

    expect(mutateAsync).toHaveBeenCalledWith({
      sourceId: "src_1",
      isEnabled: false,
    });
  });

  it("renders feature flags tab", () => {
    render(<AdminPage />);
    fireEvent.click(screen.getByRole("tab", { name: /feature flags/i }));
    expect(screen.getByText("new_ui")).toBeInTheDocument();
    expect(screen.getByText("New UI flag")).toBeInTheDocument();
  });

  it("opens feature flag edit dialog", () => {
    render(<AdminPage />);
    fireEvent.click(screen.getByRole("tab", { name: /feature flags/i }));
    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    expect(screen.getByText("Edit Feature Flag")).toBeInTheDocument();
  });

  it("renders audit events tab", () => {
    render(<AdminPage />);
    fireEvent.click(screen.getByRole("tab", { name: /audit events/i }));
    expect(screen.getByText("admin.source_enabled")).toBeInTheDocument();
    expect(screen.getByText("source")).toBeInTheDocument();
  });

  it("renders unmatched listings tab", () => {
    render(<AdminPage />);
    fireEvent.click(screen.getByRole("tab", { name: /unmatched listings/i }));
    expect(screen.getByText("Vintage Watch")).toBeInTheDocument();
    expect(screen.getByText("ebay")).toBeInTheDocument();
  });

  it("opens resolve dialog for unmatched listing", () => {
    render(<AdminPage />);
    fireEvent.click(screen.getByRole("tab", { name: /unmatched listings/i }));
    fireEvent.click(screen.getByRole("button", { name: /resolve/i }));
    expect(screen.getByText("Resolve Unmatched Listing")).toBeInTheDocument();
  });

  it("renders duplicate groups tab", () => {
    render(<AdminPage />);
    fireEvent.click(screen.getByRole("tab", { name: /duplicate groups/i }));
    expect(screen.getByText("Duplicate Group")).toBeInTheDocument();
    expect(screen.getByText("listing_1")).toBeInTheDocument();
  });

  it("shows empty state when no sources", () => {
    mockUseSources.mockReturnValue({
      data: [],
      isLoading: false,
    });
    render(<AdminPage />);
    expect(screen.getByText("No sources")).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseSources.mockReturnValue({
      data: null,
      isLoading: true,
    });
    render(<AdminPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });
});
