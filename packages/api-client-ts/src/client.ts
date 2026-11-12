import { HttpError } from "./types";
import type {
  ApiClientOptions,
  ApiError,
  ApiSuccessEnvelope,
  HealthResponse,
  ReadyResponse,
} from "./types";

export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetchFn: typeof fetch;
  private readonly defaultHeaders: Record<string, string>;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.fetchFn = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.defaultHeaders = {
      "Content-Type": "application/json",
      ...options.headers,
    } as Record<string, string>;
  }

  private async requestEnvelope<T>(
    path: string,
    init?: RequestInit
  ): Promise<ApiSuccessEnvelope<T> | null> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      ...this.defaultHeaders,
      ...(init?.headers as Record<string, string> | undefined),
    };
    const body = init?.body !== undefined ? init.body : undefined;

    const response = await this.fetchFn(url, {
      ...init,
      headers,
      ...(body !== undefined && {
        body: typeof body === "string" ? body : JSON.stringify(body),
      }),
    });

    const contentType = response.headers.get("content-type") ?? "";
    let payload: unknown = null;
    if (contentType.includes("application/json")) {
      payload = await response.json().catch(() => null);
    }

    if (!response.ok) {
      const body = isRecord(payload) ? payload : null;
      const apiError = body && isRecord(body.error) ? body.error : body;
      const error = isApiError(apiError) ? apiError : {
        code: "http_error",
        message:
          (body && typeof body.detail === "string" && body.detail) ||
          response.statusText ||
          "The request failed.",
        field_errors: null,
        trace_id: "",
        retryable: response.status >= 500,
      };
      throw new HttpError(response.status, error);
    }

    return payload as ApiSuccessEnvelope<T> | null;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const envelope = await this.requestEnvelope<T>(path, init);
    return (envelope?.data ?? null) as T;
  }

  async get(path: string, init?: RequestInit): Promise<unknown> {
    return this.request<unknown>(path, { ...init, method: "GET" });
  }

  async post<T = unknown>(
    path: string,
    init?: RequestInit
  ): Promise<T> {
    const body = init?.body !== undefined ? init.body : undefined;
    return this.request<T>(path, {
      ...init,
      method: "POST",
      ...(body !== undefined && {
        body: typeof body === "string" ? body : JSON.stringify(body),
      }),
    });
  }

  async delete(path: string, init?: RequestInit): Promise<void> {
    return this.request<void>(path, { ...init, method: "DELETE" });
  }

  async patch<T = unknown>(
    path: string,
    init?: RequestInit
  ): Promise<T> {
    const body = init?.body !== undefined ? init.body : undefined;
    return this.request<T>(path, {
      ...init,
      method: "PATCH",
      ...(body !== undefined && {
        body: typeof body === "string" ? body : JSON.stringify(body),
      }),
    });
  }

  async put<T = unknown>(
    path: string,
    init?: RequestInit
  ): Promise<T> {
    const body = init?.body !== undefined ? init.body : undefined;
    return this.request<T>(path, {
      ...init,
      method: "PUT",
      ...(body !== undefined && {
        body: typeof body === "string" ? body : JSON.stringify(body),
      }),
    });
  }

  async getEnvelope<T, Meta = Record<string, unknown>>(
    path: string,
    init?: RequestInit
  ): Promise<ApiSuccessEnvelope<T, Meta>> {
    const envelope = await this.requestEnvelope<T>(path, {
      ...init,
      method: "GET",
    });
    if (envelope === null) {
      throw new Error("Expected an API success envelope");
    }
    return envelope as ApiSuccessEnvelope<T, Meta>;
  }

  async getHealth(): Promise<HealthResponse> {
    return (await this.request<HealthResponse>("/health")) as HealthResponse;
  }

  async getReady(): Promise<ReadyResponse> {
    return (await this.request<ReadyResponse>("/ready")) as ReadyResponse;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isApiError(value: unknown): value is ApiError {
  return (
    isRecord(value) &&
    typeof value.code === "string" &&
    typeof value.message === "string" &&
    typeof value.trace_id === "string" &&
    typeof value.retryable === "boolean"
  );
}
