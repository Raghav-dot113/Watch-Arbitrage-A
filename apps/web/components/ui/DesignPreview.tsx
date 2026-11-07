"use client";

import { Box, Typography, Paper, Stack } from "@mui/material";
import {
  colors,
  semanticColors,
  typography,
  radii,
  spacing,
} from "@chronoarb/design-tokens";

interface ColorSwatchProps {
  name: string;
  value: string;
}

function ColorSwatch({ name, value }: ColorSwatchProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 1,
        p: 1.5,
        border: `1px solid`,
        borderColor: "divider",
        borderRadius: radii.md,
        bgcolor: "background.paper",
        minWidth: 96,
      }}
    >
      <Box
        sx={{
          width: 48,
          height: 48,
          borderRadius: radii.md,
          bgcolor: value,
          boxShadow: `0 0 0 1px ${value === "#ffffff" ? semanticColors.divider : "rgba(0,0,0,0.1)"}`,
        }}
      />
      <Typography
        variant="caption"
        sx={{ fontWeight: 500, color: "text.primary", mb: 0 }}
      >
        {name}
      </Typography>
      <Typography
        variant="caption"
        sx={{ color: "text.secondary", fontSize: "0.6875rem", mb: 0 }}
      >
        {value}
      </Typography>
    </Box>
  );
}

export function DesignPreview() {
  const paletteGroups = [
    { label: "Core", colors: { White: colors.white, Black: colors.black, Transparent: colors.transparent } },
    { label: "Slate", colors: colors.slate },
    { label: "Blue", colors: colors.blue },
    { label: "Emerald", colors: colors.emerald },
    { label: "Amber", colors: colors.amber },
    { label: "Rose", colors: colors.rose },
  ];

  const semanticGroups = [
    { label: "Background", colors: semanticColors.background },
    { label: "Text", colors: semanticColors.text },
    { label: "Primary", colors: semanticColors.primary },
    { label: "Success", colors: semanticColors.success },
    { label: "Warning", colors: semanticColors.warning },
    { label: "Error", colors: semanticColors.error },
    { label: "Info", colors: semanticColors.info },
    { label: "Action", colors: semanticColors.action },
  ];

  return (
    <Stack sx={{ gap: 3, py: 3 }}>
      <Paper
        variant="outlined"
        sx={{ p: 3, bgcolor: "background.paper", borderColor: "divider" }}
      >
        <Typography variant="h6" component="h2" sx={{ fontWeight: 600, mb: 2 }}>
          Design Token Preview
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Visual reference for the ChronoArb design system tokens.
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" component="h3" sx={{ fontWeight: 600, mb: 1.5, color: "text.primary" }}>
            Palette Colors
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
            {paletteGroups.map((group) =>
              Object.entries(group.colors as Record<string, string>).map(([name, value]) => (
                <ColorSwatch key={`${group.label}-${name}`} name={`${group.label} ${name}`} value={String(value)} />
              ))
            )}
          </Stack>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" component="h3" sx={{ fontWeight: 600, mb: 1.5, color: "text.primary" }}>
            Semantic Colors
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
            {semanticGroups.map((group) =>
              Object.entries(group.colors as Record<string, string>).map(([name, value]) => (
                <ColorSwatch key={`${group.label}-${name}`} name={`${group.label} ${name}`} value={String(value)} />
              ))
            )}
          </Stack>
        </Box>
      </Paper>

      <Paper
        variant="outlined"
        sx={{ p: 3, bgcolor: "background.paper", borderColor: "divider" }}
      >
        <Typography variant="h6" component="h2" sx={{ fontWeight: 600, mb: 2 }}>
          Typography & Spacing
        </Typography>
        <Stack spacing={1}>
          {[typography.h1, typography.h2, typography.h3, typography.body1, typography.body2, typography.caption, typography.overline].map((style, i) => (
            <Typography
              key={i}
              variant="body1"
              sx={{
                ...style,
                color: "text.primary",
              }}
            >
              {i === 0 ? "H1 - Display heading" : i === 1 ? "H2 - Section heading" : i === 2 ? "H3 - Sub heading" : i === 3 ? "Body 1" : i === 4 ? "Body 2" : i === 5 ? "Caption" : "Overline"}
            </Typography>
          ))}
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, mb: 0.5 }}>
              Base spacing unit: {spacing}px
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Border radii: none={radii.none}px, sm={radii.sm}px, md={radii.md}px, lg={radii.lg}px, full={radii.full}px
            </Typography>
          </Box>
        </Stack>
      </Paper>
    </Stack>
  );
}
