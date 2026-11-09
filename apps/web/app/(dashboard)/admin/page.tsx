"use client";

import React from "react";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  MenuItem,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingState } from "../../../components/ui/LoadingState";
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

const HEALTH_COLOR: Record<string, string> = {
  unknown: "default",
  healthy: "success",
  degraded: "warning",
  unhealthy: "error",
};

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
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {sourceList.map((source) => (
                  <Box
                    key={source.id}
                    sx={{
                      p: 2,
                      bgcolor: "background.paper",
                      border: `1px solid`,
                      borderColor: "divider",
                      borderRadius: "md",
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "text.primary" }}>
                          {source.display_name}
                        </Typography>
                        <Chip
                          label={source.source_key}
                          size="small"
                          variant="outlined"
                          color="default"
                        />
                      </Box>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setToggleSourceId(source.id);
                          setToggleSourceEnabled(source.is_enabled);
                          setSourceToggleOpen(true);
                        }}
                      >
                        {source.is_enabled ? "Disable" : "Enable"}
                      </Button>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Adapter Version
                      </Typography>
                      <Typography variant="body2">{source.adapter_version}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
                        Access Mode
                      </Typography>
                      <Typography variant="body2">{source.access_mode}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
                        Health
                      </Typography>
                      <Chip
                        label={source.health_status}
                        size="small"
                        variant="outlined"
                        color={
                          (HEALTH_COLOR[source.health_status] ?? "default") as any
                        }
                      />
                    </Box>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Last Fetched
                      </Typography>
                      <Typography variant="body2">
                        {source.last_fetched_at ? formatDate(source.last_fetched_at) : "—"}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
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
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {flagList.map((flag) => (
                  <Box
                    key={flag.id}
                    sx={{
                      p: 2,
                      bgcolor: "background.paper",
                      border: `1px solid`,
                      borderColor: "divider",
                      borderRadius: "md",
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "text.primary" }}>
                          {flag.key}
                        </Typography>
                        <Chip
                          label={flag.enabled ? "Enabled" : "Disabled"}
                          size="small"
                          variant="outlined"
                          color={(flag.enabled ? "success" : "default") as any}
                        />
                      </Box>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setEditingFlagId(flag.id);
                          setFlagForm({
                            enabled: flag.enabled,
                            rollout_pct: String(flag.rollout_pct ?? ""),
                            organization_ids: (flag.organization_ids ?? []).join(", "),
                          });
                          setFlagDialogOpen(true);
                        }}
                      >
                        Edit
                      </Button>
                    </Box>
                    {flag.description && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          Description
                        </Typography>
                        <Typography variant="body2">{flag.description}</Typography>
                      </Box>
                    )}
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Rollout %
                      </Typography>
                      <Typography variant="body2">{flag.rollout_pct}%</Typography>
                    </Box>
                    {flag.organization_ids && flag.organization_ids.length > 0 && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          Organizations
                        </Typography>
                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                          {flag.organization_ids.map((orgId) => (
                            <Chip key={orgId} label={orgId} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Expires At
                      </Typography>
                      <Typography variant="body2">
                        {flag.expires_at ? formatDate(flag.expires_at) : "—"}
                      </Typography>
                    </Box>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Created
                      </Typography>
                      <Typography variant="body2">{formatDate(flag.created_at)}</Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
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
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {auditList.map((event) => (
                  <Box
                    key={event.id}
                    sx={{
                      p: 2,
                      bgcolor: "background.paper",
                      border: `1px solid`,
                      borderColor: "divider",
                      borderRadius: "md",
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "text.primary" }}>
                        {event.action}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(event.created_at)}
                      </Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Resource Type
                      </Typography>
                      <Typography variant="body2">{event.resource_type}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
                        Resource ID
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                        {event.resource_id}
                      </Typography>
                    </Box>
                    {event.user_id && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          User ID
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                          {event.user_id}
                        </Typography>
                      </Box>
                    )}
                    {event.organization_id && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          Organization ID
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                          {event.organization_id}
                        </Typography>
                      </Box>
                    )}
                    {event.trace_id && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          Trace ID
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                          {event.trace_id}
                        </Typography>
                      </Box>
                    )}
                    {event.details && Object.keys(event.details).length > 0 && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          Details
                        </Typography>
                        <Typography variant="caption" sx={{ fontFamily: "monospace", fontSize: "0.8125rem", whiteSpace: "pre-wrap" }}>
                          {JSON.stringify(event.details, null, 2)}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
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
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {unmatchedList.map((listing) => (
                  <Box
                    key={listing.id}
                    sx={{
                      p: 2,
                      bgcolor: "background.paper",
                      border: `1px solid`,
                      borderColor: "divider",
                      borderRadius: "md",
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "text.primary" }}>
                          {listing.title ?? "Untitled"}
                        </Typography>
                        <Chip
                          label={listing.source_key}
                          size="small"
                          variant="outlined"
                          color="default"
                        />
                      </Box>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setResolveListingId(listing.id);
                          setResolveReferenceId(listing.reference_id);
                          setResolveDialogOpen(true);
                        }}
                      >
                        Resolve
                      </Button>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Reference ID
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                        {listing.reference_id}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
                        Match Method
                      </Typography>
                      <Typography variant="body2">{listing.match_method ?? "—"}</Typography>
                    </Box>
                    {listing.external_url && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                          External URL
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                          {listing.external_url}
                        </Typography>
                      </Box>
                    )}
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Observed At
                      </Typography>
                      <Typography variant="body2">{formatDate(listing.observation_at)}</Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
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
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {duplicateList.map((group) => (
                  <Box
                    key={group.id}
                    sx={{
                      p: 2,
                      bgcolor: "background.paper",
                      border: `1px solid`,
                      borderColor: "divider",
                      borderRadius: "md",
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "text.primary" }}>
                        Duplicate Group
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {group.listing_ids.length} listings
                      </Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Representative ID
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                        {group.representative_id}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
                        Method
                      </Typography>
                      <Typography variant="body2">{group.method ?? "—"}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
                        Confidence
                      </Typography>
                      <Typography variant="body2">{group.confidence ?? "—"}</Typography>
                    </Box>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Created
                      </Typography>
                      <Typography variant="body2">{formatDate(group.created_at)}</Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
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
