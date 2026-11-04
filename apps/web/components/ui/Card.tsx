"use client";

import { Box, Paper, Typography } from "@mui/material";

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  padded?: boolean;
  variant?: "outlined" | "elevation";
  sx?: any;
}

export function Card({
  children,
  title,
  subtitle,
  padded = true,
  variant = "outlined",
  sx,
}: CardProps) {
  return (
    <Paper
      variant={variant}
      sx={{
        p: padded ? 3 : 0,
        bgcolor: "background.paper",
        borderColor: "divider",
        borderRadius: "md",
        ...sx,
      }}
    >
      {title && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="h6" component="h3" sx={{ fontWeight: 600, color: "text.primary", mb: subtitle ? 0 : 1 }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.6 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
      )}
      <Box sx={{ borderTop: variant === "outlined" ? undefined : `1px solid`, borderColor: "divider", pt: title ? 2 : 0 }}>
        {children}
      </Box>
    </Paper>
  );
}
