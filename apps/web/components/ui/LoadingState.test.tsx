import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingState } from "./LoadingState";

describe("LoadingState", () => {
  it("renders the loading label and circular progress", () => {
    render(<LoadingState label="Fetching opportunities" />);
    expect(screen.getByText("Fetching opportunities", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders full-page variant with min-height", () => {
    render(<LoadingState fullPage label="Loading full page" />);
    const progress = screen.getByRole("progressbar");
    expect(progress).toBeInTheDocument();
    const container = progress.closest("div") as HTMLElement;
    expect(container).toHaveStyle("min-height: 300px");
  });
});
