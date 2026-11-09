import type {
  IntegrationStatusResponse,
  PushDeviceResponse,
  TelegramLinkResponse,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function getIntegrationStatus(): Promise<IntegrationStatusResponse> {
  const envelope = await apiClient.getEnvelope<IntegrationStatusResponse>(
    "/api/v1/settings/integrations",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid integration status response");
  }
  return envelope.data;
}

export async function linkTelegram(): Promise<TelegramLinkResponse> {
  const envelope = await apiClient.getEnvelope<TelegramLinkResponse>(
    "/api/v1/settings/integrations/telegram",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid telegram link response");
  }
  return envelope.data;
}

export async function unlinkTelegram(): Promise<void> {
  await apiClient.delete("/api/v1/settings/integrations/telegram", {
    headers: getAuthHeaders(),
  });
}

export async function registerPushDevice(
  body: { platform: "ios" | "android"; device_token: string },
): Promise<PushDeviceResponse> {
  const envelope = await apiClient.getEnvelope<PushDeviceResponse>(
    "/api/v1/settings/integrations/push",
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (envelope.data === null) {
    throw new Error("Invalid push device response");
  }
  return envelope.data;
}

export async function unregisterPushDevice(deviceId: string): Promise<void> {
  await apiClient.delete(`/api/v1/settings/integrations/push/${deviceId}`, {
    headers: getAuthHeaders(),
  });
}
