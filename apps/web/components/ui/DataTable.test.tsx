import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable } from "./DataTable";

const columns = [
  { key: "id", label: "ID" },
  { key: "name", label: "Name" },
  { key: "status", label: "Status" },
];

describe("DataTable", () => {
  it("renders table with title, columns and rows", () => {
    const data = [
      { id: "1", name: "Alpha", status: "published" },
      { id: "2", name: "Beta", status: "dismissed" },
    ] as unknown as Record<string, unknown>[];
    render(<DataTable title="Items" columns={columns as any} data={data} />);
    expect(screen.getByText("Items")).toBeInTheDocument();
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.getByText("published")).toBeInTheDocument();
    expect(screen.getByText("dismissed")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<DataTable title="Items" columns={columns as any} data={[]} />);
    expect(screen.getByText("No data available.")).toBeInTheDocument();
  });

  it("calls onRowClick with the row data", () => {
    const onRowClick = vi.fn();
    const data = [{ id: "1", name: "Alpha", status: "published" }] as unknown as Record<string, unknown>[];
    render(
      <DataTable title="Items" columns={columns as any} data={data} onRowClick={onRowClick} />
    );
    const row = screen.getByText("Alpha").closest("tr") as HTMLElement;
    fireEvent.click(row);
    expect(onRowClick).toHaveBeenCalledTimes(1);
  });

  it("uses custom renderCell when provided", () => {
    const data = [{ id: "1", name: "Alpha", status: "published" }] as unknown as Record<string, unknown>[];
    render(
      <DataTable
        title="Items"
        columns={columns as any}
        data={data}
        renderCell={() => <strong>custom</strong>}
      />
    );
    expect(screen.getAllByText("custom")).toHaveLength(3);
  });
});
