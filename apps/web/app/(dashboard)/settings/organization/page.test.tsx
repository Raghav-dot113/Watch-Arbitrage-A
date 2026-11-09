import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SettingsPage from "./page";

const mockUseOrganizationSettings = vi.fn();
const mockUseUpdateOrganizationSettings = vi.fn();
const mockUseSubscription = vi.fn();
const mockUseCreatePayPalSubscription = vi.fn();
const mockUseCancelPayPalSubscription = vi.fn();
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
  useCreatePayPalSubscription: () => mockUseCreatePayPalSubscription(),
  useCancelPayPalSubscription: () => mockUseCancelPayPalSubscription(),
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
  window.history.replaceState({}, "", "/settings/organization");
  vi.restoreAllMocks();
  mockUseOrganizationSettings.mockReset();
  mockUseUpdateOrganizationSettings.mockReset();
  mockUseSubscription.mockReset();
  mockUseCreatePayPalSubscription.mockReset();
  mockUseCancelPayPalSubscription.mockReset();
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
  mockUseCreatePayPalSubscription.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      subscription_id: "I_1",
      url: "https://www.sandbox.paypal.com/approve/I_1",
    }),
    isPending: false,
  });
  mockUseCancelPayPalSubscription.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      ...baseSubscription,
      status: "canceled",
    }),
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
    expect(screen.getByText("PayPal subscription")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel subscription/i })).toBeInTheDocument();
  });

  it("opens billing after returning from PayPal checkout", () => {
    window.history.replaceState(
      {},
      "",
      "/settings/organization?checkout=success",
    );

    render(<SettingsPage />);

    expect(screen.getByRole("tab", { name: /billing/i })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(
      screen.getByText(/PayPal returned you to ChronoArb/i),
    ).toBeInTheDocument();
  });

  it("opens a PayPal approval link after creating a subscription", async () => {
    const checkoutMutation = vi.fn().mockResolvedValue({
      subscription_id: "I_1",
      url: "https://www.sandbox.paypal.com/approve/I_1",
    });
    mockUseCreatePayPalSubscription.mockReturnValue({
      mutateAsync: checkoutMutation,
      isPending: false,
    });

    render(<SettingsPage />);
    fireEvent.click(screen.getByRole("tab", { name: /billing/i }));
    fireEvent.change(screen.getByRole("textbox", { name: /plan id/i }), {
      target: { value: "pro_monthly" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue with paypal/i }));

    expect(await screen.findByRole("link", { name: /open paypal/i })).toHaveAttribute(
      "href",
      "https://www.sandbox.paypal.com/approve/I_1",
    );
    expect(checkoutMutation).toHaveBeenCalledWith(
      expect.objectContaining({ plan_id: "pro_monthly", idempotency_key: expect.any(String) }),
    );
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
