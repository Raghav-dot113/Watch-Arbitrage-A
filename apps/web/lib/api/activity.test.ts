import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { listActivity, listTradeOutcomes } from "./activity";
import { apiClient } from "./client";

const mockGetEnvelope = vi.fn();

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(apiClient, "getEnvelope").mockImplementation(mockGetEnvelope);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("activity api layer", () => {
  describe("listActivity", () => {
    it("calls apiClient.getEnvelope with the activity path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "act_1",
            event_type: "feedback",
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
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listActivity();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/activity",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listActivity()).rejects.toThrow(
        "Invalid activity response",
      );
    });
  });

  describe("listTradeOutcomes", () => {
    it("calls apiClient.getEnvelope with the outcomes path and auth headers", async () => {
      const expected = {
        data: [
          {
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
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listTradeOutcomes();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/activity/outcomes",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listTradeOutcomes()).rejects.toThrow(
        "Invalid trade outcomes response",
      );
    });
  });
});
