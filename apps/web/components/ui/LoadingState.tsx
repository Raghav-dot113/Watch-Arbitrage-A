"use client";

import { Box, CircularProgress, Typography } from "@mui/material";

export interface LoadingStateProps {
  /**
   * Human-readable label announced to screen readers.
   */
  label?: string;
  /**
   * When true, renders a full-page centered loader; otherwise inline.
   */
  fullPage?: boolean;
}

export function LoadingState({ label = "Loading", fullPage = false }: LoadingStateProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        height: fullPage ? "100%" : "auto",
        minHeight: fullPage ? "300px" : undefined,
      }}
    >
      <CircularProgress size={40} sx={{ color: "primary.main" }} />
      <Box component="span" sx={{ width: 1, height: 1, position: "absolute", overflow: "hidden", clip: "rect(0 0 0 0)", whiteSpace: "nowrap" }}>
        {label}
      </Box>
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ fontSize: "0.875rem" }}
      >
        {label}
      </Typography>
    </Box>
  );
}
