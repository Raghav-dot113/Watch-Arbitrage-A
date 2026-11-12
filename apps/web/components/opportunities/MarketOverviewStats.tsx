"use client";

import { Box, Card, CardContent, Grid, Typography } from "@mui/material";
import WatchOutlinedIcon from "@mui/icons-material/WatchOutlined";
import TrackChangesOutlinedIcon from "@mui/icons-material/TrackChangesOutlined";
import AttachMoneyOutlinedIcon from "@mui/icons-material/AttachMoneyOutlined";

interface MarketOverviewStatsProps {
  activeMonitoredCount?: number;
  opportunitiesCount?: number;
  averagePrice?: string;
  priceTrend?: string;
}

export function MarketOverviewStats({
  activeMonitoredCount = 12,
  opportunitiesCount = 5,
  averagePrice = "$8,240",
  priceTrend = "-1.2%",
}: MarketOverviewStatsProps) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography
        variant="h4"
        component="h1"
        sx={{
          fontWeight: 800,
          color: "#0F172A",
          fontSize: { xs: "1.5rem", md: "1.875rem" },
          letterSpacing: "-0.02em",
          mb: 0.5,
        }}
      >
        Market Overview
      </Typography>
      <Typography
        variant="body2"
        sx={{
          color: "#64748B",
          fontSize: "0.9375rem",
          mb: 3,
        }}
      >
        Real-time intelligence across 3 marketplaces
      </Typography>

      <Grid container spacing={3}>
        {/* Card 1: Active Monitored */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card
            variant="outlined"
            sx={{
              p: 2.5,
              borderRadius: "16px",
              bgcolor: "#FFFFFF",
              borderColor: "#E2E8F0",
              boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
              transition: "transform 0.15s ease, box-shadow 0.15s ease",
              "&:hover": {
                boxShadow: "0 4px 12px 0 rgba(0, 0, 0, 0.06)",
                transform: "translateY(-1px)",
              },
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  color: "#475569",
                  fontWeight: 600,
                  fontSize: "0.875rem",
                }}
              >
                Active Monitored
              </Typography>
              <Box
                sx={{
                  width: 38,
                  height: 38,
                  borderRadius: "10px",
                  bgcolor: "#F1F5F9",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#334155",
                }}
              >
                <WatchOutlinedIcon fontSize="small" />
              </Box>
            </Box>
            <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  color: "#0F172A",
                  fontSize: "2rem",
                  lineHeight: 1,
                }}
              >
                {activeMonitoredCount}
              </Typography>
              <Box
                sx={{
                  display: "inline-flex",
                  alignItems: "center",
                  px: 1.25,
                  py: 0.35,
                  borderRadius: "9999px",
                  bgcolor: "#DCFCE7",
                  color: "#15803D",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                +2 new
              </Box>
            </Box>
          </Card>
        </Grid>

        {/* Card 2: Market Opportunities */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card
            variant="outlined"
            sx={{
              p: 2.5,
              borderRadius: "16px",
              bgcolor: "#FFFFFF",
              borderColor: "#E2E8F0",
              boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
              transition: "transform 0.15s ease, box-shadow 0.15s ease",
              "&:hover": {
                boxShadow: "0 4px 12px 0 rgba(0, 0, 0, 0.06)",
                transform: "translateY(-1px)",
              },
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  color: "#475569",
                  fontWeight: 600,
                  fontSize: "0.875rem",
                }}
              >
                Market Opportunities
              </Typography>
              <Box
                sx={{
                  width: 38,
                  height: 38,
                  borderRadius: "10px",
                  bgcolor: "#F1F5F9",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#334155",
                }}
              >
                <TrackChangesOutlinedIcon fontSize="small" />
              </Box>
            </Box>
            <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  color: "#0F172A",
                  fontSize: "2rem",
                  lineHeight: 1,
                }}
              >
                {opportunitiesCount}
              </Typography>
              <Box
                sx={{
                  display: "inline-flex",
                  alignItems: "center",
                  px: 1.25,
                  py: 0.35,
                  borderRadius: "9999px",
                  bgcolor: "#D1FAE5",
                  color: "#047857",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                High Value
              </Box>
            </Box>
          </Card>
        </Grid>

        {/* Card 3: Avg. Market Price */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card
            variant="outlined"
            sx={{
              p: 2.5,
              borderRadius: "16px",
              bgcolor: "#FFFFFF",
              borderColor: "#E2E8F0",
              boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
              transition: "transform 0.15s ease, box-shadow 0.15s ease",
              "&:hover": {
                boxShadow: "0 4px 12px 0 rgba(0, 0, 0, 0.06)",
                transform: "translateY(-1px)",
              },
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  color: "#475569",
                  fontWeight: 600,
                  fontSize: "0.875rem",
                }}
              >
                Avg. Market Price
              </Typography>
              <Box
                sx={{
                  width: 38,
                  height: 38,
                  borderRadius: "10px",
                  bgcolor: "#F1F5F9",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#334155",
                }}
              >
                <AttachMoneyOutlinedIcon fontSize="small" />
              </Box>
            </Box>
            <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  color: "#0F172A",
                  fontSize: "2rem",
                  lineHeight: 1,
                }}
              >
                {averagePrice}
              </Typography>
              <Box
                sx={{
                  display: "inline-flex",
                  alignItems: "center",
                  px: 1.25,
                  py: 0.35,
                  borderRadius: "9999px",
                  bgcolor: "#FFE4E6",
                  color: "#E11D48",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                {priceTrend}
              </Box>
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
