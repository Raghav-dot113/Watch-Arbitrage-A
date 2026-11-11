import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import DashboardLayout from "./layout";

const { mockUseAuth, mockReplace } = vi.hoisted(() => ({
  mockUseAuth: vi.fn(),
  mockReplace: vi.fn(),
}));

vi.mock("../AuthProvider", () => ({ useAuth: mockUseAuth }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
}));
vi.mock("../../components/shell/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));
vi.mock("../../components/ui/LoadingState", () => ({
  LoadingState: ({ label }: { label: string }) => (
    <div role="status">{label}</div>
  ),
}));

beforeEach(() => {
  mockUseAuth.mockReset();
  mockReplace.mockReset();
});

describe("DashboardLayout", () => {
  it("does not mount page queries until session hydration completes", () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: true });

    render(
      <DashboardLayout>
        <div>Page data request</div>
      </DashboardLayout>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Loading your session");
    expect(screen.queryByText("Page data request")).not.toBeInTheDocument();
  });

  it("redirects users without a session to login", async () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: false });

    render(
      <DashboardLayout>
        <div>Private dashboard</div>
      </DashboardLayout>,
    );

    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("Private dashboard")).not.toBeInTheDocument();
  });

  it("renders dashboard pages after session hydration", () => {
    mockUseAuth.mockReturnValue({
      user: { email: "dealer@example.com" },
      isLoading: false,
    });

    render(
      <DashboardLayout>
        <div>Private dashboard</div>
      </DashboardLayout>,
    );

    expect(screen.getByText("Private dashboard")).toBeInTheDocument();
  });
});
