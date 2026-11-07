import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { ReactNode } from "react";
import OpportunitiesPage from "./page";

const mockPush = vi.fn();
const mockUseOpportunities = vi.fn();

type GridRow = Record<string, unknown> & { id: string };
type GridColumn = {
  field?: string;
  headerName?: string;
  cellRenderer?: (params: { value: unknown; data: GridRow }) => ReactNode;
  valueFormatter?: (params: { value: unknown; data: GridRow }) => ReactNode;
};

vi.mock("ag-grid-react", () => ({
  AgGridReact: ({
    rowData = [],
    columnDefs = [],
    onRowClicked,
  }: {
    rowData?: GridRow[];
    columnDefs?: GridColumn[];
    onRowClicked?: (event: { data: GridRow }) => void;
  }) => (
    <div role="grid" aria-label="Opportunity feed">
      {rowData.map((row, index) => (
        <div
          key={row.id}
          role="row"
          data-testid={`opportunity-row-${index}`}
          onClick={() => onRowClicked?.({ data: row })}
        >
          {columnDefs.map((column) => {
            const value = column.field ? row[column.field] : null;
            const params = { value, data: row };
            let output: ReactNode = value == null ? "—" : String(value);
            if (column.cellRenderer) {
              output = column.cellRenderer(params);
            } else if (column.valueFormatter) {
              output = column.valueFormatter(params);
            }
            return (
              <div role="gridcell" key={column.field ?? column.headerName}>
                {output}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  ),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("../../../lib/hooks/useOpportunities", () => ({
  useOpportunities: (...args: unknown[]) => mockUseOpportunities(...args),
}));

const baseOpportunity = {
  id: "opp_1",
  state: "published",
  score: "85.5",
  created_at: "2026-08-02T16:42:19Z",
  valuation: {
    expected_net_profit: "2500.00",
    roi: "32.4",
  },
};

beforeEach(() => {
  mockPush.mockReset();
  mockUseOpportunities.mockReset();
});

describe("OpportunitiesPage", () => {
  it("renders the page header", () => {
    mockUseOpportunities.mockReturnValue({
      data: { data: [], meta: { trace_id: "t1", next_cursor: null, has_more: false } },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByText("Opportunities")).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseOpportunities.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getAllByText("Loading opportunities")).toHaveLength(2);
  });

  it("shows ErrorState on error", () => {
    mockUseOpportunities.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("boom"),
    });

    render(<OpportunitiesPage />);
    expect(screen.getByText("Unable to load opportunities")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("shows EmptyState when no opportunities", () => {
    mockUseOpportunities.mockReturnValue({
      data: { data: [], meta: { trace_id: "t1", next_cursor: null, has_more: false } },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByText("No opportunities")).toBeInTheDocument();
  });

  it("renders opportunity rows in the data table", () => {
    mockUseOpportunities.mockReturnValue({
      data: {
        data: [baseOpportunity],
        meta: { trace_id: "t1", next_cursor: null, has_more: false },
      },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    expect(screen.getByRole("grid", { name: "Opportunity feed" })).toBeInTheDocument();
    const row = screen.getByTestId("opportunity-row-0");
    expect(row).toBeInTheDocument();
    expect(row).toHaveTextContent("opp_1");
    expect(row).toHaveTextContent("Published");
    expect(row).toHaveTextContent("$2,500.00");
  });

  it("navigates to opportunity detail on row click", () => {
    mockUseOpportunities.mockReturnValue({
      data: {
        data: [baseOpportunity],
        meta: { trace_id: "t1", next_cursor: null, has_more: false },
      },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OpportunitiesPage />);
    const row = screen.getByTestId("opportunity-row-0") as HTMLElement;
    fireEvent.click(row);
    expect(mockPush).toHaveBeenCalledWith("/opportunities/opp_1");
  });
});
