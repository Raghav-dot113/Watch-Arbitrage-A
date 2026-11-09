"use client";

import { Box, Typography, Paper, Button } from "@mui/material";
import FolderOutlinedIcon from "@mui/icons-material/FolderOutlined";

export interface EmptyStateProps {
  /**
   * Heading text for the empty state.
   */
  title: string;
  /**
   * Supporting description text.
   */
  description?: string;
  /**
   * Optional action label (e.g. "Create watch list").
   */
  actionLabel?: string;
  /**
   * Optional action click handler.
   */
  onAction?: () => void;
  /**
   * Icon to display; defaults to a folder.
   */
  Icon?: React.ElementType;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  Icon: IconComponent = FolderOutlinedIcon,
}: EmptyStateProps) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 4,
        textAlign: "center",
        bgcolor: "background.paper",
        borderColor: "divider",
        maxWidth: "sm",
        margin: "0 auto",
      }}
    >
      <Box sx={{ mb: 2, display: "inline-flex", p: 1.5, bgcolor: "action.disabledBackground", borderRadius: "md" }}>
        <IconComponent fontSize="large" sx={{ color: "text.disabled" }} />
      </Box>
      <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600, color: "text.primary" }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, lineHeight: 1.6 }}>
          {description}
        </Typography>
      )}
      {actionLabel && onAction && (
        <Button
          variant="contained"
          onClick={onAction}
          sx={{
            bgcolor: "primary.main",
            color: "primary.contrastText",
            borderRadius: "md",
            px: 2,
            py: 1,
            fontSize: "0.875rem",
            fontWeight: 500,
            textTransform: "none",
            "&:hover": { bgcolor: "primary.dark" },
          }}
        >
          {actionLabel}
        </Button>
      )}
    </Paper>
  );
}
