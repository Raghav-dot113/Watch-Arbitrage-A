import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  listOpportunities,
  getOpportunity,
  recordOpportunityFeedback,
  getMe,
  createOrganization,
  getHealth,
  getAuthHeaders,
} from "./index";
import { apiClient } from "./client";

const mockGet = vi.fn();
const mockGetEnvelope = vi.fn();
const mockPost = vi.fn();

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(apiClient, "get").mockImplementation(mockGet);
  vi.spyOn(apiClient, "getEnvelope").mockImplementation(mockGetEnvelope);
  vi.spyOn(apiClient, "post").mockImplementation(mockPost);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api layer", () => {
  describe("listOpportunities", () => {
    it("calls apiClient.get with the opportunities path and auth headers", async () => {
      const expected = { data: [], meta: { trace_id: "t1", next_cursor: null, has_more: false } };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listOpportunities({ limit: "20", sort: "score_desc" });

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/opportunities?limit=20&sort=score_desc",
        { headers: {} }
      );
      expect(result).toEqual(expected);
    });

    it("omits empty query params", async () => {
      mockGetEnvelope.mockResolvedValue({ data: [], meta: { trace_id: "t1", next_cursor: null, has_more: false } });

      await listOpportunities();

      expect(mockGetEnvelope).toHaveBeenCalledWith("/api/v1/opportunities", { headers: {} });
    });
  });

  describe("getOpportunity", () => {
    it("calls apiClient.get with the opportunity path", async () => {
      const expected = {
        id: "opp_1",
        organization_id: "org_1",
        listing_id: "listing_1",
        valuation_id: "val_1",
        material_version: 1,
        score: null,
        state: "published",
        positive_factors: null,
        negative_factors: null,
        published_at: null,
        state_changed_at: null,
        created_at: "2026-08-02T16:42:19Z",
        valuation: null,
      };
      mockGet.mockResolvedValue(expected);

      const result = await getOpportunity("opp_1");

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/opportunities/opp_1",
        { headers: {} }
      );
      expect(result).toEqual(expected);
    });
  });

  describe("getMe", () => {
    it("calls apiClient.get with the identity me path", async () => {
      const expected = {
        user: { id: "u1", email: "a@b.com", display_name: "A", created_at: "2026-08-02T16:42:19Z", updated_at: null },
        memberships: [],
        organizations: [],
      };
      mockGet.mockResolvedValue(expected);

      const result = await getMe();

      expect(mockGet).toHaveBeenCalledWith("/api/v1/identity/me", { headers: {} });
      expect(result).toEqual(expected);
    });
  });

  describe("getHealth", () => {
    it("calls apiClient.get with /health", async () => {
      const expected = { status: "ok", trace_id: "t1" };
      mockGet.mockResolvedValue(expected);

      const result = await getHealth();

      expect(mockGet).toHaveBeenCalledWith("/health");
      expect(result).toEqual(expected);
    });
  });

  describe("getAuthHeaders", () => {
    it("returns no authentication headers in demo mode", () => {
      expect(getAuthHeaders()).toEqual({});
    });
  });

  describe("createOrganization", () => {
    it("calls apiClient.post with the organizations path and auth headers", async () => {
      const expected = {
        id: "org_1",
        name: "Test Org",
        slug: "test-org",
        created_at: "2026-08-02T16:42:19Z",
        updated_at: null,
      };
      mockPost.mockResolvedValue(expected);

      const result = await createOrganization({
        name: "Test Org",
        slug: "test-org",
      });

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/identity/organizations",
        {
          headers: {},
          body: JSON.stringify({ name: "Test Org", slug: "test-org" }),
        },
      );
      expect(result).toEqual(expected);
    });
  });
});
