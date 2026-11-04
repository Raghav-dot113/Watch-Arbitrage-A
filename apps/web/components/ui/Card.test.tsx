import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Card } from "./Card";
import { PageContainer } from "./PageContainer";

describe("Card", () => {
  it("renders title, subtitle and children", () => {
    render(
      <Card title="Card title" subtitle="Card subtitle">
        <span data-testid="card-content">content</span>
      </Card>
    );
    expect(screen.getByText("Card title")).toBeInTheDocument();
    expect(screen.getByText("Card subtitle")).toBeInTheDocument();
    expect(screen.getByTestId("card-content")).toBeInTheDocument();
  });
});

describe("PageContainer", () => {
  it("renders children", () => {
    render(
      <PageContainer>
        <span data-testid="page-content">page content</span>
      </PageContainer>
    );
    expect(screen.getByTestId("page-content")).toBeInTheDocument();
  });
});
