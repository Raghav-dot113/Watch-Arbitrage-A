import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  listWatchLists,
  createWatchList,
  updateWatchList,
  deleteWatchList,
} from "./watchlists";
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

describe("watchlists api layer", () => {
  describe("listWatchLists", () => {
    it("calls apiClient.getEnvelope with the watch-lists path and auth headers", async () => {
      const expected = {
        data: [
          {
            id: "wl_1",
            organization_id: "org_1",
            name: "My Watch List",
            created_at: "2026-08-02T16:42:19Z",
            entries: [],
          },
        ],
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await listWatchLists();

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/catalog/watch-lists",
        { headers: {} },
      );
      expect(result).toEqual(expected.data);
    });

    it("throws when data is null", async () => {
      mockGetEnvelope.mockResolvedValue({ data: null, meta: null });

      await expect(listWatchLists()).rejects.toThrow(
        "Invalid watch lists response",
      );
    });
  });

  describe("createWatchList", () => {
    it("calls apiClient.getEnvelope with POST and auth headers", async () => {
      const expected = {
        data: {
          id: "wl_1",
          organization_id: "org_1",
          name: "New List",
          created_at: "2026-08-02T16:42:19Z",
          entries: [],
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await createWatchList({
        name: "New List",
        reference_ids: ["ref_1", "ref_2"],
      });

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/catalog/watch-lists",
        {
          headers: {},
          body: JSON.stringify({
            name: "New List",
            reference_ids: ["ref_1", "ref_2"],
          }),
        },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("updateWatchList", () => {
    it("calls apiClient.getEnvelope with PUT path and auth headers", async () => {
      const expected = {
        data: {
          id: "wl_1",
          organization_id: "org_1",
          name: "Updated List",
          created_at: "2026-08-02T16:42:19Z",
          entries: [],
        },
        meta: null,
      };
      mockGetEnvelope.mockResolvedValue(expected);

      const result = await updateWatchList("wl_1", {
        name: "Updated List",
        reference_ids: ["ref_1"],
      });

      expect(mockGetEnvelope).toHaveBeenCalledWith(
        "/api/v1/catalog/watch-lists/wl_1",
        {
          headers: {},
          body: JSON.stringify({
            name: "Updated List",
            reference_ids: ["ref_1"],
          }),
        },
      );
      expect(result).toEqual(expected.data);
    });
  });

  describe("deleteWatchList", () => {
    it("calls apiClient.delete with the watch-list path and auth headers", async () => {
      mockDelete.mockResolvedValue(undefined);

      await deleteWatchList("wl_1");

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/catalog/watch-lists/wl_1",
        { headers: {} },
      );
    });
  });
});
