"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import type { Model } from "@bryntum/core-business";
import type { GridColumnConfig } from "@bryntum/grid-business";
import { BryntumGrid } from "@bryntum/grid-react-business";
import { formatCurrency, formatRelativeTime } from "../../lib/formatters";

export interface OpportunityGridRow {
  id: string;
  state: string;
  score: string | null;
  created_at: string;
  expected_net_profit: string | null;
  currency: string;
  roi: string | null;
}

interface OpportunityGridProps {
  rows: OpportunityGridRow[];
}

const STATE_LABEL: Record<string, string> = {
  published: "Published",
  dismissed: "Dismissed",
  contacted: "Contacted",
  purchased: "Purchased",
  expired: "Expired",
};

const licenseKey = process.env.NEXT_PUBLIC_BRYNTUM_LICENSE_KEY;
if (licenseKey) {
  const bryntumGlobal = globalThis as typeof globalThis & {
    bryntum?: { licenseKey?: string };
  };
  bryntumGlobal.bryntum ??= {};
  bryntumGlobal.bryntum.licenseKey = licenseKey;
}

export function compareDecimalStrings(
  left: string | null | undefined,
  right: string | null | undefined,
): number {
  if (left == null || right == null) {
    return left == null ? (right == null ? 0 : -1) : 1;
  }
  const leftParts = /^(-?)(\d+)(?:\.(\d+))?$/.exec(left);
  const rightParts = /^(-?)(\d+)(?:\.(\d+))?$/.exec(right);
  if (!leftParts || !rightParts) {
    return left.localeCompare(right);
  }
  const scale = Math.max(leftParts[3]?.length ?? 0, rightParts[3]?.length ?? 0);
  if (scale > 18) {
    return left.localeCompare(right);
  }
  const leftMagnitude = BigInt(
    `${leftParts[1]}${leftParts[2]}${(leftParts[3] ?? "").padEnd(scale, "0")}`,
  );
  const rightMagnitude = BigInt(
    `${rightParts[1]}${rightParts[2]}${(rightParts[3] ?? "").padEnd(scale, "0")}`,
  );
  return leftMagnitude < rightMagnitude ? -1 : leftMagnitude > rightMagnitude ? 1 : 0;
}

function compareRecordDecimals(
  field: "score" | "expected_net_profit" | "roi",
  left: Model,
  right: Model,
): number {
  return compareDecimalStrings(left.get(field), right.get(field));
}

function compareRecordProfit(left: Model, right: Model): number {
  const currencyOrder = String(left.get("currency") ?? "").localeCompare(
    String(right.get("currency") ?? ""),
  );
  return currencyOrder || compareRecordDecimals("expected_net_profit", left, right);
}

export default function OpportunityGrid({ rows }: OpportunityGridProps) {
  const router = useRouter();
  const store = useMemo(() => ({ pageSize: 20 }), []);
  const columns = useMemo<GridColumnConfig[]>(
    () => [
      {
        field: "id",
        text: "ID",
        minWidth: 170,
        renderer: ({ record }: { record: Model }) => ({
          tag: "a",
          href: `/opportunities/${encodeURIComponent(String(record.get("id")))}`,
          text: String(record.get("id")),
        }),
      },
      {
        field: "state",
        text: "State",
        minWidth: 130,
        renderer: ({ value }: { value: unknown }) =>
          STATE_LABEL[String(value)] ?? String(value ?? "—"),
      },
      {
        field: "score",
        text: "Score",
        minWidth: 110,
        sortable: (left, right) => compareRecordDecimals("score", left, right),
        renderer: ({ value }: { value: unknown }) => String(value ?? "—"),
      },
      {
        field: "expected_net_profit",
        text: "Expected profit",
        minWidth: 170,
        sortable: compareRecordProfit,
        renderer: ({
          record,
          value,
        }: {
          record: Model;
          value: unknown;
        }) =>
          formatCurrency(value == null ? null : String(value), String(record.get("currency") ?? "USD")),
      },
      {
        field: "roi",
        text: "ROI",
        minWidth: 110,
        sortable: (left, right) => compareRecordDecimals("roi", left, right),
        renderer: ({ value }: { value: unknown }) =>
          (value == null ? "—" : `${value}%`),
      },
      {
        field: "created_at",
        text: "Published",
        minWidth: 170,
        renderer: ({ value }: { value: unknown }) =>
          formatRelativeTime(value == null ? null : String(value)),
      },
    ],
    [],
  );

  return (
    <div role="region" aria-label="Opportunity feed">
      <BryntumGrid
        ariaLabel="Opportunity feed"
        cls="chronoarb-opportunity-grid"
        height={520}
        data={rows}
        store={store}
        columns={columns}
        bbar={{ type: "pagingtoolbar" }}
        sortFeature
        filterFeature
        filterBarFeature
        groupFeature
        columnPickerFeature
        columnReorderFeature
        columnResizeFeature
        cellTooltipFeature
        cellEditFeature={false}
        cellCopyPasteFeature={false}
        rowCopyPasteFeature={false}
        onCellClick={({ event, record, target }) => {
          if (target.closest("a")) event.preventDefault();
          const opportunityId = record.get("id");
          if (typeof opportunityId === "string") {
            router.push(`/opportunities/${encodeURIComponent(opportunityId)}`);
          }
        }}
      />
    </div>
  );
}
