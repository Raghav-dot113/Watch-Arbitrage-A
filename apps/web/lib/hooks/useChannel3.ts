import { useQuery } from "@tanstack/react-query";
import { searchChannel3, type Channel3SearchRequest } from "../api";

export function useChannel3Search(params: Channel3SearchRequest | null) {
  return useQuery({
    queryKey: ["channel3-search", params],
    queryFn: async () => {
      if (!params) throw new Error("Search parameters required");
      return searchChannel3(params);
    },
    enabled: !!params,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  });
}

export type { Channel3SearchRequest, Channel3SearchResponse, Channel3Product, Channel3Offer, Channel3Price, Channel3Brand, Channel3Image } from "../api";