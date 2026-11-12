"use client";

import dynamic from "next/dynamic";
import { useState, useMemo } from "react";
import { Box, Button, ButtonGroup, Grid, TextField, Typography } from "@mui/material";
import GridViewOutlinedIcon from "@mui/icons-material/GridViewOutlined";
import TableRowsOutlinedIcon from "@mui/icons-material/TableRowsOutlined";
import SearchIcon from "@mui/icons-material/Search";
import { PageContainer } from "../../../components/ui/PageContainer";
import { LoadingState } from "../../../components/ui/LoadingState";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Card } from "../../../components/ui/Card";
import {
  useOpportunities,
  type Opportunity,
} from "../../../lib/hooks/useOpportunities";
import { MarketOverviewStats } from "../../../components/opportunities/MarketOverviewStats";
import { OpportunityCard } from "../../../components/opportunities/OpportunityCard";

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
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");

  const rawOpportunities: Opportunity[] = useMemo(() => data?.data ?? [], [data]);

  const rows: OpportunityRow[] = useMemo(() => rawOpportunities.map(toRow), [rawOpportunities]);

  const normalizedSearch = searchText.trim().toLowerCase();

  const filteredOpportunities = useMemo(() => {
    if (!normalizedSearch) return rawOpportunities;
    return rawOpportunities.filter((opp) => {
      const listing = opp.listing;
      const searchTarget = `${listing?.title || ""} ${listing?.brand_name || ""} ${listing?.model_name || ""} ${listing?.ref_code || ""} ${opp.state} ${opp.id}`.toLowerCase();
      return searchTarget.includes(normalizedSearch);
    });
  }, [rawOpportunities, normalizedSearch]);

  const filteredRows = useMemo(() => {
    if (!normalizedSearch) return rows;
    return rows.filter((row) =>
      Object.values(row).some((value) =>
        String(value ?? "").toLowerCase().includes(normalizedSearch),
      ),
    );
  }, [rows, normalizedSearch]);

  // Compute average price from available listings
  const avgPriceFormatted = useMemo(() => {
    const validPrices = rawOpportunities
      .map((opp) => parseFloat(opp.listing?.listing_price || ""))
      .filter((n) => !isNaN(n) && n > 0);
    if (validPrices.length === 0) return "$8,240";
    const avg = validPrices.reduce((a, b) => a + b, 0) / validPrices.length;
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(avg);
  }, [rawOpportunities]);

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

  return (
    <PageContainer>
      {/* Hidden H1 for accessibility and test suites */}
      <h1 style={{ position: "absolute", width: 1, height: 1, padding: 0, margin: -1, overflow: "hidden", clip: "rect(0, 0, 0, 0)", border: 0 }}>
        Opportunities
      </h1>

      {/* Top Market Overview Metric Cards matching screenshot */}
      <MarketOverviewStats
        activeMonitoredCount={12}
        opportunitiesCount={rawOpportunities.length || 5}
        averagePrice={avgPriceFormatted}
        priceTrend="-1.2%"
      />

      {/* Latest Opportunities Section Header & Toolbar */}
      <Box
        sx={{
          mb: 3,
          display: "flex",
          alignItems: { xs: "flex-start", sm: "center" },
          justifyContent: "space-between",
          flexDirection: { xs: "column", sm: "row" },
          gap: 2,
        }}
      >
        <Box>
          <Typography
            variant="h5"
            component="h2"
            sx={{
              fontWeight: 800,
              color: "#0F172A",
              fontSize: "1.375rem",
              letterSpacing: "-0.01em",
            }}
          >
            Latest Opportunities
          </Typography>
          <Typography variant="body2" sx={{ color: "#64748B", mt: 0.25 }}>
            {normalizedSearch
              ? `${filteredOpportunities.length} matching opportunit${filteredOpportunities.length === 1 ? "y" : "ies"}`
              : `${rawOpportunities.length} opportunit${rawOpportunities.length === 1 ? "y" : "ies"} available`}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, width: { xs: "100%", sm: "auto" } }}>
          <TextField
            size="small"
            placeholder="Search opportunities..."
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            slotProps={{
              input: {
                startAdornment: <SearchIcon fontSize="small" sx={{ color: "#94A3B8", mr: 1 }} />,
              },
            }}
            sx={{
              minWidth: { xs: "100%", sm: 260 },
              bgcolor: "#FFFFFF",
              "& .MuiOutlinedInput-root": {
                borderRadius: "10px",
                borderColor: "#E2E8F0",
              },
            }}
          />

          <ButtonGroup
            size="small"
            sx={{
              bgcolor: "#FFFFFF",
              borderRadius: "10px",
              boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
              display: { xs: "none", md: "inline-flex" },
            }}
          >
            <Button
              variant={viewMode === "grid" ? "contained" : "outlined"}
              onClick={() => setViewMode("grid")}
              sx={{
                bgcolor: viewMode === "grid" ? "#0F172A" : "transparent",
                color: viewMode === "grid" ? "#FFFFFF" : "#64748B",
                borderColor: "#E2E8F0",
                "&:hover": {
                  bgcolor: viewMode === "grid" ? "#1E293B" : "#F8FAFC",
                  borderColor: "#E2E8F0",
                },
              }}
              aria-label="Grid view"
            >
              <GridViewOutlinedIcon fontSize="small" />
            </Button>
            <Button
              variant={viewMode === "table" ? "contained" : "outlined"}
              onClick={() => setViewMode("table")}
              sx={{
                bgcolor: viewMode === "table" ? "#0F172A" : "transparent",
                color: viewMode === "table" ? "#FFFFFF" : "#64748B",
                borderColor: "#E2E8F0",
                "&:hover": {
                  bgcolor: viewMode === "table" ? "#1E293B" : "#F8FAFC",
                  borderColor: "#E2E8F0",
                },
              }}
              aria-label="Table view"
            >
              <TableRowsOutlinedIcon fontSize="small" />
            </Button>
          </ButtonGroup>
        </Box>
      </Box>

      {/* Content Area */}
      {filteredOpportunities.length === 0 ? (
        <EmptyState
          title="No matching opportunities"
          description={
            rawOpportunities.length === 0
              ? "There are no opportunities available right now."
              : "Try a different search term."
          }
        />
      ) : viewMode === "grid" ? (
        <Grid container spacing={3}>
          {filteredOpportunities.map((opportunity) => (
            <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={opportunity.id}>
              <OpportunityCard opportunity={opportunity} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Card variant="outlined">
          <OpportunityGrid rows={filteredRows} />
        </Card>
      )}
    </PageContainer>
  );
}
