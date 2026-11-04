import type {
  OpportunityDetail,
  Opportunity,
  PaginatedResponse,
  PaginationMeta,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export interface ListOpportunitiesParams {
  cursor?: string;
  limit?: string;
  sort?: string;
}

export async function listOpportunities(
  params: ListOpportunitiesParams = {}
): Promise<PaginatedResponse<Opportunity>> {
  const searchParams = new URLSearchParams();
  if (params.cursor) searchParams.set("cursor", params.cursor);
  if (params.limit) searchParams.set("limit", params.limit);
  if (params.sort) searchParams.set("sort", params.sort);
  const query = searchParams.toString();
  const path = `/api/v1/opportunities${query ? `?${query}` : ""}`;
  const envelope = await apiClient.getEnvelope<Opportunity[], PaginationMeta>(path, {
    headers: getAuthHeaders(),
  });
  if (envelope.data === null || envelope.meta === null) {
    throw new Error("Invalid opportunities feed response");
  }
  return { data: envelope.data, meta: envelope.meta };
}

export async function getOpportunity(
  opportunityId: string
): Promise<OpportunityDetail> {
  return apiClient.get(`/api/v1/opportunities/${opportunityId}`, {
    headers: getAuthHeaders(),
  }) as Promise<OpportunityDetail>;
}

export async function recordOpportunityFeedback(
  opportunityId: string,
  body: { decision: string; note?: string }
): Promise<{ ok: boolean }> {
  return apiClient.post(`/api/v1/opportunities/${opportunityId}/feedback`, {
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  }) as Promise<{ ok: boolean }>;
}

export async function recordTradeOutcome(
  opportunityId: string,
  body: {
    acquisition_price?: string | null;
    acquisition_currency?: string | null;
    resale_price?: string | null;
    resale_currency?: string | null;
    actual_profit?: string | null;
    days_to_sell?: number | null;
  }
): Promise<{ ok: boolean }> {
  return apiClient.post(`/api/v1/opportunities/${opportunityId}/trade-outcome`, {
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  }) as Promise<{ ok: boolean }>;
}
