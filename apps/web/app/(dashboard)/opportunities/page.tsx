"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { Box, TextField, Typography } from "@mui/material";
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

const OpportunityGrid = dynamic(
  () => import("../../../components/opportunities/OpportunityGrid"),
  {
    ssr: false,
    loading: () => <LoadingState label="Loading opportunity grid" />,
  },
);

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

export default function OpportunitiesPage() {
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

  const normalizedSearch = searchText.trim().toLowerCase();
  const filteredRows = normalizedSearch
    ? rows.filter((row) =>
        Object.values(row).some((value) =>
          String(value ?? "").toLowerCase().includes(normalizedSearch),
        ),
      )
    : rows;

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
          {normalizedSearch
            ? `${filteredRows.length} matching opportunit${filteredRows.length === 1 ? "y" : "ies"}`
            : `${rows.length} opportunit${rows.length === 1 ? "y" : "ies"} available`}
        </Typography>
        <TextField
          size="small"
          label="Search opportunities"
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          sx={{ minWidth: 240 }}
        />
      </Box>
      {filteredRows.length === 0 ? (
        <EmptyState
          title="No matching opportunities"
          description="Try a different search term."
        />
      ) : (
        <Card variant="outlined">
          <OpportunityGrid rows={filteredRows} />
        </Card>
      )}
    </PageContainer>
  );
}
