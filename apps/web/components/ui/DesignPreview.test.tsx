import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DesignPreview } from "./DesignPreview";

describe("DesignPreview", () => {
  it("renders the design token preview heading", () => {
    render(<DesignPreview />);
    expect(screen.getByText("Design Token Preview")).toBeInTheDocument();
  });

  it("renders palette color swatches", () => {
    render(<DesignPreview />);
    expect(screen.getByText("Slate 50")).toBeInTheDocument();
    expect(screen.getByText("Blue 500")).toBeInTheDocument();
    expect(screen.getByText("Rose 500")).toBeInTheDocument();
  });

  it("renders semantic color swatches", () => {
    render(<DesignPreview />);
    expect(screen.getByText("Primary main")).toBeInTheDocument();
    expect(screen.getByText("Error main")).toBeInTheDocument();
    expect(screen.getByText("Success main")).toBeInTheDocument();
  });

  it("renders typography samples", () => {
    render(<DesignPreview />);
    expect(screen.getByText("H1 - Display heading")).toBeInTheDocument();
    expect(screen.getByText("Body 1")).toBeInTheDocument();
  });

  it("renders spacing and radii info", () => {
    render(<DesignPreview />);
    expect(screen.getByText(/Base spacing unit: 4px/)).toBeInTheDocument();
    expect(screen.getByText(/Border radii:/)).toBeInTheDocument();
  });
});
