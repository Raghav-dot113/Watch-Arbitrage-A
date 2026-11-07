"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  AllCommunityModule,
  colorSchemeDark,
  ModuleRegistry,
  themeQuartz,
  type ColDef,
  type ICellRendererParams,
  type ValueFormatterParams,
} from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { Box, Chip, TextField, Typography } from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { LoadingState } from "../../../components/ui/LoadingState";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Card } from "../../../components/ui/Card";
import {
  useOpportunities,
  type Opportunity,
} from "../../../lib/hooks/useOpportunities";
import { formatCurrency, formatRelativeTime } from "../../../lib/formatters";

ModuleRegistry.registerModules([AllCommunityModule]);

const STATE_CHIP_COLOR: Record<
  string,
  "default" | "success" | "info" | "primary" | "error"
> = {
  published: "success",
  dismissed: "default",
  contacted: "info",
  purchased: "primary",
  expired: "error",
};

const STATE_LABEL: Record<string, string> = {
  published: "Published",
  dismissed: "Dismissed",
  contacted: "Contacted",
  purchased: "Purchased",
  expired: "Expired",
};

const opportunityGridTheme = themeQuartz.withPart(colorSchemeDark);

interface OpportunityRow {
  id: string;
  state: string;
  score: string | null;
  created_at: string;
  expected_net_profit: string | null;
  currency: string;
  roi: string | null;
}

function toRow(opportunity: Opportunity): OpportunityRow {
  return {
    id: opportunity.id,
    state: opportunity.state,
    score: opportunity.score,
    created_at: opportunity.created_at,
    expected_net_profit:
      opportunity.valuation?.expected_net_profit ?? null,
    currency: opportunity.valuation?.exit_price_currency ?? "USD",
    roi: opportunity.valuation?.roi ?? null,
  };
}

function compareDecimalStrings(
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

export default function OpportunitiesPage() {
  const router = useRouter();
  const { data, isLoading, isError, error } = useOpportunities();
  const [searchText, setSearchText] = useState("");

  if (isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading opportunities" fullPage />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Unable to load opportunities"
          description={
            error instanceof Error ? error.message : "An unexpected error occurred."
          }
          retryLabel="Try again"
          onRetry={() => window.location.reload()}
        />
      </PageContainer>
    );
  }

  const rows: OpportunityRow[] = (data?.data ?? []).map(toRow);

  if (rows.length === 0) {
    return (
      <PageContainer>
        <PageHeader
          title="Opportunities"
          description="View and evaluate current watch arbitrage opportunities."
        />
        <EmptyState
          title="No opportunities"
          description="There are no opportunities available right now."
        />
      </PageContainer>
    );
  }

  const columns: ColDef<OpportunityRow>[] = [
    {
      field: "id",
      headerName: "ID",
      minWidth: 170,
      cellRenderer: ({ value, data }: ICellRendererParams<OpportunityRow, string>) => (
        <Link href={`/opportunities/${data?.id}`} onClick={(event) => event.stopPropagation()}>
          {value}
        </Link>
      ),
    },
    {
      field: "state",
      headerName: "State",
      minWidth: 130,
      cellRenderer: ({ value }: ICellRendererParams<OpportunityRow, string>) => {
        const state = value ?? "";
        return (
        <Chip
          label={STATE_LABEL[state] ?? state}
          size="small"
          color={STATE_CHIP_COLOR[state] ?? "default"}
          variant="outlined"
        />
        );
      },
    },
    {
      field: "score",
      headerName: "Score",
      minWidth: 110,
      comparator: compareDecimalStrings,
      valueFormatter: ({ value }: ValueFormatterParams<OpportunityRow, string | null>) =>
        value ?? "—",
    },
    {
      field: "expected_net_profit",
      headerName: "Expected profit",
      minWidth: 170,
      comparator: (left, right, leftNode, rightNode) => {
        const currencyOrder = (leftNode.data?.currency ?? "").localeCompare(
          rightNode.data?.currency ?? "",
        );
        return currencyOrder || compareDecimalStrings(left, right);
      },
      valueFormatter: ({
        value,
        data,
      }: ValueFormatterParams<OpportunityRow, string | null>) =>
        formatCurrency(value ?? null, data?.currency ?? "USD"),
    },
    {
      field: "roi",
      headerName: "ROI",
      minWidth: 110,
      comparator: compareDecimalStrings,
      valueFormatter: ({ value }: ValueFormatterParams<OpportunityRow, string | null>) =>
        value == null ? "—" : `${value}%`,
    },
    {
      field: "created_at",
      headerName: "Published",
      minWidth: 170,
      valueFormatter: ({ value }: ValueFormatterParams<OpportunityRow, string>) =>
        formatRelativeTime(value ?? null),
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Opportunities"
        description="View and evaluate current watch arbitrage opportunities."
      />
      <Box
        sx={{
          mb: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {rows.length} opportunity{rows.length !== 1 ? "s" : ""} available
        </Typography>
        <TextField
          size="small"
          label="Search opportunities"
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          sx={{ minWidth: 240 }}
        />
      </Box>
      <Card variant="outlined">
        <Box role="region" aria-label="Opportunity feed">
          <AgGridReact<OpportunityRow>
            aria-label="Opportunity feed"
            className="chronoarb-opportunity-grid"
            theme={opportunityGridTheme}
            rowData={rows}
            columnDefs={columns}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
              minWidth: 100,
            }}
            getRowId={({ data }) => data.id}
            quickFilterText={searchText}
            pagination
            paginationPageSize={20}
            paginationPageSizeSelector={[10, 20, 50]}
            domLayout="autoHeight"
            onRowClicked={({ data }) => {
              if (data) {
                router.push(`/opportunities/${data.id}`);
              }
            }}
          />
        </Box>
      </Card>
    </PageContainer>
  );
}
