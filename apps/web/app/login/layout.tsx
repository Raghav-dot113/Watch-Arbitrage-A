import { Suspense, type ReactNode } from "react";
import { LoadingState } from "../../components/ui/LoadingState";

export default function LoginLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<LoadingState label="Loading sign-in" fullPage />}>
      {children}
    </Suspense>
  );
}
