export interface ApiSuccessEnvelope<
  T = unknown,
  Meta = Record<string, unknown>,
> {
  data: T | null;
  meta: Meta | null;
}

export interface ApiError {
  code: string;
  message: string;
  field_errors: Record<string, string[]> | null;
  trace_id: string;
  retryable: boolean;
}

export class HttpError extends Error {
  readonly status: number;
  readonly error: ApiError;
  readonly retryable: boolean;

  constructor(status: number, error: ApiError) {
    super(`${status} ${error.code}: ${error.message}`);
    this.name = "HttpError";
    this.status = status;
    this.error = error;
    this.retryable = error.retryable;
  }
}

export interface HealthResponse {
  status: string;
  trace_id: string;
}

export interface ReadyResponse {
  status: string;
  database: string;
  trace_id: string;
}

export interface ApiClientOptions {
  baseUrl: string;
  fetch?: typeof fetch;
  headers?: Record<string, string>;
}
