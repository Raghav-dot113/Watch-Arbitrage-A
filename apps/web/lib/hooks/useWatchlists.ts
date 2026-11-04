import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createWatchList,
  deleteWatchList,
  listWatchLists,
  updateWatchList,
  type WatchList,
  type WatchListCreateRequest,
  type WatchListUpdateRequest,
} from "../api";

export function useWatchlists() {
  return useQuery({
    queryKey: ["watchLists"],
    queryFn: async () => {
      return listWatchLists();
    },
  });
}

export function useCreateWatchList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: WatchListCreateRequest) => createWatchList(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchLists"] });
    },
  });
}

export function useUpdateWatchList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      watchListId,
      body,
    }: {
      watchListId: string;
      body: WatchListUpdateRequest;
    }) => updateWatchList(watchListId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchLists"] });
    },
  });
}

export function useDeleteWatchList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (watchListId: string) => deleteWatchList(watchListId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchLists"] });
    },
  });
}

export type { WatchList };
