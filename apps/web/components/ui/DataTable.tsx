"use client";

import { Box, Typography, TableContainer, Table, TableHead, TableRow, TableCell, TableBody, Paper } from "@mui/material";

export interface DataTableColumn {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
  sortable?: boolean;
}

export interface DataTableProps<T extends Record<string, unknown>> {
  title: string;
  columns: DataTableColumn[];
  data: T[];
  emptyDescription?: string;
  /**
   * Render a custom cell for a given column key and row.
   */
  renderCell?: (key: string, value: unknown, row: T) => React.ReactNode;
  /**
   * Optional row click handler.
   */
  onRowClick?: (row: T) => void;
  /**
   * Test id prefix for rows.
   */
  testIdPrefix?: string;
}

export function DataTable<T extends Record<string, unknown>>({
  title,
  columns,
  data,
  emptyDescription,
  renderCell,
  onRowClick,
  testIdPrefix = "row",
}: DataTableProps<T>) {
  if (!data || data.length === 0) {
    return (
      <Paper variant="outlined" sx={{ p: 0, bgcolor: "background.paper", borderColor: "divider" }}>
        <Box sx={{ p: 3, textAlign: "center" }}>
          <Typography variant="body2" color="text.secondary">
            {emptyDescription ?? "No data available."}
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 0, bgcolor: "background.paper", borderColor: "divider" }}>
      <Box sx={{ px: 2, pb: 1 }}>
        <Typography variant="subtitle2" component="h3" sx={{ fontWeight: 600, color: "text.primary" }}>
          {title}
        </Typography>
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ "& th": { bgcolor: "action.disabledBackground", color: "text.secondary", fontWeight: 500, borderBottom: `1px solid`, borderColor: "divider" } }}>
              {columns.map((column) => (
                <TableCell
                  key={column.key}
                  align={column.align}
                  sx={{ px: 2, py: 1, fontSize: "0.8125rem", textTransform: "uppercase", letterSpacing: "0.05em" }}
                >
                  {column.label}
                </TableCell>
              ))}
              {onRowClick && <TableCell sx={{ px: 2, py: 1 }} />}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, index) => (
              <TableRow
                key={String(row.id ?? index)}
                hover
                sx={{
                  "&:hover": { bgcolor: "action.hover" },
                  cursor: onRowClick ? "pointer" : undefined,
                  "& td": { borderBottom: `1px solid`, borderColor: "divider" },
                }}
                onClick={() => onRowClick?.(row)}
                role="row"
                tabIndex={onRowClick ? 0 : -1}
                data-testid={`${testIdPrefix}-${index}`}
              >
                {columns.map((column) => {
                  const value = row[column.key];
                  return (
                    <TableCell
                      key={column.key}
                      align={column.align}
                      sx={{ px: 2, py: 1, fontSize: "0.875rem", color: "text.primary" }}
                    >
                      {renderCell ? renderCell(column.key, value, row) : String(value ?? "—")}
                    </TableCell>
                  );
                })}
                {onRowClick && <TableCell sx={{ px: 2, py: 1 }} />}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
