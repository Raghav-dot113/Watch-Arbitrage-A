"use client";

import React from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingState } from "../../../components/ui/LoadingState";
import {
  ChronoArbGrid,
  type ChronoArbGridAction,
  type ChronoArbGridColumn,
} from "../../../components/bryntum/ChronoArbGrid";
import {
  useAlertRules,
  useCreateAlertRule,
  useUpdateAlertRule,
  useDeleteAlertRule,
  useRequestAlertTest,
  useAlertDeliveries,
  type AlertChannel,
  type AlertRuleResponse,
  type AlertDeliveryResponse,
} from "../../../lib/hooks/useAlerts";
import { formatDate } from "../../../lib/formatters";

const CHANNEL_LABEL: Record<string, string> = {
  in_app: "In-app",
  push: "Push",
  telegram: "Telegram",
};

function filterSummary(rule: AlertRuleResponse): string {
  const parts: string[] = [];
  const references = rule.filters.reference_ids ?? [];
  if (references.length > 0) {
    parts.push(`${references.length} ref${references.length === 1 ? "" : "s"}`);
  }
  if (rule.filters.min_profit) parts.push(`min profit ${rule.filters.min_profit}`);
  if (rule.filters.max_acquisition) {
    parts.push(`max acquisition ${rule.filters.max_acquisition}`);
  }
  const conditions = rule.filters.conditions ?? [];
  if (conditions.length > 0) parts.push(conditions.join(", "));
  return parts.join(" • ") || "Any opportunity";
}

const RULE_COLUMNS: ChronoArbGridColumn<AlertRuleResponse>[] = [
  { field: "name", text: "Rule", flex: 1, render: (rule) => rule.name },
  {
    field: "channels",
    text: "Channels",
    width: 170,
    render: (rule) => rule.channels.map((channel) => CHANNEL_LABEL[channel] ?? channel).join(", "),
  },
  { field: "filters", text: "Filters", width: 280, render: filterSummary },
  {
    field: "cooldown_minutes",
    text: "Cooldown",
    width: 110,
    render: (rule) => `${rule.cooldown_minutes} min`,
  },
  {
    field: "is_enabled",
    text: "Status",
    width: 100,
    render: (rule) => (rule.is_enabled ? "Enabled" : "Disabled"),
  },
  {
    field: "created_at",
    text: "Created",
    width: 170,
    render: (rule) => formatDate(rule.created_at),
  },
];

const DELIVERY_COLUMNS: ChronoArbGridColumn<AlertDeliveryResponse>[] = [
  {
    field: "channel",
    text: "Channel",
    width: 110,
    render: (delivery) => CHANNEL_LABEL[delivery.channel] ?? delivery.channel,
  },
  {
    field: "delivery_status",
    text: "Status",
    width: 110,
    render: (delivery) => delivery.delivery_status,
  },
  {
    field: "opportunity_id",
    text: "Opportunity",
    width: 180,
    render: (delivery) => delivery.opportunity_id,
  },
  {
    field: "material_version",
    text: "Version",
    width: 100,
    render: (delivery) => `v${delivery.material_version}`,
  },
  {
    field: "created_at",
    text: "Created",
    width: 170,
    render: (delivery) => formatDate(delivery.created_at),
  },
];

interface AlertRuleFormData {
  name: string;
  reference_ids: string;
  min_profit: string;
  max_acquisition: string;
  conditions: string;
  channels: string;
  cooldown_minutes: string;
}

