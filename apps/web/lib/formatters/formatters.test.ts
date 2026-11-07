import { describe, expect, it } from "vitest";
import {
  formatCurrency,
  formatMoney,
  formatPercent,
  type Money,
} from "./currency";
import { formatDate, formatDateTime, formatRelativeTime } from "./date";

describe("formatCurrency", () => {
  it("formats a numeric value as USD currency", () => {
    expect(formatCurrency(11150, "USD")).toBe("$11,150.00");
  });

  it("formats a string value as currency", () => {
    expect(formatCurrency("11150.00", "USD")).toBe("$11,150.00");
  });

  it("returns em dash for null/undefined", () => {
    expect(formatCurrency(null)).toBe("—");
    expect(formatCurrency(undefined)).toBe("—");
  });

  it("returns em dash for NaN string", () => {
    expect(formatCurrency("not-a-number")).toBe("—");
  });

  it("uses the provided currency", () => {
    expect(formatCurrency(100, "EUR")).toBe("\u20AC100.00");
  });
});

describe("formatMoney", () => {
  it("formats a Money object", () => {
    const money: Money = { value: "5000.00", currency: "USD" };
    expect(formatMoney(money)).toBe("$5,000.00");
  });

  it("returns em dash for null", () => {
    expect(formatMoney(null)).toBe("—");
  });
});

describe("formatPercent", () => {
  it("formats a percent value", () => {
    expect(formatPercent(15.5)).toBe("15.50%");
  });

  it("formats a string percent value", () => {
    expect(formatPercent("15.5")).toBe("15.50%");
  });

  it("returns em dash for null/undefined", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(undefined)).toBe("—");
  });
});

describe("formatDate", () => {
  it("formats an ISO date string", () => {
    expect(formatDate("2026-08-02T16:42:19Z")).toBe("Aug 2, 2026");
  });

  it("returns em dash for null/undefined", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("returns em dash for invalid date", () => {
    expect(formatDate("not-a-date")).toBe("—");
  });
});

describe("formatDateTime", () => {
  it("formats an ISO datetime string", () => {
    const result = formatDateTime("2026-08-02T16:42:19Z");
    expect(result).toContain("2026");
    expect(result).toContain("Aug");
  });

  it("returns em dash for null/undefined", () => {
    expect(formatDateTime(null)).toBe("—");
  });
});

describe("formatRelativeTime", () => {
  it("returns 'just now' for very recent timestamps", () => {
    const now = new Date().toISOString();
    expect(formatRelativeTime(now)).toBe("just now");
  });

  it("returns minutes ago for recent timestamps", () => {
    const fiveMinsAgo = new Date(Date.now() - 5 * 60000).toISOString();
    expect(formatRelativeTime(fiveMinsAgo)).toBe("5 min ago");
  });

  it("returns hours ago for older timestamps", () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 3600000).toISOString();
    expect(formatRelativeTime(threeHoursAgo)).toBe("3 hr ago");
  });

  it("returns days ago for old timestamps", () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 86400000).toISOString();
    expect(formatRelativeTime(twoDaysAgo)).toBe("2 days ago");
  });

  it("returns em dash for null/undefined", () => {
    expect(formatRelativeTime(null)).toBe("—");
  });
});
