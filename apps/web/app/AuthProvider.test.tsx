import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, fireEvent } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthProvider";

const session = {
  userId: "dev|user@example.com",
  email: "user@example.com",
  name: "user",
  orgId: "org_dev",
  orgName: "Dev Organization",
  role: "dealer",
};

type FetchArgs = [input: RequestInfo | URL, init?: RequestInit];

function mockFetch(handler: (url: string, init?: RequestInit) => Response) {
  return vi.fn((input, init) => handler(String(input), init)) as unknown as typeof globalThis.fetch;
}

function Harness() {
  const { user, isLoading, login, logout, refresh } = useAuth();
  return (
    <div>
      <span data-testid="user">{user?.email ?? "none"}</span>
      <span data-testid="loading">{String(isLoading)}</span>
      <button data-testid="login-btn" onClick={() => login("new@example.com")}>
        login
      </button>
      <button data-testid="logout-btn" onClick={logout}>logout</button>
      <button data-testid="refresh-btn" onClick={refresh}>refresh</button>
    </div>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  (globalThis.fetch as unknown) = mockFetch((url) => {
    if (url.endsWith("/api/auth/session")) {
      return Response.json({ ok: true, user: session });
    }
    if (url.endsWith("/api/auth/login")) {
      return Response.json({ ok: true, user: session });
    }
    if (url.endsWith("/api/auth/logout")) {
      return Response.json({ ok: true });
    }
    return Response.json({ ok: false }, { status: 404 });
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AuthProvider", () => {
  it("hydrates user from session on mount", async () => {
    render(
      <AuthProvider>
        <Harness />
      </AuthProvider>
    );
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(screen.getByTestId("user").textContent).toBe("user@example.com");
  });

  it("login sets the user", async () => {
    render(
      <AuthProvider>
        <Harness />
      </AuthProvider>
    );
    await act(async () => {
      fireEvent.click(screen.getByTestId("login-btn"));
    });
    expect(screen.getByTestId("user").textContent).toBe("user@example.com");
  });

  it("logout clears the user", async () => {
    render(
      <AuthProvider>
        <Harness />
      </AuthProvider>
    );
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
      fireEvent.click(screen.getByTestId("logout-btn"));
    });
    expect(screen.getByTestId("user").textContent).toBe("none");
  });

  it("throws when useAuth used outside provider", () => {
    let error: Error | null = null;
    function Broken() {
      try {
        useAuth();
      } catch (e) {
        error = e as Error;
      }
      return null;
    }
    render(<Broken />);
    expect(error).not.toBeNull();
    expect(error!.message).toContain("AuthProvider");
  });
});
