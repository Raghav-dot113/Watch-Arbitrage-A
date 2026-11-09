import type {
  PayPalCheckoutRequest,
  PayPalSubscriptionApprovalResponse,
  SubscriptionResponse,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function getSubscription(): Promise<SubscriptionResponse> {
  const envelope = await apiClient.getEnvelope<SubscriptionResponse>(
    "/api/v1/billing/subscription",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid subscription response");
  }
  return envelope.data;
}

export async function createPayPalSubscription(
  body: PayPalCheckoutRequest,
  idempotencyKey: string,
): Promise<PayPalSubscriptionApprovalResponse> {
  const result = await apiClient.post<PayPalSubscriptionApprovalResponse>(
    "/api/v1/billing/checkout",
    {
      headers: { ...getAuthHeaders(), "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(body),
    },
  );
  if (result === null) {
    throw new Error("Invalid PayPal subscription response");
  }
  return result;
}

export async function cancelPayPalSubscription(
  idempotencyKey: string,
): Promise<SubscriptionResponse> {
  const result = await apiClient.post<SubscriptionResponse>(
    "/api/v1/billing/cancel",
    {
      headers: { ...getAuthHeaders(), "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({}),
    },
  );
  if (result === null) {
    throw new Error("Invalid PayPal cancellation response");
  }
  return result;
}
