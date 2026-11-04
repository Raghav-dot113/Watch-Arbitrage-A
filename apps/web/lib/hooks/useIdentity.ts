import { useQuery } from "@tanstack/react-query";
import { getMe, type MeResponse } from "../api";

export function useIdentity() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      return getMe();
    },
    retry: 1,
  });
}

export type { MeResponse };
