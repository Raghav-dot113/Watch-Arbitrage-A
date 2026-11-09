import { useQuery } from "@tanstack/react-query";
import { getHealth, getReady, type HealthResponse, type ReadyResponse } from "../api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      return getHealth();
    },
    refetchInterval: 30000,
  });
}

export function useReady() {
  return useQuery({
    queryKey: ["ready"],
    queryFn: async () => {
      return getReady();
    },
  });
}

export type { HealthResponse, ReadyResponse };
