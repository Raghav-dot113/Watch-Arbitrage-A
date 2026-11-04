import type { Membership, OrganizationCreateRequest } from "./types";
import { apiClient, getAuthHeaders } from "./client";

export async function getMe(): Promise<{
  user: Membership & { email: string; display_name: string | null; id: string; created_at: string; updated_at: string | null };
  memberships: Membership[];
  organizations: { id: string; name: string; slug: string; created_at: string; updated_at: string | null }[];
}> {
  return apiClient.get("/api/v1/identity/me", {
    headers: getAuthHeaders(),
  }) as Promise<{
    user: Membership & { email: string; display_name: string | null; id: string; created_at: string; updated_at: string | null };
    memberships: Membership[];
    organizations: { id: string; name: string; slug: string; created_at: string; updated_at: string | null }[];
  }>;
}

export async function createOrganization(
  body: OrganizationCreateRequest,
): Promise<{ id: string; name: string; slug: string; created_at: string; updated_at: string | null }> {
  return apiClient.post("/api/v1/identity/organizations", {
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  }) as Promise<{
    id: string;
    name: string;
    slug: string;
    created_at: string;
    updated_at: string | null;
  }>;
}

export async function listOrganizations(): Promise<
  { data: Membership[]; meta: unknown } | null
> {
  return apiClient.get("/api/v1/identity/organizations", {
    headers: getAuthHeaders(),
  }) as Promise<{
    data: Membership[];
    meta: unknown;
  } | null>;
}
