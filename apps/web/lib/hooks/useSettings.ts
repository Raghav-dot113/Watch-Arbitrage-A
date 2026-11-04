import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCheckoutSession,
  createPortalSession,
  getIntegrationStatus,
  getOrganizationSettings,
  getSubscription,
  linkTelegram,
  patchOrganizationSettings,
  registerPushDevice,
  unlinkTelegram,
  unregisterPushDevice,
  type IntegrationStatusResponse,
  type OrganizationSettingsPatchRequest,
  type OrganizationSettingsResponse,
  type PushDeviceResponse,
  type SubscriptionResponse,
  type TelegramLinkResponse,
  type FeeDefaults,
} from "../api";

export function useOrganizationSettings() {
  return useQuery({
    queryKey: ["organizationSettings"],
    queryFn: async () => {
      return getOrganizationSettings();
    },
  });
}

export function useUpdateOrganizationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: OrganizationSettingsPatchRequest) =>
      patchOrganizationSettings(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizationSettings"] });
    },
  });
}

export function useSubscription() {
  return useQuery({
    queryKey: ["subscription"],
    queryFn: async () => {
      return getSubscription();
    },
  });
}

export function useCreateCheckoutSession() {
  return useMutation({
    mutationFn: (body: Parameters<typeof createCheckoutSession>[0]) =>
      createCheckoutSession(body),
  });
}

export function useCreatePortalSession() {
  return useMutation({
    mutationFn: () => createPortalSession(),
  });
}

export function useIntegrationStatus() {
  return useQuery({
    queryKey: ["integrationStatus"],
    queryFn: async () => {
      return getIntegrationStatus();
    },
  });
}

export function useLinkTelegram() {
  return useMutation({
    mutationFn: () => linkTelegram(),
    onSuccess: () => {
      // invalidate integration status after linking
    },
  });
}

export function useUnlinkTelegram() {
  return useMutation({
    mutationFn: () => unlinkTelegram(),
  });
}

export function useRegisterPushDevice() {
  return useMutation({
    mutationFn: (body: Parameters<typeof registerPushDevice>[0]) =>
      registerPushDevice(body),
  });
}

export function useUnregisterPushDevice() {
  return useMutation({
    mutationFn: (deviceId: string) => unregisterPushDevice(deviceId),
  });
}

export type {
  OrganizationSettingsResponse,
  OrganizationSettingsPatchRequest,
  FeeDefaults,
  SubscriptionResponse,
  IntegrationStatusResponse,
  PushDeviceResponse,
  TelegramLinkResponse,
};
