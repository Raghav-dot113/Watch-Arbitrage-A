import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  listAlertRules,
  createAlertRule,
  getAlertRule,
  updateAlertRule,
  deleteAlertRule,
  requestAlertTest,
  listAlertDeliveries,
} from "./alerts";
import { apiClient } from "./client";

const mockGetEnvelope = vi.fn();
const mockDelete = vi.fn();
const mockPost = vi.fn();
const mockPut = vi.fn();

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(apiClient, "getEnvelope").mockImplementation(mockGetEnvelope);
  vi.spyOn(apiClient, "delete").mockImplementation(mockDelete);
  vi.spyOn(apiClient, "post").mockImplementation(mockPost);
  vi.spyOn(apiClient, "put").mockImplementation(mockPut);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("alerts api layer", () => {
  describe("listAlertRules", () => {
    it("calls apiClient.getEnvelope with the alert rules path and auth headers", async () => {
      const expected = {
        data: [
          {
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
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listAlertRules();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/alerts/rules",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listAlertRules()).rejects.toThrow(
        "Invalid alert rules response",
      );
    });
  });

  describe("createAlertRule", () => {
    it("calls apiClient.post with the alert rules path and auth headers", async () => {
      const expected = {
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
      mockPost.mockResolvedValue(expected);

      const result = await createAlertRule({
        name: "High profit watches",
        filters: { reference_ids: ["ref_1"], min_profit: "100.00", max_acquisition: null, conditions: null },
        channels: ["in_app"],
        cooldown_minutes: 60,
        is_enabled: true,
      });

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/alerts/rules",
        {
          headers: {},
          body: JSON.stringify({
            name: "High profit watches",
            filters: { reference_ids: ["ref_1"], min_profit: "100.00", max_acquisition: null, conditions: null },
            channels: ["in_app"],
            cooldown_minutes: 60,
            is_enabled: true,
          }),
        },
      );
      expect(result).toEqual(expected);
    });
  });

  describe("getAlertRule", () => {
    it("calls apiClient.getEnvelope with the rule path and auth headers", async () => {
      const expected = {
        data: {
          id: "ar_1",
          organization_id: "org_1",
          created_by: "u1",
          name: "High profit watches",
          filters: { reference_ids: null, min_profit: null, max_acquisition: null, conditions: null },
          channels: ["in_app"],
          cooldown_minutes: 60,
          is_enabled: true,
          created_at: "2026-08-02T16:42:19Z",
          updated_at: "2026-08-02T16:42:19Z",
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await getAlertRule("ar_1");

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/alerts/rules/ar_1",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("updateAlertRule", () => {
    it("calls apiClient.put with the rule path and auth headers", async () => {
      const expected = {
        id: "ar_1",
        organization_id: "org_1",
        created_by: "u1",
        name: "Updated rule",
        filters: { reference_ids: null, min_profit: null, max_acquisition: null, conditions: null },
        channels: ["in_app"],
        cooldown_minutes: 30,
        is_enabled: true,
        created_at: "2026-08-02T16:42:19Z",
        updated_at: "2026-08-02T17:00:00Z",
      };
      mockPut.mockResolvedValue(expected);

      const result = await updateAlertRule("ar_1", {
        name: "Updated rule",
        filters: { reference_ids: null, min_profit: null, max_acquisition: null, conditions: null },
        channels: ["in_app"],
        cooldown_minutes: 30,
        is_enabled: true,
      });

      expect(mockPut).toHaveBeenCalledWith(
        "/api/v1/alerts/rules/ar_1",
        {
          headers: {},
          body: JSON.stringify({
            name: "Updated rule",
            filters: { reference_ids: null, min_profit: null, max_acquisition: null, conditions: null },
            channels: ["in_app"],
            cooldown_minutes: 30,
            is_enabled: true,
          }),
        },
      );
      expect(result).toEqual(expected);
    });
  });

  describe("deleteAlertRule", () => {
    it("calls apiClient.delete with the rule path and auth headers", async () => {
      mockDelete.mockResolvedValue(undefined);

      await deleteAlertRule("ar_1");

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/alerts/rules/ar_1",
        { headers: {} },
      );
    });
  });

  describe("requestAlertTest", () => {
    it("calls apiClient.post with test path and auth headers", async () => {
      const expected = { event_id: "evt_1", status: "pending" };
      mockPost.mockResolvedValue(expected);

      const result = await requestAlertTest("ar_1");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/alerts/rules/ar_1/test",
        {
          headers: {
            "Idempotency-Key": expect.any(String),
          },
        },
      );
      expect(result).toEqual({ event_id: "evt_1", status: "pending" });
    });
  });

  describe("listAlertDeliveries", () => {
    it("calls apiClient.getEnvelope with deliveries path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "ad_1",
            rule_id: "ar_1",
            opportunity_id: "opp_1",
            material_version: 1,
            channel: "in_app",
            delivery_status: "sent",
            created_at: "2026-08-02T16:42:19Z",
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listAlertDeliveries();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/alerts/deliveries",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });
  });
});
