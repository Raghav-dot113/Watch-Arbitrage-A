import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SettingsPage from "./page";

const mockUseOrganizationSettings = vi.fn();
const mockUseUpdateOrganizationSettings = vi.fn();
const mockUseSubscription = vi.fn();
const mockUseCreateCheckoutSession = vi.fn();
const mockUseCreatePortalSession = vi.fn();
const mockUseIntegrationStatus = vi.fn();
const mockUseLinkTelegram = vi.fn();
const mockUseUnlinkTelegram = vi.fn();
const mockUseRegisterPushDevice = vi.fn();
const mockUseUnregisterPushDevice = vi.fn();

vi.mock("../../../../lib/hooks/useSettings", () => ({
  useOrganizationSettings: (...args: unknown[]) =>
    mockUseOrganizationSettings(...args),
  useUpdateOrganizationSettings: () => mockUseUpdateOrganizationSettings(),
  useSubscription: (...args: unknown[]) => mockUseSubscription(...args),
  useCreateCheckoutSession: () => mockUseCreateCheckoutSession(),
  useCreatePortalSession: () => mockUseCreatePortalSession(),
  useIntegrationStatus: (...args: unknown[]) =>
    mockUseIntegrationStatus(...args),
  useLinkTelegram: () => mockUseLinkTelegram(),
  useUnlinkTelegram: () => mockUseUnlinkTelegram(),
  useRegisterPushDevice: () => mockUseRegisterPushDevice(),
  useUnregisterPushDevice: () => mockUseUnregisterPushDevice(),
}));

const baseSettings = {
  currency: "USD",
  timezone: "America/New_York",
  default_fees: {
    buyer_fee: "10.00",
    tax_and_duty: null,
    inbound_shipping: null,
    authentication_cost: null,
    service_reserve: null,
    financing_cost: null,
    acquisition_risk_reserve: null,
    selling_fee: null,
    outbound_shipping: null,
    resale_payment_cost: null,
    exit_risk_reserve: null,
  },
};

const baseSubscription = {
  id: "sub_1",
  status: "active",
  plan_id: "pro_monthly",
  current_period_start: "2026-08-01T00:00:00Z",
  current_period_end: "2026-09-01T00:00:00Z",
  trial_end: null,
};

const baseIntegrationStatus = {
  telegram_status: "disconnected",
  telegram_link_expires_at: null,
  push_devices: [],
};

beforeEach(() => {
  vi.restoreAllMocks();
  mockUseOrganizationSettings.mockReset();
  mockUseUpdateOrganizationSettings.mockReset();
  mockUseSubscription.mockReset();
  mockUseCreateCheckoutSession.mockReset();
  mockUseCreatePortalSession.mockReset();
  mockUseIntegrationStatus.mockReset();
  mockUseLinkTelegram.mockReset();
  mockUseUnlinkTelegram.mockReset();
  mockUseRegisterPushDevice.mockReset();
  mockUseUnregisterPushDevice.mockReset();
  mockUseOrganizationSettings.mockReturnValue({
    data: baseSettings,
    isLoading: false,
  });
  mockUseSubscription.mockReturnValue({
    data: baseSubscription,
  });
  mockUseIntegrationStatus.mockReturnValue({
    data: baseIntegrationStatus,
  });
  mockUseUpdateOrganizationSettings.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseCreateCheckoutSession.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ session_id: "cs_1", url: "https://checkout.stripe.com" }),
    isPending: false,
  });
  mockUseCreatePortalSession.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ url: "https://billing.stripe.com/portal" }),
    isPending: false,
  });
  mockUseLinkTelegram.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ link_url: "https://t.me/bot", expires_at: "2026-08-02T17:00:00Z" }),
    isPending: false,
  });
  mockUseUnlinkTelegram.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseRegisterPushDevice.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ id: "pd_1", platform: "ios", created_at: "2026-08-02T16:42:19Z", updated_at: "2026-08-02T16:42:19Z" }),
    isPending: false,
  });
  mockUseUnregisterPushDevice.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
});

describe("SettingsPage", () => {
  it("renders organization settings tab", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByText("Organization Settings")).toBeInTheDocument();
    expect(screen.getByText("USD")).toBeInTheDocument();
    expect(screen.getByText("America/New_York")).toBeInTheDocument();
  });

  it("renders billing tab", () => {
    render(<SettingsPage />);
    const billingTab = screen.getByRole("tab", { name: /billing/i });
    fireEvent.click(billingTab);
    expect(screen.getByText("Billing & Subscription")).toBeInTheDocument();
    expect(screen.getByText("pro_monthly")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("renders integrations tab", () => {
    render(<SettingsPage />);
    const integrationsTab = screen.getByRole("tab", { name: /integrations/i });
    fireEvent.click(integrationsTab);
    expect(screen.getByText("Telegram")).toBeInTheDocument();
    expect(screen.getByText("disconnected")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseOrganizationSettings.mockReturnValue({
      data: null,
      isLoading: true,
    });

    render(<SettingsPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows edit organization settings dialog", () => {
    render(<SettingsPage />);
    const editButton = screen.getByRole("button", {
      name: /edit organization settings/i,
    });
    expect(editButton).toBeInTheDocument();
  });
});
