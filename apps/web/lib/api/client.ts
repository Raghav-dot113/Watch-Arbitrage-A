import { ApiClient } from "@chronoarb/api-client";

const baseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export const apiClient = new ApiClient({
  baseUrl,
  fetch: (input, init) => globalThis.fetch(input, init),
});

/**
 * Authentication is intentionally disabled for the hackathon demo. Keeping this
 * helper means transport modules do not need to branch on deployment mode.
 */
export function getAuthHeaders(): Record<string, string> {
  return {};
}

export { baseUrl };
