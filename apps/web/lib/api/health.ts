import type { HealthResponse, ReadyResponse } from "./types";
import { apiClient } from "./client";

export async function getHealth(): Promise<HealthResponse> {
  return apiClient.get("/health") as Promise<HealthResponse>;
}

export async function getReady(): Promise<ReadyResponse> {
  return apiClient.get("/ready") as Promise<ReadyResponse>;
}