import type {
  WatchList,
  WatchListCreateRequest,
  WatchListUpdateRequest,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function listWatchLists(): Promise<WatchList[]> {
  const envelope = await apiClient.getEnvelope<WatchList[]>(
    "/api/v1/catalog/watch-lists",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid watch lists response");
  }
  return envelope.data;
}

export async function createWatchList(
  body: WatchListCreateRequest,
): Promise<WatchList> {
  const result = await apiClient.post<WatchList>(
    "/api/v1/catalog/watch-lists",
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (!result) {
    throw new Error("Invalid watch list create response");
  }
  return result;
}

export async function updateWatchList(
  watchListId: string,
  body: WatchListUpdateRequest,
): Promise<WatchList> {
  const result = await apiClient.put<WatchList>(
    `/api/v1/catalog/watch-lists/${watchListId}`,
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (!result) {
    throw new Error("Invalid watch list update response");
  }
  return result;
}

export async function deleteWatchList(watchListId: string): Promise<void> {
  await apiClient.delete(`/api/v1/catalog/watch-lists/${watchListId}`, {
    headers: getAuthHeaders(),
  });
}
