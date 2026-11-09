import type {
  OrganizationSettingsPatchRequest,
  OrganizationSettingsResponse,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function getOrganizationSettings(): Promise<OrganizationSettingsResponse> {
  const envelope = await apiClient.getEnvelope<OrganizationSettingsResponse>(
    "/api/v1/settings/organization",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid organization settings response");
  }
  return envelope.data;
}

export async function patchOrganizationSettings(
  body: OrganizationSettingsPatchRequest,
): Promise<OrganizationSettingsResponse> {
  const envelope = await apiClient.getEnvelope<OrganizationSettingsResponse>(
    "/api/v1/settings/organization",
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
  if (envelope.data === null) {
    throw new Error("Invalid organization settings response");
  }
  return envelope.data;
}
