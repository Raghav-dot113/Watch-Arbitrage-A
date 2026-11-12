"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "../../components/shell/AppShell";
import { LoadingState } from "../../components/ui/LoadingState";
import { useAuth } from "../AuthProvider";

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, router, user]);

  if (isLoading || !user) {
    return <LoadingState label="Loading your session" fullPage />;
  }

  return <AppShell>{children}</AppShell>;
}
