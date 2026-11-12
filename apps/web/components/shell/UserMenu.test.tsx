import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserMenu } from "./UserMenu";

describe("UserMenu", () => {
  it("renders the demo workspace identity", () => {
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.getByText("Demo Dealer")).toBeInTheDocument();
    expect(screen.getByText("owner@demo.example.com")).toBeInTheDocument();
  });

  it("does not render a sign-out action in demo mode", () => {
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.queryByText("Sign out")).not.toBeInTheDocument();
  });

  it("renders Profile and Organization menu items", () => {
    const anchorEl = document.createElement("div");
    render(<UserMenu anchorEl={anchorEl} open onClose={vi.fn()} />);
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Organization")).toBeInTheDocument();
  });
});
