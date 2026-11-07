"use client";

import { Box } from "@mui/material";

export interface PageContainerProps {
  children: React.ReactNode;
  sx?: React.CSSProperties;
}

export function PageContainer({ children, sx }: PageContainerProps) {
  return (
    <Box className="px-6 sm:px-8 lg:px-10" sx={sx}>
      {children}
    </Box>
  );
}
