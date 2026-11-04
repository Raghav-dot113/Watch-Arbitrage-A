"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Box,
  Button,
  Chip,
  Typography,
  Paper,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { DataTable } from "../../../components/ui/DataTable";
import { LoadingState } from "../../../components/ui/LoadingState";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Card } from "../../../components/ui/Card";
import {
  useOpportunities,
  type Opportunity,
} from "../../../lib/hooks/useOpportunities";
import {
  formatCurrency,
  formatDate,
  formatRelativeTime,
} from "../../../lib/formatters";

const STATE_CHIP_COLOR: Record<string, string> = {
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

interface OpportunityRow {
  id: string;
  state: string;
  score: string | null;
  created_at: string;
  expected_net_profit: string | null;
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
    roi: opportunity.valuation?.roi ?? null,
  };
}

export default function OpportunitiesPage() {
  const router = useRouter();
  const { data, isLoading, isError, error } = useOpportunities();

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

  const columns = [
    { key: "id", label: "ID" },
    { key: "state", label: "State", align: "center" as const },
    { key: "score", label: "Score", align: "right" as const },
    { key: "expected_net_profit", label: "Expected profit", align: "right" as const },
    { key: "roi", label: "ROI", align: "right" as const },
    { key: "created_at", label: "Published", align: "left" as const },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Opportunities"
        description="View and evaluate current watch arbitrage opportunities."
        actions={
          <Button variant="outlined" startIcon={<></>} disabled>
            Refresh
          </Button>
        }
      />
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {rows.length} opportunity{rows.length !== 1 ? "s" : ""} available
        </Typography>
      </Box>
      <Card variant="outlined">
        <DataTable
          title="Opportunity feed"
          columns={columns}
          data={rows as unknown as Record<string, unknown>[]}
          renderCell={(key, value, row) => {
            const typedRow = row as unknown as OpportunityRow;
            if (key === "state") {
              const color = STATE_CHIP_COLOR[typedRow.state] ?? "default";
              return (
                <Chip
                  label={STATE_LABEL[typedRow.state] ?? typedRow.state}
                  size="small"
                  color={color as any}
                  variant="outlined"
                />
              );
            }
            if (key === "score") {
              return value == null ? "—" : String(value);
            }
            if (key === "expected_net_profit") {
              return formatCurrency(value as string | null, "USD");
            }
            if (key === "roi") {
              return value == null ? "—" : `${String(value)}%`;
            }
            if (key === "created_at") {
              return formatRelativeTime(value as string | null);
            }
            return String(value ?? "—");
          }}
          onRowClick={(row) => {
            router.push(`/opportunities/${row.id}`);
          }}
          testIdPrefix="opportunity-row"
        />
      </Card>
    </PageContainer>
  );
}
