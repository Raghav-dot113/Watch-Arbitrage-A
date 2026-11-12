"use client";

import "../../lib/bryntum/license";
import { useCallback, useMemo } from "react";
import { Box } from "@mui/material";
import type { Model } from "@bryntum/core-business";
import type { GridColumnConfig } from "@bryntum/grid-business";
import { BryntumGrid } from "@bryntum/grid-react-business";

export interface ChronoArbGridColumn<Row> {
  field: string;
  text: string;
  width?: number;
  flex?: number;
  render?: (row: Row) => string;
}

export interface ChronoArbGridAction<Row> {
  key: string;
  label: string | ((row: Row) => string);
  onClick: (row: Row) => void;
  tone?: "default" | "danger";
}

export interface ChronoArbGridProps<Row extends { id: string }> {
  ariaLabel: string;
  rows: Row[];
  columns: ChronoArbGridColumn<Row>[];
  actions?: ChronoArbGridAction<Row>[];
  height?: number;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => {
    switch (character) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      default:
        return "&#39;";
    }
  });
}

function cellText<Row extends { id: string }>(
  column: ChronoArbGridColumn<Row>,
  row: Row,
): string {
  if (column.render) {
    return escapeHtml(column.render(row));
  }
  const value = (row as Record<string, unknown>)[column.field];
  return escapeHtml(value == null || value === "" ? "—" : String(value));
}

function actionLabel<Row>(label: string | ((row: Row) => string), row: Row): string {
  return typeof label === "function" ? label(row) : label;
}

export function ChronoArbGrid<Row extends { id: string }>({
  ariaLabel,
  rows,
  columns,
  actions = [],
  height = 420,
}: ChronoArbGridProps<Row>) {
  const gridColumns = useMemo<GridColumnConfig[]>(() => {
    const mapped: GridColumnConfig[] = columns.map((column) => ({
      field: column.field,
      text: column.text,
      width: column.width,
      flex: column.flex,
      // Values are escaped in cellText before they reach Bryntum.
      htmlEncode: false,
      renderer: ({ record }: { record: Model }) =>
        cellText(column, (record as unknown as { data: Row }).data),
    }));

    if (actions.length > 0) {
      mapped.push({
        field: "__actions",
        text: "Actions",
        width: 230,
        sortable: false,
        filterable: false,
        htmlEncode: false,
        renderer: ({ record }: { record: Model }) => {
          const row = (record as unknown as { data: Row }).data;
          return actions
            .map((action) => {
              const label = escapeHtml(actionLabel(action.label, row));
              const tone = action.tone === "danger" ? " is-danger" : "";
              return `<button type="button" class="chronoarb-grid-action${tone}" data-grid-action="${escapeHtml(action.key)}" data-grid-row-id="${escapeHtml(row.id)}">${label}</button>`;
            })
            .join("");
        },
      });
    }

    return mapped;
  }, [actions, columns]);

  const store = useMemo(() => ({ pageSize: 25 }), []);

  const handleCellClick = useCallback(
    ({
      event,
      record,
    }: {
      event: { target: EventTarget | null; preventDefault: () => void };
      record: Model;
    }) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const button = target.closest<HTMLElement>("button[data-grid-action]");
      if (!button) {
        return;
      }
      event.preventDefault();
      const action = actions.find(
        (candidate) => candidate.key === button.dataset.gridAction,
      );
      if (action) {
        action.onClick((record as unknown as { data: Row }).data);
      }
    },
    [actions],
  );

  return (
    <Box sx={{ minWidth: 0 }}>
      <BryntumGrid
        ariaLabel={ariaLabel}
        cls="chronoarb-bryntum-grid"
        height={height}
        data={rows}
        store={store}
        columns={gridColumns}
        bbar={{ type: "pagingtoolbar" }}
        sortFeature
        filterFeature
        filterBarFeature
        columnPickerFeature
        columnReorderFeature
        columnResizeFeature
        cellTooltipFeature
        cellEditFeature={false}
        cellCopyPasteFeature={false}
        rowCopyPasteFeature={false}
        onCellClick={handleCellClick}
      />
    </Box>
  );
}
