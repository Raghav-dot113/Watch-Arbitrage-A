import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  listSources,
  updateSource,
  listFeatureFlags,
  updateFeatureFlag,
  listAuditEvents,
  listUnmatchedListings,
  resolveUnmatchedListing,
  listDuplicateGroups,
} from "./admin";
import { apiClient } from "./client";

const mockGetEnvelope = vi.fn();
const mockPatch = vi.fn();
const mockPost = vi.fn();

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(apiClient, "getEnvelope").mockImplementation(mockGetEnvelope);
  vi.spyOn(apiClient, "patch").mockImplementation(mockPatch);
  vi.spyOn(apiClient, "post").mockImplementation(mockPost);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("admin api layer", () => {
  describe("listSources", () => {
    it("calls apiClient.getEnvelope with the admin sources path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "src_1",
            source_key: "ebay",
            display_name: "eBay",
            adapter_version: "1.0.0",
            access_mode: "public",
            is_enabled: true,
            health_status: "unknown",
            last_fetched_at: null,
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listSources();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/admin/sources",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listSources()).rejects.toThrow("Invalid sources response");
    });
  });

  describe("updateSource", () => {
    it("calls apiClient.patch with the source path and auth headers", async () => {
      const expected = {
        id: "src_1",
        source_key: "ebay",
        display_name: "eBay",
        adapter_version: "1.0.0",
        access_mode: "public",
        is_enabled: false,
        health_status: "unknown",
        last_fetched_at: null,
      };
      mockPatch.mockResolvedValue(expected);

      const result = await updateSource("src_1", false);

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/admin/sources/src_1",
        {
          headers: {},
          body: JSON.stringify({ is_enabled: false }),
        },
      );
      expect(result).toEqual(expected);
    });
  });

  describe("listFeatureFlags", () => {
    it("calls apiClient.getEnvelope with the admin flags path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "flag_1",
            key: "new_ui",
            description: "New UI flag",
            enabled: true,
            organization_ids: null,
            rollout_pct: 100,
            expires_at: null,
            created_at: "2026-08-02T16:42:19Z",
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listFeatureFlags();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/admin/flags",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listFeatureFlags()).rejects.toThrow(
        "Invalid feature flags response",
      );
    });
  });

  describe("updateFeatureFlag", () => {
    it("calls apiClient.patch with the flag path and auth headers", async () => {
      const expected = {
        id: "flag_1",
        key: "new_ui",
        description: "New UI flag",
        enabled: false,
        organization_ids: ["org_1"],
        rollout_pct: 50,
        expires_at: null,
        created_at: "2026-08-02T16:42:19Z",
      };
      mockPatch.mockResolvedValue(expected);

      const result = await updateFeatureFlag("flag_1", {
        enabled: false,
        organization_ids: ["org_1"],
        rollout_pct: 50,
        expires_at: null,
      });

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/admin/flags/flag_1",
        {
          headers: {},
          body: JSON.stringify({
            enabled: false,
            organization_ids: ["org_1"],
            rollout_pct: 50,
            expires_at: null,
          }),
        },
      );
      expect(result).toEqual(expected);
    });
  });

  describe("listAuditEvents", () => {
    it("calls apiClient.getEnvelope with the admin audit path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "audit_1",
            organization_id: "org_1",
            user_id: "user_1",
            action: "admin.source_enabled",
            resource_type: "source",
            resource_id: "src_1",
            details: { is_enabled: true },
            trace_id: "trace_1",
            created_at: "2026-08-02T16:42:19Z",
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listAuditEvents();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/admin/audit",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listAuditEvents()).rejects.toThrow(
        "Invalid audit events response",
      );
    });
  });

  describe("listUnmatchedListings", () => {
    it("calls apiClient.getEnvelope with the admin unmatched path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "unmatched_1",
            reference_id: "ref_1",
            source_key: "ebay",
            title: "Vintage Watch",
            external_url: "https://ebay.com/item/1",
            match_method: null,
            observation_at: "2026-08-02T16:42:19Z",
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listUnmatchedListings();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/admin/unmatched",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listUnmatchedListings()).rejects.toThrow(
        "Invalid unmatched listings response",
      );
    });
  });

  describe("resolveUnmatchedListing", () => {
    it("calls apiClient.post with the resolve path and auth headers", async () => {
      const expected = {
        id: "unmatched_1",
        reference_id: "ref_2",
        source_key: "ebay",
        title: "Vintage Watch",
        external_url: "https://ebay.com/item/1",
        match_method: "manual_review",
        observation_at: "2026-08-02T16:42:19Z",
      };
      mockPost.mockResolvedValue(expected);

      const result = await resolveUnmatchedListing("unmatched_1", "ref_2");

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/admin/unmatched/unmatched_1/resolve",
        {
          headers: {},
          body: JSON.stringify({ reference_id: "ref_2" }),
        },
      );
      expect(result).toEqual(expected);
    });
  });

  describe("listDuplicateGroups", () => {
    it("calls apiClient.getEnvelope with the admin duplicates path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "dup_1",
            representative_id: "listing_1",
            method: "fuzzy_match",
            confidence: "0.95",
            listing_ids: ["listing_1", "listing_2"],
            created_at: "2026-08-02T16:42:19Z",
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listDuplicateGroups();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/admin/duplicates",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listDuplicateGroups()).rejects.toThrow(
        "Invalid duplicate groups response",
      );
    });
  });
});
