import type {
  AuditEvent,
  DuplicateGroup,
  FeatureFlag,
  FeatureFlagPatchRequest,
  SourceAdmin,
  SourcePatchRequest,
  UnmatchedListing,
  UnmatchedResolveRequest,
} from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function listSources(): Promise<SourceAdmin[]> {
  const envelope = await apiClient.getEnvelope<SourceAdmin[]>(
    "/api/v1/admin/sources",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid sources response");
  }
  return envelope.data;
}

export async function updateSource(
  sourceId: string,
  isEnabled: boolean,
): Promise<SourceAdmin> {
  return apiClient.patch<SourceAdmin>(
    `/api/v1/admin/sources/${sourceId}`,
    {
      headers: getAuthHeaders(),
      body: JSON.stringify({ is_enabled: isEnabled }),
    },
  );
}

export async function listFeatureFlags(): Promise<FeatureFlag[]> {
  const envelope = await apiClient.getEnvelope<FeatureFlag[]>(
    "/api/v1/admin/flags",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid feature flags response");
  }
  return envelope.data;
}

export async function updateFeatureFlag(
  flagId: string,
  body: FeatureFlagPatchRequest,
): Promise<FeatureFlag> {
  return apiClient.patch<FeatureFlag>(
    `/api/v1/admin/flags/${flagId}`,
    {
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    },
  );
}

export async function listAuditEvents(): Promise<AuditEvent[]> {
  const envelope = await apiClient.getEnvelope<AuditEvent[]>(
    "/api/v1/admin/audit",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid audit events response");
  }
  return envelope.data;
}

export async function listUnmatchedListings(): Promise<UnmatchedListing[]> {
  const envelope = await apiClient.getEnvelope<UnmatchedListing[]>(
    "/api/v1/admin/unmatched",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid unmatched listings response");
  }
  return envelope.data;
}

export async function resolveUnmatchedListing(
  listingId: string,
  referenceId: string,
): Promise<UnmatchedListing> {
  const envelope = await apiClient.post<UnmatchedListing>(
    `/api/v1/admin/unmatched/${listingId}/resolve`,
    {
      headers: getAuthHeaders(),
      body: JSON.stringify({ reference_id: referenceId }),
    },
  );
  if (envelope === null) {
    throw new Error("Invalid unmatched listing resolve response");
  }
  return envelope;
}

export async function listDuplicateGroups(): Promise<DuplicateGroup[]> {
  const envelope = await apiClient.getEnvelope<DuplicateGroup[]>(
    "/api/v1/admin/duplicates",
    { headers: getAuthHeaders() },
  );
  if (envelope.data === null) {
    throw new Error("Invalid duplicate groups response");
  }
  return envelope.data;
}
