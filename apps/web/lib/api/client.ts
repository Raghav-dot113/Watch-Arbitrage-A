import { ApiClient } from "@chronoarb/api-client";

const baseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export const apiClient = new ApiClient({
  baseUrl,
  fetch: fetchWithSessionRecovery,
});

let authToken: string | null = null;
let organizationId: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function setAuthOrganizationId(id: string | null) {
  organizationId = id;
}

async function fetchWithSessionRecovery(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (organizationId && !headers.has("X-Organization-ID")) {
    headers.set("X-Organization-ID", organizationId);
  }
  if (authToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const requestInit = { ...init, headers };
  const response = await globalThis.fetch(input, requestInit);
  if (response.status !== 401 || typeof window === "undefined") {
    return response;
  }

  let refreshResponse: Response;
  try {
    refreshResponse = await globalThis.fetch("/api/auth/session?refresh=1", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    if (error instanceof Error) {
      return response;
    }
    throw error;
  }
  if (!refreshResponse.ok) {
    return response;
  }

  let refreshed: { user?: { apiToken?: unknown; orgId?: unknown } };
  try {
    refreshed = (await refreshResponse.json()) as typeof refreshed;
  } catch {
    return response;
  }
  if (typeof refreshed.user?.apiToken !== "string") {
    return response;
  }

  authToken = refreshed.user.apiToken;
  organizationId =
    typeof refreshed.user.orgId === "string" ? refreshed.user.orgId : null;
  headers.set("Authorization", `Bearer ${authToken}`);
  if (organizationId) {
    headers.set("X-Organization-ID", organizationId);
  } else {
    headers.delete("X-Organization-ID");
  }
  return globalThis.fetch(input, { ...requestInit, headers });
}

export function getAuthHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

export { baseUrl };
