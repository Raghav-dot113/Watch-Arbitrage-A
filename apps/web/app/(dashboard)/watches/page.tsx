"use client";

import React from "react";
import {
  Alert,
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

const WATCH_LIST_COLUMNS: ChronoArbGridColumn<WatchList>[] = [
  { field: "name", text: "Name", flex: 1, render: (watchList) => watchList.name },
  {
    field: "entries",
    text: "Entries",
    width: 110,
    render: (watchList) =>
      `${watchList.entries.length} ${watchList.entries.length === 1 ? "entry" : "entries"}`,
  },
  {
    field: "references",
    text: "References",
    width: 320,
    render: (watchList) =>
      watchList.entries.map((entry) => entry.reference_id).join(", ") || "—",
  },
  {
    field: "created_at",
    text: "Created",
    width: 170,
    render: (watchList) => formatDate(watchList.created_at),
  },
];

function parseReferenceIds(value: string): string[] {
  const ids = value
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean);
  return ids.filter((id, index) => ids.indexOf(id) === index);
}

function getMutationErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "error" in error) {
    const apiError = (error as { error?: { message?: unknown } }).error;
    if (typeof apiError?.message === "string" && apiError.message) {
      return apiError.message;
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
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
  const [formError, setFormError] = React.useState<string | null>(null);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);
  const [form, setForm] = React.useState<WatchListFormData>({
    name: "",
    reference_ids: "",
  });

  const openCreateDialog = () => {
    setForm({ name: "", reference_ids: "" });
    setFormError(null);
    setDialogOpen(true);
  };

  const closeCreateDialog = () => {
    if (createWatchList.isPending) return;
    setDialogOpen(false);
    setFormError(null);
  };

  const openEditDialog = React.useCallback((watchList: WatchList) => {
    setForm({
      name: watchList.name,
      reference_ids: watchList.entries.map((entry) => entry.reference_id).join(", "),
    });
    setFormError(null);
    setEditingId(watchList.id);
    setEditDialogOpen(true);
  }, []);

  const closeEditDialog = () => {
    if (updateWatchList.isPending) return;
    setEditDialogOpen(false);
    setEditingId(null);
    setFormError(null);
  };

  const openDeleteDialog = React.useCallback((watchListId: string) => {
    setDeleteId(watchListId);
    setDeleteError(null);
    setDeleteConfirmOpen(true);
  }, []);

  const watchListActions = React.useMemo<ChronoArbGridAction<WatchList>[]>(
    () => [
      { key: "edit", label: "Edit", onClick: openEditDialog },
      {
        key: "delete",
        label: "Delete",
        tone: "danger",
        onClick: (watchList) => openDeleteDialog(watchList.id),
      },
    ],
    [openDeleteDialog, openEditDialog],
  );

  const closeDeleteDialog = () => {
    if (deleteWatchList.isPending) return;
    setDeleteConfirmOpen(false);
    setDeleteId(null);
    setDeleteError(null);
  };

  const handleCreateSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (createWatchList.isPending) return;
    const name = form.name.trim();
    if (!name) {
      setFormError("Enter a name for this watch list.");
      return;
    }
    setFormError(null);
    try {
      await createWatchList.mutateAsync({
        name,
        reference_ids: parseReferenceIds(form.reference_ids),
      });
    } catch (error) {
      setFormError(getMutationErrorMessage(error));
      return;
    }
    setForm({ name: "", reference_ids: "" });
    setDialogOpen(false);
  };

  const handleUpdateSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (updateWatchList.isPending || !editingId) return;
    const name = form.name.trim();
    if (!name) {
      setFormError("Enter a name for this watch list.");
      return;
    }
    setFormError(null);
    try {
      await updateWatchList.mutateAsync({
        watchListId: editingId,
        body: { name, reference_ids: parseReferenceIds(form.reference_ids) },
      });
    } catch (error) {
      setFormError(getMutationErrorMessage(error));
      return;
    }
    setForm({ name: "", reference_ids: "" });
    setEditingId(null);
    setEditDialogOpen(false);
  };

  const handleDelete = async () => {
    if (deleteWatchList.isPending || !deleteId) return;
    try {
      await deleteWatchList.mutateAsync(deleteId);
    } catch (error) {
      setDeleteError(getMutationErrorMessage(error));
      return;
    }
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

  return (
    <PageContainer>
      <PageHeader
        title="Watches"
        description="Organize catalog references into watch lists."
        actions={
          <Button variant="outlined" onClick={openCreateDialog}>
            Create watch list
          </Button>
        }
      />
      {watchLists.length === 0 ? (
        <EmptyState
          title="No watch lists"
          description="Create your first watch list to track catalog references."
          actionLabel="Create watch list"
          onAction={openCreateDialog}
        />
      ) : (
        <ChronoArbGrid
          ariaLabel="Watch lists"
          rows={watchLists}
          columns={WATCH_LIST_COLUMNS}
          actions={watchListActions}
          height={420}
        />
      )}

      <Dialog open={dialogOpen} onClose={closeCreateDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>Create Watch List</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleCreateSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {formError && <Alert severity="error">{formError}</Alert>}
              <TextField
                required
                autoFocus
                label="Name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                helperText="A name for this watch list"
              />
              <TextField
                label="Reference IDs"
                value={form.reference_ids}
                onChange={(event) =>
                  setForm({ ...form, reference_ids: event.target.value })
                }
                helperText="Optional: comma-separated catalog reference IDs"
              />
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button
                  type="button"
                  onClick={closeCreateDialog}
                  disabled={createWatchList.isPending}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={createWatchList.isPending}
                >
                  {createWatchList.isPending ? "Creating..." : "Create"}
                </Button>
              </Box>
            </Box>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={editDialogOpen} onClose={closeEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>Edit Watch List</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleUpdateSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {formError && <Alert severity="error">{formError}</Alert>}
              <TextField
                required
                autoFocus
                label="Name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                helperText="A name for this watch list"
              />
              <TextField
                label="Reference IDs"
                value={form.reference_ids}
                onChange={(event) =>
                  setForm({ ...form, reference_ids: event.target.value })
                }
                helperText="Optional: comma-separated catalog reference IDs"
              />
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button
                  type="button"
                  onClick={closeEditDialog}
                  disabled={updateWatchList.isPending}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={updateWatchList.isPending}
                >
                  {updateWatchList.isPending ? "Saving..." : "Save"}
                </Button>
              </Box>
            </Box>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteConfirmOpen}
        onClose={closeDeleteDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Delete Watch List</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          {deleteError && <Alert severity="error">{deleteError}</Alert>}
          <Typography variant="body2">
            Are you sure you want to delete this watch list? This cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 2, pb: 2 }}>
          <Button onClick={closeDeleteDialog} disabled={deleteWatchList.isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            variant="contained"
            color="error"
            disabled={deleteWatchList.isPending}
          >
            {deleteWatchList.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
}
