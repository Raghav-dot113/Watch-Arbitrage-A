import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  getOrganizationSettings,
  patchOrganizationSettings,
} from "./settings";
import {
  getSubscription,
  createCheckoutSession,
  createPortalSession,
} from "./billing";
import {
  getIntegrationStatus,
  linkTelegram,
  unlinkTelegram,
  registerPushDevice,
  unregisterPushDevice,
} from "./integrations";
import { apiClient } from "./client";

const mockGetEnvelope = vi.fn();
const mockDelete = vi.fn();

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(apiClient, "getEnvelope").mockImplementation(mockGetEnvelope);
  vi.spyOn(apiClient, "delete").mockImplementation(mockDelete);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("settings api layer", () => {
  describe("getOrganizationSettings", () => {
    it("calls apiClient.getEnvelope with org settings path and auth headers", async () => {
      const expected = {
        data: {
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
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await getOrganizationSettings();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/settings/organization",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("patchOrganizationSettings", () => {
    it("calls apiClient.getEnvelope with PATCH path and auth headers", async () => {
      const expected = {
        data: {
          currency: "EUR",
          timezone: "Europe/Berlin",
          default_fees: {
            buyer_fee: null,
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
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await patchOrganizationSettings({
        currency: "EUR",
        timezone: "Europe/Berlin",
      });

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/settings/organization",
        {
          headers: {},
          body: JSON.stringify({
            currency: "EUR",
            timezone: "Europe/Berlin",
          }),
        },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("getSubscription", () => {
    it("calls apiClient.getEnvelope with billing subscription path", async () => {
      const expected = {
        data: {
          id: "sub_1",
          status: "active",
          plan_id: "pro_monthly",
          current_period_start: "2026-08-01T00:00:00Z",
          current_period_end: "2026-09-01T00:00:00Z",
          trial_end: null,
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await getSubscription();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/billing/subscription",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("createCheckoutSession", () => {
    it("calls apiClient.getEnvelope with checkout path", async () => {
      const expected = {
        data: { session_id: "cs_1", url: "https://checkout.stripe.com/session" },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await createCheckoutSession({ plan_id: "pro_monthly" });

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/billing/checkout",
        {
          headers: {},
          body: JSON.stringify({ plan_id: "pro_monthly" }),
        },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("createPortalSession", () => {
    it("calls apiClient.getEnvelope with portal path", async () => {
      const expected = {
        data: { url: "https://billing.stripe.com/portal" },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await createPortalSession();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/billing/portal",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("getIntegrationStatus", () => {
    it("calls apiClient.getEnvelope with integrations path", async () => {
      const expected = {
        data: {
          telegram_status: "disconnected",
          telegram_link_expires_at: null,
          push_devices: [],
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await getIntegrationStatus();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/settings/integrations",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("linkTelegram", () => {
    it("calls apiClient.getEnvelope with telegram link path", async () => {
      const expected = {
        data: {
          link_url: "https://t.me/chronoarb_bot?start=abc123",
          expires_at: "2026-08-02T17:00:00Z",
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await linkTelegram();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/settings/integrations/telegram",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("unlinkTelegram", () => {
    it("calls apiClient.delete with telegram unlink path", async () => {
      mockDelete.mockResolvedValue(undefined);

      await unlinkTelegram();

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/settings/integrations/telegram",
        { headers: {} },
      );
    });
  });

  describe("registerPushDevice", () => {
    it("calls apiClient.getEnvelope with push device path", async () => {
      const expected = {
        data: {
          id: "pd_1",
          platform: "ios",
          created_at: "2026-08-02T16:42:19Z",
          updated_at: "2026-08-02T16:42:19Z",
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await registerPushDevice({
        platform: "ios",
        device_token: "token_123",
      });

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/settings/integrations/push",
        {
          headers: {},
          body: JSON.stringify({ platform: "ios", device_token: "token_123" }),
        },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("unregisterPushDevice", () => {
    it("calls apiClient.delete with push device path", async () => {
      mockDelete.mockResolvedValue(undefined);

      await unregisterPushDevice("pd_1");

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/settings/integrations/push/pd_1",
        { headers: {} },
      );
    });
  });
});
