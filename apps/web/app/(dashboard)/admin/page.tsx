"use client";

import React from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import { LoadingState } from "../../../components/ui/LoadingState";
import {
  ChronoArbGrid,
  type ChronoArbGridAction,
  type ChronoArbGridColumn,
} from "../../../components/bryntum/ChronoArbGrid";
import {
  useSources,
  useUpdateSource,
  useFeatureFlags,
  useUpdateFeatureFlag,
  useAuditEvents,
  useUnmatchedListings,
  useResolveUnmatchedListing,
  useDuplicateGroups,
  type SourceAdmin,
  type FeatureFlag,
  type AuditEvent,
  type UnmatchedListing,
  type DuplicateGroup,
} from "../../../lib/hooks/useAdmin";
import { formatDate } from "../../../lib/formatters";

const SOURCE_COLUMNS: ChronoArbGridColumn<SourceAdmin>[] = [
  { field: "display_name", text: "Source", flex: 1, render: (source) => source.display_name },
  { field: "source_key", text: "Key", width: 150, render: (source) => source.source_key },
  {
    field: "adapter_version",
    text: "Adapter",
    width: 110,
    render: (source) => source.adapter_version,
  },
  { field: "access_mode", text: "Access", width: 120, render: (source) => source.access_mode },
  { field: "health_status", text: "Health", width: 110, render: (source) => source.health_status },
  {
    field: "last_fetched_at",
    text: "Last fetched",
    width: 170,
    render: (source) =>
      source.last_fetched_at ? formatDate(source.last_fetched_at) : "—",
  },
  {
    field: "is_enabled",
    text: "State",
    width: 100,
    render: (source) => (source.is_enabled ? "Enabled" : "Disabled"),
  },
];

const FLAG_COLUMNS: ChronoArbGridColumn<FeatureFlag>[] = [
  { field: "key", text: "Flag", width: 190, render: (flag) => flag.key },
  { field: "description", text: "Description", flex: 1, render: (flag) => flag.description ?? "—" },
  {
    field: "enabled",
    text: "State",
    width: 100,
    render: (flag) => (flag.enabled ? "Enabled" : "Disabled"),
  },
  { field: "rollout_pct", text: "Rollout", width: 100, render: (flag) => `${flag.rollout_pct}%` },
  {
    field: "organization_ids",
    text: "Organizations",
    width: 200,
    render: (flag) => (flag.organization_ids ?? []).join(", ") || "All",
  },
  {
    field: "expires_at",
    text: "Expires",
    width: 160,
    render: (flag) => (flag.expires_at ? formatDate(flag.expires_at) : "—"),
  },
  {
    field: "created_at",
    text: "Created",
    width: 160,
    render: (flag) => formatDate(flag.created_at),
  },
];

const AUDIT_COLUMNS: ChronoArbGridColumn<AuditEvent>[] = [
  { field: "created_at", text: "When", width: 170, render: (event) => formatDate(event.created_at) },
  { field: "action", text: "Action", width: 220, render: (event) => event.action },
  {
    field: "resource_type",
    text: "Resource",
    width: 140,
    render: (event) => event.resource_type,
  },
  {
    field: "resource_id",
    text: "Resource ID",
    width: 190,
    render: (event) => event.resource_id,
  },
  { field: "user_id", text: "User", width: 160, render: (event) => event.user_id ?? "—" },
  {
    field: "organization_id",
    text: "Organization",
    width: 160,
    render: (event) => event.organization_id ?? "—",
  },
  { field: "trace_id", text: "Trace", width: 180, render: (event) => event.trace_id ?? "—" },
];

