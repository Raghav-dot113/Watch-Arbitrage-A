import type { ActivityItem, TradeOutcome } from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function listActivity(): Promise<ActivityItem[]> {
  const envelope = await apiClient.getEnvelope<ActivityItem[]>(
    "/api/v1/activity",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid activity response");
  }
  return envelope.data;
}

export async function listTradeOutcomes(): Promise<TradeOutcome[]> {
  const envelope = await apiClient.getEnvelope<TradeOutcome[]>(
    "/api/v1/activity/outcomes",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid trade outcomes response");
  }
  return envelope.data;
}
