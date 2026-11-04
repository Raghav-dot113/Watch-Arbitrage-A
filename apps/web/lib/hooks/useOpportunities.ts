import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listOpportunities,
  getOpportunity,
  recordOpportunityFeedback,
  recordTradeOutcome,
  type ListOpportunitiesParams,
  type Opportunity,
  type PaginatedResponse,
} from "../api";

export function useOpportunities(params: ListOpportunitiesParams = {}) {
  return useQuery({
    queryKey: ["opportunities", params],
    queryFn: async () => {
      return listOpportunities(params);
    },
    placeholderData: (previousData) => previousData,
  });
}

export function useOpportunity(opportunityId: string | null) {
  return useQuery({
    queryKey: ["opportunity", opportunityId],
    queryFn: async () => {
      if (!opportunityId) throw new Error("opportunityId required");
      return getOpportunity(opportunityId);
    },
    enabled: !!opportunityId,
  });
}

export function useRecordFeedback(opportunityId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { decision: string; note?: string }) =>
      recordOpportunityFeedback(opportunityId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity", opportunityId] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });
}

export function useRecordTradeOutcome(opportunityId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      acquisition_price?: string | null;
      acquisition_currency?: string | null;
      resale_price?: string | null;
      resale_currency?: string | null;
      actual_profit?: string | null;
      days_to_sell?: number | null;
    }) => recordTradeOutcome(opportunityId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity", opportunityId] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });
}

export type { Opportunity, PaginatedResponse, ListOpportunitiesParams };
