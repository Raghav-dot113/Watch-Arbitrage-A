import { describe, expect, it } from "vitest";
import {
  LoadingState,
  EmptyState,
  ErrorState,
  DataTable,
  Card,
  PageContainer,
} from "./index";

describe("ui index barrel", () => {
  it("exports all shared components", () => {
    expect(LoadingState).toBeDefined();
    expect(EmptyState).toBeDefined();
    expect(ErrorState).toBeDefined();
    expect(DataTable).toBeDefined();
    expect(Card).toBeDefined();
    expect(PageContainer).toBeDefined();
  });
});
