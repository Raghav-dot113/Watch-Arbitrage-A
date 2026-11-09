import type {
  AlertDeliveryResponse,
  AlertRuleCreateRequest,
  AlertRuleResponse,
  AlertTestAcceptedResponse,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function listAlertRules(): Promise<AlertRuleResponse[]> {
  const envelope = await apiClient.getEnvelope<AlertRuleResponse[]>(
    "/api/v1/alerts/rules",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid alert rules response");
  }
  return envelope.data;
}

export async function createAlertRule(
  body: AlertRuleCreateRequest,
): Promise<AlertRuleResponse> {
  const envelope = await apiClient.getEnvelope<AlertRuleResponse>(
    "/api/v1/alerts/rules",
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (envelope.data === null) {
    throw new Error("Invalid alert rule create response");
  }
  return envelope.data;
}

export async function getAlertRule(ruleId: string): Promise<AlertRuleResponse> {
  const envelope = await apiClient.getEnvelope<AlertRuleResponse>(
    `/api/v1/alerts/rules/${ruleId}`,
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid alert rule response");
  }
  return envelope.data;
}

export async function updateAlertRule(
  ruleId: string,
  body: AlertRuleCreateRequest,
): Promise<AlertRuleResponse> {
  const envelope = await apiClient.getEnvelope<AlertRuleResponse>(
    `/api/v1/alerts/rules/${ruleId}`,
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (envelope.data === null) {
    throw new Error("Invalid alert rule update response");
  }
  return envelope.data;
}

export async function deleteAlertRule(ruleId: string): Promise<void> {
  await apiClient.delete(`/api/v1/alerts/rules/${ruleId}`, {
    headers: getAuthHeaders(),
  });
}

export async function requestAlertTest(ruleId: string): Promise<AlertTestAcceptedResponse> {
  const envelope = await apiClient.getEnvelope<AlertTestAcceptedResponse>(
    `/api/v1/alerts/rules/${ruleId}/test`,
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid alert test response");
  }
  return envelope.data;
}

export async function listAlertDeliveries(): Promise<AlertDeliveryResponse[]> {
  const envelope = await apiClient.getEnvelope<AlertDeliveryResponse[]>(
    "/api/v1/alerts/deliveries",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid alert deliveries response");
  }
  return envelope.data;
}
