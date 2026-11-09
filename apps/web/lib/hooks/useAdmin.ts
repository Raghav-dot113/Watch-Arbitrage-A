import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listAuditEvents,
  listDuplicateGroups,
  listFeatureFlags,
  listSources,
  listUnmatchedListings,
  resolveUnmatchedListing,
  updateFeatureFlag,
  updateSource,
  type AuditEvent,
  type DuplicateGroup,
  type FeatureFlag,
  type FeatureFlagPatchRequest,
  type SourceAdmin,
  type UnmatchedListing,
} from "../api";

export function useSources() {
  return useQuery({
    queryKey: ["adminSources"],
    queryFn: async () => {
      return listSources();
    },
  });
}

export function useUpdateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sourceId, isEnabled }: { sourceId: string; isEnabled: boolean }) =>
      updateSource(sourceId, isEnabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminSources"] });
    },
  });
}

export function useFeatureFlags() {
  return useQuery({
    queryKey: ["adminFeatureFlags"],
    queryFn: async () => {
      return listFeatureFlags();
    },
  });
}

export function useUpdateFeatureFlag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      flagId,
      body,
    }: {
      flagId: string;
      body: FeatureFlagPatchRequest;
    }) => updateFeatureFlag(flagId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminFeatureFlags"] });
    },
  });
}

export function useAuditEvents() {
  return useQuery({
    queryKey: ["adminAuditEvents"],
    queryFn: async () => {
      return listAuditEvents();
    },
  });
}

export function useUnmatchedListings() {
  return useQuery({
    queryKey: ["adminUnmatchedListings"],
    queryFn: async () => {
      return listUnmatchedListings();
    },
  });
}

export function useResolveUnmatchedListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      listingId,
      referenceId,
    }: {
      listingId: string;
      referenceId: string;
    }) => resolveUnmatchedListing(listingId, referenceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminUnmatchedListings"] });
    },
  });
}

export function useDuplicateGroups() {
  return useQuery({
    queryKey: ["adminDuplicateGroups"],
    queryFn: async () => {
      return listDuplicateGroups();
    },
  });
}

export type {
  AuditEvent,
  DuplicateGroup,
  FeatureFlag,
  SourceAdmin,
  UnmatchedListing,
};