const UNMATCHED_COLUMNS: ChronoArbGridColumn<UnmatchedListing>[] = [
  {
    field: "title",
    text: "Listing",
    flex: 1,
    render: (listing) => listing.title ?? "Untitled",
  },
  {
    field: "source_key",
    text: "Source",
    width: 130,
    render: (listing) => listing.source_key,
  },
  {
    field: "reference_id",
    text: "Reference",
    width: 170,
    render: (listing) => listing.reference_id,
  },
  {
    field: "match_method",
    text: "Match method",
    width: 150,
    render: (listing) => listing.match_method ?? "—",
  },
  {
    field: "external_url",
    text: "External URL",
    width: 260,
    render: (listing) => listing.external_url ?? "—",
  },
  {
    field: "observation_at",
    text: "Observed",
    width: 170,
    render: (listing) => formatDate(listing.observation_at),
  },
];

const DUPLICATE_COLUMNS: ChronoArbGridColumn<DuplicateGroup>[] = [
  {
    field: "representative_id",
    text: "Representative",
    width: 200,
    render: (group) => group.representative_id,
  },
  { field: "method", text: "Method", width: 150, render: (group) => group.method ?? "—" },
  {
    field: "confidence",
    text: "Confidence",
    width: 120,
    render: (group) => group.confidence ?? "—",
  },
  {
    field: "listing_ids",
    text: "Listings",
    flex: 1,
    render: (group) => group.listing_ids.join(", "),
  },
  {
    field: "created_at",
    text: "Created",
    width: 170,
    render: (group) => formatDate(group.created_at),
  },
];

