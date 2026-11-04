"use client";

import { Box, Typography, Paper, Button } from "@mui/material";
import ErrorOutlinedIcon from "@mui/icons-material/ErrorOutlined";

export interface ErrorStateProps {
  /**
   * Error title/heading.
   */
  title: string;
  /**
   * Error description or message.
   */
  description?: string;
  /**
   * Optional retry label.
   */
  retryLabel?: string;
  /**
   * Optional retry handler.
   */
  onRetry?: () => void;
  /**
   * Whether to render full-page centered or inline.
   */
  fullPage?: boolean;
}

export function ErrorState({
  title,
  description,
  retryLabel = "Try again",
  onRetry,
  fullPage = false,
}: ErrorStateProps) {
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
        minHeight: fullPage ? "300px" : undefined,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: fullPage ? "center" : undefined,
      }}
    >
      <Box sx={{ mb: 2, p: 1.5, bgcolor: "error.light", color: "error.contrastText", borderRadius: "md" }}>
        <ErrorOutlinedIcon fontSize="large" />
      </Box>
      <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600, color: "text.primary" }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, lineHeight: 1.6 }}>
          {description}
        </Typography>
      )}
      {onRetry && (
        <Button
          variant="contained"
          startIcon={<ErrorOutlinedIcon fontSize="small" />}
          onClick={onRetry}
          sx={{ borderRadius: "md", textTransform: "none", fontWeight: 500 }}
        >
          {retryLabel}
        </Button>
      )}
    </Paper>
  );
}
