import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import LoginPage from "./page";

const mockLogin = vi.fn();
const mockPush = vi.fn();

vi.mock("../AuthProvider", () => ({
  AuthProvider: vi.fn(({ children }: { children: React.ReactNode }) => children),
  useAuth: () => ({
    login: mockLogin,
    isLoading: false,
    user: null,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: () => null }),
}));

beforeEach(() => {
  mockLogin.mockReset();
  mockPush.mockReset();
  vi.restoreAllMocks();
  (globalThis.fetch as unknown) = vi.fn(() =>
    Response.json({ ok: true })
  ) as unknown as typeof globalThis.fetch;
});

describe("LoginPage", () => {
  it("renders the email form and submit button", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeInTheDocument();
  });

  it("calls login with the email on submit and navigates to callback", async () => {
    mockLogin.mockResolvedValue(undefined);
    render(<LoginPage />);
    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "dealer@example.com" } });
    fireEvent.submit(screen.getByRole("button", { name: /continue/i }));

    await act(async () => {});
    expect(mockLogin).toHaveBeenCalledWith("dealer@example.com");
    expect(mockPush).toHaveBeenCalledWith("/opportunities");
  });

  it("shows error when login fails", async () => {
    mockLogin.mockRejectedValue(new Error("bad credentials"));
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "dealer@example.com" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /continue/i }));

    await act(async () => {});
    expect(screen.getByText("bad credentials")).toBeInTheDocument();
  });
});
