import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createOrganization,
  type OrganizationCreateRequest,
} from "../api";

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: OrganizationCreateRequest) => createOrganization(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      queryClient.invalidateQueries({ queryKey: ["organizationSettings"] });
    },
  });
}

export type { OrganizationCreateRequest };
