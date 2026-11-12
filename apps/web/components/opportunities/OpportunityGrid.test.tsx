import { describe, expect, it, vi } from "vitest";
import { compareDecimalStrings } from "./OpportunityGrid";

vi.mock("@bryntum/grid-react-business", () => ({
  BryntumGrid: () => null,
}));

describe("compareDecimalStrings", () => {
  it("compares decimal values exactly without floating-point conversion", () => {
    expect(compareDecimalStrings("2500.00", "2499.99")).toBeGreaterThan(0);
    expect(compareDecimalStrings("1.2", "1.20")).toBe(0);
    expect(compareDecimalStrings("-0.01", "0")).toBeLessThan(0);
  });

  it("sorts missing values before present values", () => {
    expect(compareDecimalStrings(null, "0")).toBeLessThan(0);
    expect(compareDecimalStrings("0", null)).toBeGreaterThan(0);
    expect(compareDecimalStrings(undefined, null)).toBe(0);
  });
});
