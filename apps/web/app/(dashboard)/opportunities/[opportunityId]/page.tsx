"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { use } from "react";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../../components/shell/PageHeader";
import { PageContainer } from "../../../../components/ui/PageContainer";
import { Card } from "../../../../components/ui/Card";
import { LoadingState } from "../../../../components/ui/LoadingState";
import { ErrorState } from "../../../../components/ui/ErrorState";
import {
  useOpportunity,
  useRecordFeedback,
  useRecordTradeOutcome,
  type Opportunity,
} from "../../../../lib/hooks/useOpportunities";
import {
  formatCurrency,
  formatPercent,
  formatDate,
  formatRelativeTime,
} from "../../../../lib/formatters";

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

export default function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ opportunityId: string }>;
}) {
  const router = useRouter();
  const { opportunityId } = use(params);
  const { data, isLoading, isError, error } = useOpportunity(opportunityId);
  const recordFeedback = useRecordFeedback(opportunityId);
  const recordOutcome = useRecordTradeOutcome(opportunityId);
  const [outcomeDialogOpen, setOutcomeDialogOpen] = React.useState(false);
  const [outcomeForm, setOutcomeForm] = React.useState<{
    acquisition_price: string;
    acquisition_currency: string;
    resale_price: string;
    resale_currency: string;
    actual_profit: string;
    days_to_sell: string;
  }>({
    acquisition_price: "",
    acquisition_currency: "USD",
    resale_price: "",
    resale_currency: "USD",
    actual_profit: "",
    days_to_sell: "",
  });

  const handleFeedback = async (decision: string) => {
    if (recordFeedback.isPending) return;
    await recordFeedback.mutateAsync({ decision });
    if (decision === "purchased") {
      setOutcomeDialogOpen(true);
    }
  };

  const handleOutcomeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (recordOutcome.isPending) return;
    await recordOutcome.mutateAsync({
      acquisition_price: outcomeForm.acquisition_price || undefined,
      acquisition_currency: outcomeForm.acquisition_currency || undefined,
      resale_price: outcomeForm.resale_price || undefined,
      resale_currency: outcomeForm.resale_currency || undefined,
      actual_profit: outcomeForm.actual_profit || undefined,
      days_to_sell:
        outcomeForm.days_to_sell !== ""
          ? Number(outcomeForm.days_to_sell)
          : undefined,
    });
    setOutcomeDialogOpen(false);
  };

  if (isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading opportunity" fullPage />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Unable to load opportunity"
          description={
            error instanceof Error ? error.message : "An unexpected error occurred."
          }
          retryLabel="Try again"
          onRetry={() => router.push(`/opportunities/${opportunityId}`)}
        />
      </PageContainer>
    );
  }

  if (!data) {
    return (
      <PageContainer>
        <ErrorState
          title="Opportunity not found"
          description={`Opportunity ${opportunityId} does not exist.`}
          retryLabel="Back to feed"
          onRetry={() => router.push("/opportunities")}
        />
      </PageContainer>
    );
  }

  const valuation = data.valuation;

  return (
    <PageContainer>
      <PageHeader
        title="Opportunity detail"
        description={`Review the full deal analysis for ${data.id}.`}
        actions={
          <Link href="/opportunities">
            <Button variant="outlined">Back to feed</Button>
          </Link>
        }
      />
      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Opportunity {data.id}
        </Typography>
      </Box>
      <Card variant="outlined" sx={{ mb: 3 }}>
        <Box sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Box>
              <Typography
                variant="h6"
                component="h2"
                sx={{ fontWeight: 600, mb: 0.5, color: "text.primary" }}
              >
                Deal analysis
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Material version {data.material_version} • State:{" "}
                <Chip
                  label={STATE_LABEL[data.state] ?? data.state}
                  size="small"
                  color={STATE_CHIP_COLOR[data.state] as any}
                  variant="outlined"
                />
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 1 }}>
              <Chip
                label={data.score == null ? "—" : String(data.score)}
                size="small"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
              <Chip
                label={formatRelativeTime(data.created_at)}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        </Box>
      </Card>
      <Card variant="outlined" sx={{ mb: 3 }}>
        <Box sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography
            variant="h6"
            component="h2"
            sx={{ fontWeight: 600, mb: 0, color: "text.primary" }}
          >
            Decision
          </Typography>
          {data.my_decision && (
            <Typography variant="body2" color="text.secondary">
              Your decision: {data.my_decision}
            </Typography>
          )}
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Button
              variant="outlined"
              onClick={() => handleFeedback("contacted")}
              disabled={recordFeedback.isPending || data.my_decision === "contacted"}
            >
              Contacted
            </Button>
            <Button
              variant="outlined"
              onClick={() => handleFeedback("dismissed")}
              disabled={recordFeedback.isPending || data.my_decision === "dismissed"}
            >
              Dismissed
            </Button>
            <Button
              variant="contained"
              onClick={() => handleFeedback("purchased")}
              disabled={
                recordFeedback.isPending ||
                data.my_decision === "purchased" ||
                recordOutcome.isPending
              }
            >
              Purchased
            </Button>
          </Box>
          {data.my_decision === "purchased" && (
            <Button
              variant="outlined"
              onClick={() => setOutcomeDialogOpen(true)}
              disabled={recordOutcome.isPending}
            >
              Record trade outcome
            </Button>
          )}
        </Box>
      </Card>
      {valuation && (
        <Card variant="outlined" sx={{ mb: 3 }}>
          <Box sx={{ p: 3 }}>
            <Typography
              variant="h6"
              component="h2"
              sx={{ fontWeight: 600, mb: 2, color: "text.primary" }}
            >
              Cost waterfall
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow
                    sx={{
                      "& th": {
                        bgcolor: "action.disabledBackground",
                        color: "text.secondary",
                        fontWeight: 500,
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.8125rem",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      Metric
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.8125rem",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        align: "right",
                      }}
                    >
                      Value
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      All-in acquisition
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {formatCurrency(
                        valuation.all_in_acquisition,
                        valuation.exit_price_currency ?? "USD"
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Expected exit price
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {formatCurrency(
                        valuation.expected_exit_price,
                        valuation.exit_price_currency ?? "USD"
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Expected net resale
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {formatCurrency(
                        valuation.expected_net_resale,
                        valuation.exit_price_currency ?? "USD"
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Expected net profit
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {formatCurrency(
                        valuation.expected_net_profit,
                        valuation.exit_price_currency ?? "USD"
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      ROI
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {formatPercent(valuation.roi ?? null)}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Confidence
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {formatPercent(valuation.confidence ?? null)}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Comparable count
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                        align: "right",
                      }}
                    >
                      {valuation.comparable_count == null
                        ? "—"
                        : String(valuation.comparable_count)}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Model version
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.secondary",
                        align: "right",
                      }}
                    >
                      {valuation.model_version}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Cost assumptions version
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.secondary",
                        align: "right",
                      }}
                    >
                      {valuation.cost_assumptions_version}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    sx={{
                      "& td": {
                        borderBottom: `1px solid`,
                        borderColor: "divider",
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.primary",
                      }}
                    >
                      Valuation created
                    </TableCell>
                    <TableCell
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: "0.875rem",
                        color: "text.secondary",
                        align: "right",
                      }}
                    >
                      {formatDate(valuation.created_at)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </Card>
      )}
      <Dialog
        open={outcomeDialogOpen}
        onClose={() => setOutcomeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Record Trade Outcome</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleOutcomeSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              required
              label="Acquisition price"
              type="text"
              inputMode="decimal"
              value={outcomeForm.acquisition_price}
              onChange={(e) => setOutcomeForm({ ...outcomeForm, acquisition_price: e.target.value })}
              helperText="What you paid to acquire the item"
            />
            <TextField
              required
              label="Acquisition currency"
              value={outcomeForm.acquisition_currency}
              onChange={(e) => setOutcomeForm({ ...outcomeForm, acquisition_currency: e.target.value })}
              slotProps={{ htmlInput: { maxLength: 3 } }}
              helperText="ISO currency code (e.g. USD)"
            />
            <TextField
              label="Resale price"
              type="text"
              inputMode="decimal"
              value={outcomeForm.resale_price}
              onChange={(e) => setOutcomeForm({ ...outcomeForm, resale_price: e.target.value })}
              helperText="What you sold the item for"
            />
            <TextField
              label="Resale currency"
              value={outcomeForm.resale_currency}
              onChange={(e) => setOutcomeForm({ ...outcomeForm, resale_currency: e.target.value })}
              slotProps={{ htmlInput: { maxLength: 3 } }}
              helperText="ISO currency code (e.g. USD)"
            />
            <TextField
              label="Actual profit"
              type="text"
              inputMode="decimal"
              value={outcomeForm.actual_profit}
              onChange={(e) => setOutcomeForm({ ...outcomeForm, actual_profit: e.target.value })}
              helperText="Dealer-reported profit in acquisition currency"
            />
            <TextField
              label="Days to sell"
              type="text"
              inputMode="numeric"
              value={outcomeForm.days_to_sell}
              onChange={(e) => setOutcomeForm({ ...outcomeForm, days_to_sell: e.target.value })}
              helperText="Days between acquisition and resale"
            />
            <Divider sx={{ my: 1 }} />
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1 }}>
              <Button type="button" onClick={() => setOutcomeDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={recordOutcome.isPending}
              >
                Record outcome
              </Button>
            </Box>
          </Box>
          </form>
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
