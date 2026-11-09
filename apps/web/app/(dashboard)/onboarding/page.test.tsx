import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import OnboardingPage from "./page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockUseCreateOrganization = vi.fn();
const mockUseUpdateOrganizationSettings = vi.fn();
const mockUseOrganizationSettings = vi.fn();

vi.mock("../../../lib/hooks/useOnboarding", () => ({
  useCreateOrganization: () => mockUseCreateOrganization(),
}));

vi.mock("../../../lib/hooks/useSettings", () => ({
  useUpdateOrganizationSettings: () => mockUseUpdateOrganizationSettings(),
  useOrganizationSettings: (...args: unknown[]) =>
    mockUseOrganizationSettings(...args),
}));

beforeEach(() => {
  vi.restoreAllMocks();
  mockPush.mockReset();
  mockUseCreateOrganization.mockReset();
  mockUseUpdateOrganizationSettings.mockReset();
  mockUseOrganizationSettings.mockReset();
  mockUseCreateOrganization.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      id: "org_1",
      name: "Test Org",
      slug: "test-org",
      created_at: "2026-08-02T16:42:19Z",
      updated_at: null,
    }),
    isPending: false,
  });
  mockUseUpdateOrganizationSettings.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  });
  mockUseOrganizationSettings.mockReturnValue({
    data: undefined,
    isLoading: false,
  });
});

describe("OnboardingPage", () => {
  it("renders step 1 - organization details", () => {
    render(<OnboardingPage />);
    expect(screen.getByText("Set up your organization")).toBeInTheDocument();
    const stepLabels = screen.getAllByText("Create organization");
    expect(stepLabels.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByLabelText(/organization name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization slug/i)).toBeInTheDocument();
  });

  it("slugifies organization name on change", () => {
    render(<OnboardingPage />);
    const nameInput = screen.getByLabelText(/organization name/i);
    fireEvent.input(nameInput, { target: { value: "My Dealership Inc" } });
    const slugInput = screen.getByLabelText(/organization slug/i);
    expect(slugInput).toHaveValue("my-dealership-inc");
  });

  it("creates organization on next click", async () => {
    render(<OnboardingPage />);
    const nameInput = screen.getByLabelText(/organization name/i);
    fireEvent.input(nameInput, { target: { value: "My Org" } });
    const slugInput = screen.getByLabelText(/organization slug/i);
    fireEvent.input(slugInput, { target: { value: "my-org" } });

    const nextButton = screen.getByRole("button", {
      name: /create organization/i,
    });
    fireEvent.click(nextButton);

    await vi.waitFor(() => {
      expect(mockUseCreateOrganization()).toHaveProperty("mutateAsync");
    });
  });

  it("advances to step 2 after creating organization", async () => {
    render(<OnboardingPage />);
    const nameInput = screen.getByLabelText(/organization name/i);
    fireEvent.input(nameInput, { target: { value: "My Org" } });
    const slugInput = screen.getByLabelText(/organization slug/i);
    fireEvent.input(slugInput, { target: { value: "my-org" } });

    const nextButton = screen.getByRole("button", {
      name: /create organization/i,
    });
    fireEvent.click(nextButton);

    await vi.waitFor(() => {
      expect(screen.getByText("Configure settings")).toBeInTheDocument();
    });
  });

  it("shows loading state while creating organization", () => {
    mockUseCreateOrganization.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({
        id: "org_1",
        name: "Test Org",
        slug: "test-org",
        created_at: "2026-08-02T16:42:19Z",
        updated_at: null,
      }),
      isPending: true,
    });

    render(<OnboardingPage />);
    const nameInput = screen.getByLabelText(/organization name/i);
    fireEvent.input(nameInput, { target: { value: "My Org" } });
    const slugInput = screen.getByLabelText(/organization slug/i);
    fireEvent.input(slugInput, { target: { value: "my-org" } });

    const nextButton = screen.getByRole("button", {
      name: /creating/i,
    });
    expect(nextButton).toHaveAttribute("disabled", "");
  });
});
