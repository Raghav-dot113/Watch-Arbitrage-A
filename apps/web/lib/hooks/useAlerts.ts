import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createAlertRule,
  deleteAlertRule,
  listAlertDeliveries,
  listAlertRules,
  requestAlertTest,
  updateAlertRule,
  type AlertChannel,
  type AlertDeliveryResponse,
  type AlertRuleResponse,
} from "../api";

export function useAlertRules() {
  return useQuery({
    queryKey: ["alertRules"],
    queryFn: async () => {
      return listAlertRules();
    },
  });
}

export function useCreateAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof createAlertRule>[0]) =>
      createAlertRule(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] });
    },
  });
}

export function useUpdateAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      ruleId,
      body,
    }: {
      ruleId: string;
      body: Parameters<typeof updateAlertRule>[1];
    }) => updateAlertRule(ruleId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] });
    },
  });
}

export function useDeleteAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: string) => deleteAlertRule(ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] });
    },
  });
}

export function useRequestAlertTest() {
  return useMutation({
    mutationFn: (ruleId: string) => requestAlertTest(ruleId),
  });
}

export function useAlertDeliveries() {
  return useQuery({
    queryKey: ["alertDeliveries"],
    queryFn: async () => {
      return listAlertDeliveries();
    },
  });
}

export type { AlertRuleResponse, AlertDeliveryResponse, AlertChannel };