export default function AlertsPage() {
  const { data, isLoading, isError, error } = useAlertRules();
  const { data: deliveries, isLoading: deliveriesLoading } = useAlertDeliveries();
  const createAlertRule = useCreateAlertRule();
  const updateAlertRule = useUpdateAlertRule();
  const deleteAlertRule = useDeleteAlertRule();
  const requestAlertTest = useRequestAlertTest();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editDialogOpen, setEditDialogOpen] = React.useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = React.useState(false);
  const [deleteId, setDeleteId] = React.useState<string | null>(null);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [testDialogOpen, setTestDialogOpen] = React.useState(false);
  const [testingId, setTestingId] = React.useState<string | null>(null);
  const [testResult, setTestResult] = React.useState<{
    event_id: string;
    status: string;
  } | null>(null);
  const [form, setForm] = React.useState<AlertRuleFormData>({
    name: "",
    reference_ids: "",
    min_profit: "",
    max_acquisition: "",
    conditions: "",
    channels: "in_app",
    cooldown_minutes: "60",
  });

  const openCreateDialog = React.useCallback(() => {
    setForm({
      name: "",
      reference_ids: "",
      min_profit: "",
      max_acquisition: "",
      conditions: "",
      channels: "in_app",
      cooldown_minutes: "60",
    });
    setDialogOpen(true);
  }, []);

  const openEditDialog = React.useCallback((rule: AlertRuleResponse) => {
    setForm({
      name: rule.name,
      reference_ids: (rule.filters.reference_ids ?? []).join(", "),
      min_profit: rule.filters.min_profit ?? "",
      max_acquisition: rule.filters.max_acquisition ?? "",
      conditions: (rule.filters.conditions ?? []).join(", "),
      channels: rule.channels.join(", "),
      cooldown_minutes: String(rule.cooldown_minutes),
    });
    setEditingId(rule.id);
    setEditDialogOpen(true);
  }, []);

  const openTestDialog = React.useCallback((rule: AlertRuleResponse) => {
    setTestingId(rule.id);
    setTestDialogOpen(true);
    setTestResult(null);
  }, []);

  const openDeleteDialog = React.useCallback((rule: AlertRuleResponse) => {
    setDeleteId(rule.id);
    setDeleteConfirmOpen(true);
  }, []);

  const ruleActions = React.useMemo<ChronoArbGridAction<AlertRuleResponse>[]>(
    () => [
      { key: "edit", label: "Edit", onClick: openEditDialog },
      { key: "test", label: "Test", onClick: openTestDialog },
      { key: "delete", label: "Delete", tone: "danger", onClick: openDeleteDialog },
    ],
    [openDeleteDialog, openEditDialog, openTestDialog],
  );

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (createAlertRule.isPending) return;
    const referenceIds = form.reference_ids
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    const conditions = form.conditions
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    await createAlertRule.mutateAsync({
      name: form.name,
      filters: {
        reference_ids: referenceIds.length > 0 ? referenceIds : null,
        min_profit: form.min_profit || null,
        max_acquisition: form.max_acquisition || null,
        conditions: conditions.length > 0 ? conditions : null,
      },
      channels: form.channels.split(",").map((c) => c.trim()).filter(Boolean) as unknown as AlertChannel[],
      cooldown_minutes: Number(form.cooldown_minutes) || 60,
      is_enabled: true,
    });
    setForm({
      name: "",
      reference_ids: "",
      min_profit: "",
      max_acquisition: "",
      conditions: "",
      channels: "in_app",
      cooldown_minutes: "60",
    });
    setDialogOpen(false);
  };

  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (updateAlertRule.isPending || !editingId) return;
    const referenceIds = form.reference_ids
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    const conditions = form.conditions
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    await updateAlertRule.mutateAsync({
      ruleId: editingId,
      body: {
        name: form.name,
        filters: {
          reference_ids: referenceIds.length > 0 ? referenceIds : null,
          min_profit: form.min_profit || null,
          max_acquisition: form.max_acquisition || null,
          conditions: conditions.length > 0 ? conditions : null,
        },
        channels: form.channels.split(",").map((c) => c.trim()).filter(Boolean) as unknown as AlertChannel[],
        cooldown_minutes: Number(form.cooldown_minutes) || 60,
        is_enabled: true,
      },
    });
    setForm({
      name: "",
      reference_ids: "",
      min_profit: "",
      max_acquisition: "",
      conditions: "",
      channels: "in_app",
      cooldown_minutes: "60",
    });
    setEditingId(null);
    setEditDialogOpen(false);
  };

  const handleDelete = async () => {
    if (deleteAlertRule.isPending || !deleteId) return;
    await deleteAlertRule.mutateAsync(deleteId);
    setDeleteId(null);
    setDeleteConfirmOpen(false);
  };

  const handleTest = async () => {
    if (requestAlertTest.isPending || !testingId) return;
    const result = await requestAlertTest.mutateAsync(testingId);
    setTestResult(result);
    setTestDialogOpen(false);
  };

  const alertRules: AlertRuleResponse[] = data ?? [];
  const alertDeliveries: AlertDeliveryResponse[] = deliveries ?? [];

  if (isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading alert rules" fullPage />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Unable to load alert rules"
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
        title="Alerts"
        description="Manage your matching rules and notifications."
        actions={
          <Button variant="outlined" onClick={openCreateDialog}>
            Create alert rule
          </Button>
        }
      />
      <Box sx={{ display: "flex", flexDirection: { xs: "column", lg: "row" }, gap: 2 }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            Alert Rules
          </Typography>
          {alertRules.length === 0 ? (
            <EmptyState
              title="No alert rules"
              description="Create your first alert rule to get notified about matching opportunities."
              actionLabel="Create alert rule"
              onAction={openCreateDialog}
            />
          ) : (
            <ChronoArbGrid
              ariaLabel="Alert rules"
              rows={alertRules}
              columns={RULE_COLUMNS}
              actions={ruleActions}
              height={430}
            />
          )}
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            Recent Deliveries
          </Typography>
          {deliveriesLoading ? (
            <LoadingState label="Loading deliveries" />
          ) : alertDeliveries.length === 0 ? (
            <EmptyState
              title="No deliveries"
              description="Alert deliveries will appear here when rules match opportunities."
            />
          ) : (
            <ChronoArbGrid
              ariaLabel="Alert deliveries"
              rows={alertDeliveries}
              columns={DELIVERY_COLUMNS}
              height={430}
            />
          )}
        </Box>
      </Box>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Create Alert Rule</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleCreateSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <TextField
                required
                label="Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                helperText="A name for this alert rule"
              />
              <TextField
                label="Reference IDs"
                value={form.reference_ids}
                onChange={(e) => setForm({ ...form, reference_ids: e.target.value })}
                helperText="Comma-separated catalog reference IDs"
              />
              <TextField
                label="Min Profit"
                type="text"
                inputMode="decimal"
                value={form.min_profit}
                onChange={(e) => setForm({ ...form, min_profit: e.target.value })}
                helperText="Minimum expected profit (decimal string)"
              />
              <TextField
                label="Max Acquisition"
                type="text"
                inputMode="decimal"
                value={form.max_acquisition}
                onChange={(e) => setForm({ ...form, max_acquisition: e.target.value })}
                helperText="Maximum all-in acquisition price (decimal string)"
              />
              <TextField
                label="Conditions"
                value={form.conditions}
                onChange={(e) => setForm({ ...form, conditions: e.target.value })}
                helperText="Comma-separated condition labels"
              />
              <TextField
                required
                label="Channels"
                value={form.channels}
                onChange={(e) => setForm({ ...form, channels: e.target.value })}
                helperText="Comma-separated: in_app, push, telegram"
              />
              <TextField
                required
                label="Cooldown (minutes)"
                type="text"
                inputMode="numeric"
                value={form.cooldown_minutes}
                onChange={(e) => setForm({ ...form, cooldown_minutes: e.target.value })}
                helperText="Minutes between notifications for the same opportunity"
              />
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button type="button" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={createAlertRule.isPending}
                >
                  Create
                </Button>
              </Box>
            </Box>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Edit Alert Rule</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleUpdateSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <TextField
                required
                label="Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                helperText="A name for this alert rule"
              />
              <TextField
                label="Reference IDs"
                value={form.reference_ids}
                onChange={(e) => setForm({ ...form, reference_ids: e.target.value })}
                helperText="Comma-separated catalog reference IDs"
              />
              <TextField
                label="Min Profit"
                type="text"
                inputMode="decimal"
                value={form.min_profit}
                onChange={(e) => setForm({ ...form, min_profit: e.target.value })}
                helperText="Minimum expected profit (decimal string)"
              />
              <TextField
                label="Max Acquisition"
                type="text"
                inputMode="decimal"
                value={form.max_acquisition}
                onChange={(e) => setForm({ ...form, max_acquisition: e.target.value })}
                helperText="Maximum all-in acquisition price (decimal string)"
              />
              <TextField
                label="Conditions"
                value={form.conditions}
                onChange={(e) => setForm({ ...form, conditions: e.target.value })}
                helperText="Comma-separated condition labels"
              />
              <TextField
                required
                label="Channels"
                value={form.channels}
                onChange={(e) => setForm({ ...form, channels: e.target.value })}
                helperText="Comma-separated: in_app, push, telegram"
              />
              <TextField
                required
                label="Cooldown (minutes)"
                type="text"
                inputMode="numeric"
                value={form.cooldown_minutes}
                onChange={(e) => setForm({ ...form, cooldown_minutes: e.target.value })}
                helperText="Minutes between notifications for the same opportunity"
              />
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button type="button" onClick={() => setEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={updateAlertRule.isPending}
                >
                  Save
                </Button>
              </Box>
            </Box>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Delete Alert Rule</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <Typography variant="body2">
            Are you sure you want to delete this alert rule? This cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 2, pb: 2 }}>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDelete}
            variant="contained"
            color="error"
            disabled={deleteAlertRule.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={testDialogOpen}
        onClose={() => setTestDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Test Alert Rule</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          {testResult ? (
            <>
              <Typography variant="body2">
                Test notification accepted.
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Event ID: {testResult.event_id} • Status: {testResult.status}
              </Typography>
            </>
          ) : (
            <Typography variant="body2">
              Send a test notification for this alert rule?
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 2, pb: 2 }}>
          {testResult ? (
            <Button
              onClick={() => {
                setTestDialogOpen(false);
                setTestResult(null);
              }}
            >
              Done
            </Button>
          ) : (
            <>
              <Button
                onClick={() => {
                  setTestDialogOpen(false);
                  setTestingId(null);
                  setTestResult(null);
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleTest}
                variant="contained"
                disabled={requestAlertTest.isPending}
              >
                Send test
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
}
