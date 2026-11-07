import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserMenu } from "./UserMenu";

const mockUseAuth = vi.hoisted(() => vi.fn());

vi.mock("../../app/AuthProvider", () => ({
  useAuth: mockUseAuth,
}));

beforeEach(() => {
  mockUseAuth.mockImplementation(() => ({
    user: {
      userId: "dev|dealer@example.com",
      email: "dealer@example.com",
      name: "Dealer User",
      orgId: "org_dev",
      orgName: "Dev Organization",
      role: "dealer",
    },
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  }));
});

describe("UserMenu", () => {
  it("renders user name and email when open with a user", () => {
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.getByText("Dealer User")).toBeInTheDocument();
    expect(screen.getByText("dealer@example.com")).toBeInTheDocument();
  });

  it("renders Sign out menu item", () => {
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.getByText("Sign out")).toBeInTheDocument();
  });

  it("renders Profile and Organization menu items", () => {
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Organization")).toBeInTheDocument();
  });

  it("does not render Sign out when no user", () => {
    mockUseAuth.mockImplementation(() => ({
      user: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    }));
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.queryByText("Sign out")).not.toBeInTheDocument();
  });
});
