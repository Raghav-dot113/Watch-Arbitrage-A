"use client";

import React from "react";
import {
  Box,
  Button,
  Chip,
  Divider,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingState } from "../../../components/ui/LoadingState";
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

const EVENT_COLOR: Record<string, string> = {
  feedback: "info",
  outcome: "success",
};

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
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {activityItems.map((item) => (
                <Box
                  key={item.id}
                  sx={{
                    p: 2,
                    bgcolor: "background.paper",
                    border: `1px solid`,
                    borderColor: "divider",
                    borderRadius: "md",
                  }}
                >
                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Chip
                        label={EVENT_LABEL[item.event_type] ?? item.event_type}
                        size="small"
                        variant="outlined"
                        color={EVENT_COLOR[item.event_type] as any}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(item.created_at)}
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 0.5, fontSize: "0.875rem" }}>
                    {item.decision
                      ? `Decision: {item.decision} for opportunity {item.opportunity_id ?? "—"}`
                      : `Activity for opportunity {item.opportunity_id ?? "—"}`}
                  </Typography>
                  {item.notes && (
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                      {item.notes}
                    </Typography>
                  )}
                  {item.decision && (
                    <Box sx={{ mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.25 }}>
                        Decision
                      </Typography>
                      <Chip label={item.decision} size="small" variant="outlined" />
                    </Box>
                  )}
                  {(item.acquisition_price || item.resale_price || item.actual_profit) && (
                    <Box sx={{ mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.25 }}>
                        Trade Details
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                        {item.acquisition_price && (
                          <Typography variant="caption" sx={{ mr: 1 }}>
                            Acq: {item.acquisition_price} {item.acquisition_currency ?? ""}
                          </Typography>
                        )}
                        {item.resale_price && (
                          <Typography variant="caption" sx={{ mr: 1 }}>
                            Resale: {item.resale_price} {item.resale_currency ?? ""}
                          </Typography>
                        )}
                        {item.actual_profit && (
                          <Typography variant="caption" sx={{ mr: 1 }}>
                            Profit: {item.actual_profit}
                          </Typography>
                        )}
                        {item.days_to_sell != null && (
                          <Typography variant="caption">
                            Days to sell: {item.days_to_sell}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  )}
                </Box>
              ))}
            </Box>
          )}
        </Box>
        <Divider sx={{ my: 1 }} />
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
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {tradeOutcomes.map((outcome) => (
                <Box
                  key={outcome.id}
                  sx={{
                    p: 2,
                    bgcolor: "background.paper",
                    border: `1px solid`,
                    borderColor: "divider",
                    borderRadius: "md",
                  }}
                >
                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(outcome.created_at)}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 0.5, fontSize: "0.875rem" }}>
                    Opportunity {outcome.opportunity_id ?? "—"}
                  </Typography>
                  <Box sx={{ mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 0.25 }}>
                      Trade Details
                    </Typography>
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                      {outcome.acquisition_price && (
                        <Typography variant="caption" sx={{ mr: 1 }}>
                          Acq: {outcome.acquisition_price} {outcome.acquisition_currency ?? ""}
                        </Typography>
                      )}
                      {outcome.resale_price && (
                        <Typography variant="caption" sx={{ mr: 1 }}>
                          Resale: {outcome.resale_price} {outcome.resale_currency ?? ""}
                        </Typography>
                      )}
                      {outcome.actual_profit && (
                        <Typography variant="caption" sx={{ mr: 1 }}>
                          Profit: {outcome.actual_profit}
                        </Typography>
                      )}
                      {outcome.days_to_sell != null && (
                        <Typography variant="caption">
                          Days to sell: {outcome.days_to_sell}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      </Box>
    </PageContainer>
  );
}
