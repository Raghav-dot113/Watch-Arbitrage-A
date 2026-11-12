"use client";

import { Box, Typography } from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingState } from "../../../components/ui/LoadingState";
import {
  ChronoArbGrid,
  type ChronoArbGridColumn,
} from "../../../components/bryntum/ChronoArbGrid";
import {
  useActivity,
  useTradeOutcomes,
  type ActivityItem,
  type TradeOutcome,
} from "../../../lib/hooks/useActivity";
import { formatDate } from "../../../lib/formatters";

const EVENT_LABEL: Record<string, string> = {
  feedback: "Feedback",
  outcome: "Trade Outcome",
};

function tradeDetails(
  acquisition: string | null,
  acquisitionCurrency: string | null,
  resale: string | null,
  resaleCurrency: string | null,
  profit: string | null,
  daysToSell: number | null,
): string {
  const parts: string[] = [];
  if (acquisition) parts.push(`Acq ${acquisition} ${acquisitionCurrency ?? ""}`.trim());
  if (resale) parts.push(`Resale ${resale} ${resaleCurrency ?? ""}`.trim());
  if (profit) parts.push(`Profit ${profit}`);
  if (daysToSell != null) parts.push(`${daysToSell} days`);
  return parts.join(" • ") || "—";
}

const ACTIVITY_COLUMNS: ChronoArbGridColumn<ActivityItem>[] = [
  {
    field: "created_at",
    text: "When",
    width: 170,
    render: (item) => formatDate(item.created_at),
  },
  {
    field: "event_type",
    text: "Event",
    width: 130,
    render: (item) => EVENT_LABEL[item.event_type] ?? item.event_type,
  },
  {
    field: "decision",
    text: "Decision",
    width: 130,
    render: (item) => item.decision ?? "—",
  },
  {
    field: "opportunity_id",
    text: "Opportunity",
    width: 170,
    render: (item) => item.opportunity_id ?? "—",
  },
  {
    field: "reference_id",
    text: "Reference",
    width: 150,
    render: (item) => item.reference_id ?? "—",
  },
  {
    field: "notes",
    text: "Notes",
    flex: 1,
    render: (item) => item.notes ?? "—",
  },
  {
    field: "trade_details",
    text: "Trade details",
    width: 290,
    render: (item) =>
      tradeDetails(
        item.acquisition_price,
        item.acquisition_currency,
        item.resale_price,
        item.resale_currency,
        item.actual_profit,
        item.days_to_sell,
      ),
  },
];

const OUTCOME_COLUMNS: ChronoArbGridColumn<TradeOutcome>[] = [
  {
    field: "created_at",
    text: "Recorded",
    width: 170,
    render: (outcome) => formatDate(outcome.created_at),
  },
  {
    field: "opportunity_id",
    text: "Opportunity",
    width: 170,
    render: (outcome) => outcome.opportunity_id ?? "—",
  },
  {
    field: "reference_id",
    text: "Reference",
    width: 150,
    render: (outcome) => outcome.reference_id,
  },
  {
    field: "acquisition_price",
    text: "Acquisition",
    width: 170,
    render: (outcome) =>
      outcome.acquisition_price
        ? `${outcome.acquisition_price} ${outcome.acquisition_currency ?? ""}`.trim()
        : "—",
  },
  {
    field: "resale_price",
    text: "Resale",
    width: 170,
    render: (outcome) =>
      outcome.resale_price
        ? `${outcome.resale_price} ${outcome.resale_currency ?? ""}`.trim()
        : "—",
  },
  {
    field: "actual_profit",
    text: "Actual profit",
    width: 160,
    render: (outcome) =>
      outcome.actual_profit
        ? `${outcome.actual_profit} ${outcome.actual_profit_currency ?? ""}`.trim()
        : "—",
  },
  {
    field: "days_to_sell",
    text: "Days to sell",
    width: 120,
    render: (outcome) => (outcome.days_to_sell == null ? "—" : String(outcome.days_to_sell)),
  },
];

export default function ActivityPage() {
  const { data, isLoading, isError, error } = useActivity();
  const { data: outcomes, isLoading: outcomesLoading } = useTradeOutcomes();

  const activityItems: ActivityItem[] = data ?? [];
  const tradeOutcomes: TradeOutcome[] = outcomes ?? [];

  if (isLoading || outcomesLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading activity" fullPage />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Unable to load activity"
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
      <PageHeader
        title="Activity"
        description="Review your past actions and system events."
      />
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            Activity Feed
          </Typography>
          {activityItems.length === 0 ? (
            <EmptyState
              title="No activity"
              description="Your activity will appear here when you record feedback or trade outcomes."
            />
          ) : (
            <ChronoArbGrid
              ariaLabel="Activity feed"
              rows={activityItems}
              columns={ACTIVITY_COLUMNS}
              height={420}
            />
          )}
        </Box>
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            Trade Outcomes
          </Typography>
          {tradeOutcomes.length === 0 ? (
            <EmptyState
              title="No trade outcomes"
              description="Trade outcomes will appear here when you record a sale outcome for a purchased opportunity."
            />
          ) : (
            <ChronoArbGrid
              ariaLabel="Trade outcomes"
              rows={tradeOutcomes}
              columns={OUTCOME_COLUMNS}
              height={360}
            />
          )}
        </Box>
      </Box>
    </PageContainer>
  );
}
