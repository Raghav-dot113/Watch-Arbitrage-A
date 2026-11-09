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
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingState } from "../../../components/ui/LoadingState";
import {
  useWatchlists,
  useCreateWatchList,
  useUpdateWatchList,
  useDeleteWatchList,
  type WatchList,
} from "../../../lib/hooks/useWatchlists";
import { formatDate } from "../../../lib/formatters";

interface WatchListFormData {
  name: string;
  reference_ids: string;
}

export default function WatchesPage() {
  const { data, isLoading, isError, error } = useWatchlists();
  const createWatchList = useCreateWatchList();
  const updateWatchList = useUpdateWatchList();
  const deleteWatchList = useDeleteWatchList();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editDialogOpen, setEditDialogOpen] = React.useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = React.useState(false);
  const [deleteId, setDeleteId] = React.useState<string | null>(null);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [form, setForm] = React.useState<WatchListFormData>({
    name: "",
    reference_ids: "",
  });

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (createWatchList.isPending) return;
    const referenceIds = form.reference_ids
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    await createWatchList.mutateAsync({
      name: form.name,
      reference_ids: referenceIds,
    });
    setForm({ name: "", reference_ids: "" });
    setDialogOpen(false);
  };

  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (updateWatchList.isPending || !editingId) return;
    const referenceIds = form.reference_ids
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    await updateWatchList.mutateAsync({
      watchListId: editingId,
      body: { name: form.name, reference_ids: referenceIds },
    });
    setForm({ name: "", reference_ids: "" });
    setEditingId(null);
    setEditDialogOpen(false);
  };

  const handleDelete = async () => {
    if (deleteWatchList.isPending || !deleteId) return;
    await deleteWatchList.mutateAsync(deleteId);
    setDeleteId(null);
    setDeleteConfirmOpen(false);
  };

  const watchLists: WatchList[] = data ?? [];

  if (isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading watch lists" fullPage />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Unable to load watch lists"
          description={
            error instanceof Error ? error.message : "An unexpected error occurred."
          }
          retryLabel="Try again"
          onRetry={() => window.location.reload()}
        />
      </PageContainer>
    );
  }

  if (watchLists.length === 0) {
    return (
      <PageContainer>
        <PageHeader
          title="Watches"
          description="Organize catalog references into watch lists."
          actions={
            <Button
              variant="outlined"
              onClick={() => {
                setForm({ name: "", reference_ids: "" });
                setDialogOpen(true);
              }}
            >
              Create watch list
            </Button>
          }
        />
        <EmptyState
          title="No watch lists"
          description="Create your first watch list to track catalog references."
          actionLabel="Create watch list"
          onAction={() => {
            setForm({ name: "", reference_ids: "" });
            setDialogOpen(true);
          }}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="Watches"
        description="Organize catalog references into watch lists."
        actions={
          <Button
            variant="outlined"
            onClick={() => {
              setForm({ name: "", reference_ids: "" });
              setDialogOpen(true);
            }}
          >
            Create watch list
          </Button>
        }
      />
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {watchLists.map((watchList) => (
          <Box key={watchList.id} sx={{ p: 2, bgcolor: "background.paper", border: `1px solid`, borderColor: "divider", borderRadius: "md" }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "text.primary" }}>
                {watchList.name}
              </Typography>
              <Box sx={{ display: "flex", gap: 1 }}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    setForm({
                      name: watchList.name,
                      reference_ids: watchList.entries.map((e) => e.reference_id).join(", "),
                    });
                    setEditingId(watchList.id);
                    setEditDialogOpen(true);
                  }}
                >
                  Edit
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  color="error"
                  onClick={() => {
                    setDeleteId(watchList.id);
                    setDeleteConfirmOpen(true);
                  }}
                >
                  Delete
                </Button>
              </Box>
            </Box>
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {watchList.entries.length} {watchList.entries.length === 1 ? "entry" : "entries"} • Created {formatDate(watchList.created_at)}
              </Typography>
            </Box>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
              {watchList.entries.map((entry) => (
                <Chip
                  key={entry.id}
                  label={entry.reference_id}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        ))}
      </Box>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Create Watch List</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleCreateSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              required
              label="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              helperText="A name for this watch list"
            />
            <TextField
              required
              label="Reference IDs"
              value={form.reference_ids}
              onChange={(e) => setForm({ ...form, reference_ids: e.target.value })}
              helperText="Comma-separated catalog reference IDs"
            />
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
              <Button type="button" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={createWatchList.isPending}
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
        <DialogTitle sx={{ fontWeight: 600 }}>Edit Watch List</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleUpdateSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              required
              label="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              helperText="A name for this watch list"
            />
            <TextField
              required
              label="Reference IDs"
              value={form.reference_ids}
              onChange={(e) => setForm({ ...form, reference_ids: e.target.value })}
              helperText="Comma-separated catalog reference IDs"
            />
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
              <Button type="button" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={updateWatchList.isPending}
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
        <DialogTitle sx={{ fontWeight: 600 }}>Delete Watch List</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <Typography variant="body2">
            Are you sure you want to delete this watch list? This cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 2, pb: 2 }}>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDelete}
            variant="contained"
            color="error"
            disabled={deleteWatchList.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
}
