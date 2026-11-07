import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState
        title="No opportunities"
        description="Create a watch list to start receiving opportunities."
      />
    );
    expect(screen.getByText("No opportunities")).toBeInTheDocument();
    expect(
      screen.getByText("Create a watch list to start receiving opportunities.")
    ).toBeInTheDocument();
  });

  it("renders action button and calls onAction when clicked", () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No opportunities"
        actionLabel="Create watch list"
        onAction={onAction}
      />
    );
    const button = screen.getByRole("button", { name: /create watch list/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("does not render action when no handler provided", () => {
    render(<EmptyState title="No opportunities" actionLabel="Create" />);
    expect(screen.queryByRole("button", { name: /create/i })).not.toBeInTheDocument();
  });
});
