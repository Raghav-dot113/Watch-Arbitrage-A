import type {
  StripeCheckoutRequest,
  StripePortalResponse,
  StripeSessionResponse,
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

export async function createCheckoutSession(
  body: StripeCheckoutRequest,
): Promise<StripeSessionResponse> {
  const envelope = await apiClient.getEnvelope<StripeSessionResponse>(
    "/api/v1/billing/checkout",
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (envelope.data === null) {
    throw new Error("Invalid checkout session response");
  }
  return envelope.data;
}

export async function createPortalSession(): Promise<StripePortalResponse> {
  const envelope = await apiClient.getEnvelope<StripePortalResponse>(
    "/api/v1/billing/portal",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid portal session response");
  }
  return envelope.data;
}
