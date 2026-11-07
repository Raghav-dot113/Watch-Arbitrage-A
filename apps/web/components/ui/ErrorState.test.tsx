import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorState } from "./ErrorState";

describe("ErrorState", () => {
  it("renders title and description", () => {
    render(
      <ErrorState
        title="Something went wrong"
        description="Unable to load opportunities at this time."
      />
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(
      screen.getByText("Unable to load opportunities at this time.")
    ).toBeInTheDocument();
  });

  it("calls onRetry when retry button clicked", () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        title="Something went wrong"
        retryLabel="Try again"
        onRetry={onRetry}
      />
    );
    const button = screen.getByRole("button", { name: /try again/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("does not render retry button when no handler provided", () => {
    render(<ErrorState title="Something went wrong" />);
    expect(screen.queryByRole("button", { name: /try again/i })).not.toBeInTheDocument();
  });
});
