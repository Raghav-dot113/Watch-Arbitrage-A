export interface MockGridColumn<Row> {
  field: string;
  text?: string;
  render?: (row: Row) => string;
}

export interface MockGridAction<Row> {
  key: string;
  label: string | ((row: Row) => string);
  onClick: (row: Row) => void;
}

export interface MockChronoArbGridProps<Row extends { id: string }> {
  ariaLabel: string;
  rows: Row[];
  columns: MockGridColumn<Row>[];
  actions?: MockGridAction<Row>[];
}

/**
 * Lightweight stand-in for the Bryntum-backed grid in jsdom tests. It mirrors the
 * rows, rendered cell text, and action buttons the real wrapper produces.
 */
export function MockChronoArbGrid<Row extends { id: string }>({
  ariaLabel,
  rows,
  columns,
  actions = [],
}: MockChronoArbGridProps<Row>) {
  return (
    <div role="grid" aria-label={ariaLabel}>
      {rows.map((row) => (
        <div role="row" key={row.id}>
          {columns.map((column) => (
            <span key={column.field}>
              {column.render
                ? column.render(row)
                : String((row as Record<string, unknown>)[column.field] ?? "")}
            </span>
          ))}
          {actions.map((action) => (
            <button
              key={action.key}
              type="button"
              onClick={() => action.onClick(row)}
            >
              {typeof action.label === "function" ? action.label(row) : action.label}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}
