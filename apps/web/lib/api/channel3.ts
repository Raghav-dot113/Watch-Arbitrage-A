import type {
  Channel3SearchRequest,
  Channel3SearchResponse,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function searchChannel3(
  payload: Channel3SearchRequest
): Promise<Channel3SearchResponse> {
  return apiClient.post("/api/v1/catalog/channel3/search", {
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  }) as Promise<Channel3SearchResponse>;
}