export default function AdminPage() {
  const [tab, setTab] = React.useState("sources");

  const { data: sources, isLoading: sourcesLoading } = useSources();
  const updateSource = useUpdateSource();
  const [sourceToggleOpen, setSourceToggleOpen] = React.useState(false);
  const [toggleSourceId, setToggleSourceId] = React.useState<string | null>(null);
  const [toggleSourceEnabled, setToggleSourceEnabled] = React.useState(false);

  const { data: flags, isLoading: flagsLoading } = useFeatureFlags();
  const updateFeatureFlag = useUpdateFeatureFlag();
  const [flagDialogOpen, setFlagDialogOpen] = React.useState(false);
  const [editingFlagId, setEditingFlagId] = React.useState<string | null>(null);
  const [flagForm, setFlagForm] = React.useState<{
    enabled: boolean;
    rollout_pct: string;
    organization_ids: string;
  }>({ enabled: true, rollout_pct: "", organization_ids: "" });

  const { data: auditEvents, isLoading: auditLoading } = useAuditEvents();

  const { data: unmatched, isLoading: unmatchedLoading } = useUnmatchedListings();
  const resolveUnmatched = useResolveUnmatchedListing();
  const [resolveDialogOpen, setResolveDialogOpen] = React.useState(false);
  const [resolveListingId, setResolveListingId] = React.useState<string | null>(null);
  const [resolveReferenceId, setResolveReferenceId] = React.useState("");

  const { data: duplicates, isLoading: duplicatesLoading } = useDuplicateGroups();

  const openSourceToggle = React.useCallback((source: SourceAdmin) => {
    setToggleSourceId(source.id);
    setToggleSourceEnabled(source.is_enabled);
    setSourceToggleOpen(true);
  }, []);

  const openFlagEditor = React.useCallback((flag: FeatureFlag) => {
    setEditingFlagId(flag.id);
    setFlagForm({
      enabled: flag.enabled,
      rollout_pct: String(flag.rollout_pct ?? ""),
      organization_ids: (flag.organization_ids ?? []).join(", "),
    });
    setFlagDialogOpen(true);
  }, []);

  const openResolveDialog = React.useCallback((listing: UnmatchedListing) => {
    setResolveListingId(listing.id);
    setResolveReferenceId(listing.reference_id);
    setResolveDialogOpen(true);
  }, []);

  const sourceActions = React.useMemo<ChronoArbGridAction<SourceAdmin>[]>(
    () => [
      {
        key: "toggle",
        label: (source) => (source.is_enabled ? "Disable" : "Enable"),
        onClick: openSourceToggle,
      },
    ],
    [openSourceToggle],
  );

  const flagActions = React.useMemo<ChronoArbGridAction<FeatureFlag>[]>(
    () => [{ key: "edit", label: "Edit", onClick: openFlagEditor }],
    [openFlagEditor],
  );

  const unmatchedActions = React.useMemo<ChronoArbGridAction<UnmatchedListing>[]>(
    () => [{ key: "resolve", label: "Resolve", onClick: openResolveDialog }],
    [openResolveDialog],
  );

  const isLoading =
    sourcesLoading ||
    flagsLoading ||
    auditLoading ||
    unmatchedLoading ||
    duplicatesLoading;

  if (isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading admin console" fullPage />
      </PageContainer>
    );
  }

  const sourceList: SourceAdmin[] = sources ?? [];
  const flagList: FeatureFlag[] = flags ?? [];
  const auditList: AuditEvent[] = auditEvents ?? [];
  const unmatchedList: UnmatchedListing[] = unmatched ?? [];
  const duplicateList: DuplicateGroup[] = duplicates ?? [];

  const handleToggleSource = async () => {
    if (updateSource.isPending || !toggleSourceId) return;
    await updateSource.mutateAsync({
      sourceId: toggleSourceId,
      isEnabled: !toggleSourceEnabled,
    });
    setToggleSourceId(null);
    setSourceToggleOpen(false);
  };

  const handleFlagSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (updateFeatureFlag.isPending || !editingFlagId) return;
    const orgIds = flagForm.organization_ids
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    await updateFeatureFlag.mutateAsync({
      flagId: editingFlagId,
      body: {
        enabled: flagForm.enabled,
        rollout_pct:
          flagForm.rollout_pct === "" ? undefined : Number(flagForm.rollout_pct),
        organization_ids: orgIds.length > 0 ? orgIds : null,
        expires_at: null,
      },
    });
    setFlagForm({ enabled: true, rollout_pct: "", organization_ids: "" });
    setEditingFlagId(null);
    setFlagDialogOpen(false);
  };

  const handleResolve = async () => {
    if (resolveUnmatched.isPending || !resolveListingId) return;
    await resolveUnmatched.mutateAsync({
      listingId: resolveListingId,
      referenceId: resolveReferenceId,
    });
    setResolveListingId(null);
    setResolveReferenceId("");
    setResolveDialogOpen(false);
  };

  return (
    <PageContainer>
      <PageHeader
        title="Admin Console"
        description="Manage sources, feature flags, audit events, unmatched listings, and duplicate groups."
      />
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Tabs
          value={tab}
          onChange={(_, newValue) => setTab(newValue as string)}
          sx={{ minWidth: 300 }}
        >
          <Tab label="Sources" value="sources" />
          <Tab label="Feature Flags" value="flags" />
          <Tab label="Audit Events" value="audit" />
          <Tab label="Unmatched Listings" value="unmatched" />
          <Tab label="Duplicate Groups" value="duplicates" />
        </Tabs>

        {tab === "sources" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Data Sources
            </Typography>
            {sourceList.length === 0 ? (
              <EmptyState title="No sources" />
            ) : (
              <ChronoArbGrid
                ariaLabel="Data sources"
                rows={sourceList}
                columns={SOURCE_COLUMNS}
                actions={sourceActions}
                height={460}
              />
            )}
          </Box>
        )}

        {tab === "flags" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Feature Flags
            </Typography>
            {flagList.length === 0 ? (
              <EmptyState title="No feature flags" />
            ) : (
              <ChronoArbGrid
                ariaLabel="Feature flags"
                rows={flagList}
                columns={FLAG_COLUMNS}
                actions={flagActions}
                height={460}
              />
            )}
          </Box>
        )}

        {tab === "audit" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Audit Events
            </Typography>
            {auditList.length === 0 ? (
              <EmptyState title="No audit events" />
            ) : (
              <ChronoArbGrid
                ariaLabel="Audit events"
                rows={auditList}
                columns={AUDIT_COLUMNS}
                height={500}
              />
            )}
          </Box>
        )}

        {tab === "unmatched" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Unmatched Listings
            </Typography>
            {unmatchedList.length === 0 ? (
              <EmptyState title="No unmatched listings" />
            ) : (
              <ChronoArbGrid
                ariaLabel="Unmatched listings"
                rows={unmatchedList}
                columns={UNMATCHED_COLUMNS}
                actions={unmatchedActions}
                height={460}
              />
            )}
          </Box>
        )}

        {tab === "duplicates" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Duplicate Groups
            </Typography>
            {duplicateList.length === 0 ? (
              <EmptyState title="No duplicate groups" />
            ) : (
              <ChronoArbGrid
                ariaLabel="Duplicate groups"
                rows={duplicateList}
                columns={DUPLICATE_COLUMNS}
                height={420}
              />
            )}
          </Box>
        )}

        <Dialog
          open={sourceToggleOpen}
          onClose={() => setSourceToggleOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ fontWeight: 600 }}>
            {toggleSourceEnabled ? "Disable Source" : "Enable Source"}
          </DialogTitle>
          <DialogContent sx={{ py: 2 }}>
            <Typography variant="body2">
              Are you sure you want to{" "}
              {toggleSourceEnabled ? "disable" : "enable"} this data source?
            </Typography>
          </DialogContent>
          <DialogActions sx={{ px: 2, pb: 2 }}>
            <Button onClick={() => setSourceToggleOpen(false)}>Cancel</Button>
            <Button
              onClick={handleToggleSource}
              variant="contained"
              color="error"
              disabled={updateSource.isPending}
            >
              {toggleSourceEnabled ? "Disable" : "Enable"}
            </Button>
          </DialogActions>
        </Dialog>

        <Dialog
          open={flagDialogOpen}
          onClose={() => setFlagDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ fontWeight: 600 }}>Edit Feature Flag</DialogTitle>
          <DialogContent sx={{ py: 2 }}>
            <form onSubmit={handleFlagSubmit}>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField
                  required
                  label="Enabled"
                  select
                  value={String(flagForm.enabled)}
                  onChange={(e) =>
                    setFlagForm({ ...flagForm, enabled: e.target.value === "true" })
                  }
                >
                  <MenuItem value="true">Enabled</MenuItem>
                  <MenuItem value="false">Disabled</MenuItem>
                </TextField>
                <TextField
                  required
                  label="Rollout %"
                  type="text"
                  inputMode="numeric"
                  value={flagForm.rollout_pct}
                  onChange={(e) => setFlagForm({ ...flagForm, rollout_pct: e.target.value })}
                  helperText="0 to 100"
                />
                <TextField
                  label="Organization IDs"
                  value={flagForm.organization_ids}
                  onChange={(e) => setFlagForm({ ...flagForm, organization_ids: e.target.value })}
                  helperText="Comma-separated organization IDs (optional)"
                />
                <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                  <Button type="button" onClick={() => setFlagDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={updateFeatureFlag.isPending}
                  >
                    Save
                  </Button>
                </Box>
              </Box>
            </form>
          </DialogContent>
        </Dialog>

        <Dialog
          open={resolveDialogOpen}
          onClose={() => setResolveDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ fontWeight: 600 }}>Resolve Unmatched Listing</DialogTitle>
          <DialogContent sx={{ py: 2 }}>
            <form onSubmit={(e) => { e.preventDefault(); handleResolve(); }}>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField
                  required
                  label="Reference ID"
                  value={resolveReferenceId}
                  onChange={(e) => setResolveReferenceId(e.target.value)}
                  helperText="Catalog reference ID to match this listing against"
                />
                <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                  <Button type="button" onClick={() => setResolveDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    color="success"
                    disabled={resolveUnmatched.isPending}
                  >
                    Resolve
                  </Button>
                </Box>
              </Box>
            </form>
          </DialogContent>
        </Dialog>
      </Box>
    </PageContainer>
  );
}
