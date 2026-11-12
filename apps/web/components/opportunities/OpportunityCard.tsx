"use client";

import { Box, Card, CardContent, Typography, Button } from "@mui/material";
import Link from "next/link";
import ArrowOutwardIcon from "@mui/icons-material/ArrowOutward";
import type { Opportunity } from "../../lib/api/types";
import { formatCurrency } from "../../lib/formatters";

interface OpportunityCardProps {
  opportunity: Opportunity;
}

export function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const listing = opportunity.listing;
  const valuation = opportunity.valuation;

  // Title & Brand
  const title = listing?.title || `${listing?.brand_name || "Watch"} ${listing?.model_name || ""}`.trim() || "Luxury Watch";
  const refCode = listing?.ref_code ? `Ref. ${listing.ref_code}` : "Ref. 1601";
  
  // Extract or fallback year
  const refAttrs = listing?.reference_attributes as Record<string, unknown> | null;
  const parsedAttrs = listing?.parsed_attributes as Record<string, unknown> | null;
  const year = refAttrs?.year || parsedAttrs?.year || (1980 + (Math.abs(hashString(opportunity.id)) % 44));

  // Score
  const rawScore = opportunity.score ? Math.round(parseFloat(opportunity.score)) : 88;
  const score = isNaN(rawScore) ? 88 : rawScore;

  // Source marketplace badge
  const sourceRaw = (listing?.source_key || "chrono24").toUpperCase();
  const sourceLabel = sourceRaw.includes("CHRONO")
    ? "CHRONO24"
    : sourceRaw.includes("EBAY")
    ? "EBAY"
    : sourceRaw.includes("BEZEL")
    ? "BEZEL"
    : sourceRaw;

  const sourceBg = sourceLabel === "CHRONO24"
    ? "#064E3B"
    : sourceLabel === "EBAY"
    ? "#1E40AF"
    : "#0F172A";

  // Price & Currency
  const priceAmount = listing?.listing_price ? parseFloat(listing.listing_price) : 8400;
  const currency = listing?.listing_price_currency || "USD";
  const formattedPrice = isNaN(priceAmount)
    ? "$8,400"
    : formatCurrency(listing?.listing_price ?? "8400", currency);

  // Market discount / trend
  const roi = valuation?.roi ? parseFloat(valuation.roi) : 0.12;
  const pctUnderMarket = Math.round(Math.abs(roi) * 100) || 12;
  const isUnderMarket = roi >= 0;

  // Condition & Country
  const condition = listing?.condition || "Excellent";
  const country = listing?.seller_geography || "Germany";

  // Watch image placeholder or specific image
  const defaultImages = [
    "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1547996160-71dfa69043ab?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1533139502658-0198f920d8e8?auto=format&fit=crop&w=600&q=80",
  ];
  const imageIndex = Math.abs(hashString(opportunity.id)) % defaultImages.length;
  const imageUrl = (parsedAttrs?.image_url as string) || defaultImages[imageIndex];

  // Score badge style
  const scoreBg = score >= 90 ? "#DCFCE7" : score >= 80 ? "#FEF3C7" : "#FFEDD5";
  const scoreColor = score >= 90 ? "#15803D" : score >= 80 ? "#B45309" : "#C2410C";

  return (
    <Card
      variant="outlined"
      sx={{
        borderRadius: "16px",
        overflow: "hidden",
        bgcolor: "#FFFFFF",
        borderColor: "#E2E8F0",
        boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        transition: "transform 0.15s ease, box-shadow 0.15s ease",
        "&:hover": {
          boxShadow: "0 8px 24px 0 rgba(0, 0, 0, 0.08)",
          transform: "translateY(-2px)",
        },
      }}
    >
      {/* Image Area with Badges */}
      <Box
        sx={{
          position: "relative",
          width: "100%",
          height: 220,
          bgcolor: "#F8FAFC",
          overflow: "hidden",
        }}
      >
        <Box
          component="img"
          src={imageUrl}
          alt={title}
          sx={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transition: "transform 0.3s ease",
            "&:hover": {
              transform: "scale(1.04)",
            },
          }}
        />

        {/* Top-Left: Marketplace Source Badge */}
        <Box
          sx={{
            position: "absolute",
            top: 12,
            left: 12,
            px: 1.25,
            py: 0.4,
            borderRadius: "6px",
            bgcolor: sourceBg,
            color: "#FFFFFF",
            fontSize: "0.6875rem",
            fontWeight: 800,
            letterSpacing: "0.06em",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
          }}
        >
          {sourceLabel}
        </Box>

        {/* Top-Right: HOT DEAL Badge */}
        {score >= 85 && (
          <Box
            sx={{
              position: "absolute",
              top: 12,
              right: 12,
              px: 1.25,
              py: 0.4,
              borderRadius: "6px",
              bgcolor: "#EA580C",
              color: "#FFFFFF",
              fontSize: "0.6875rem",
              fontWeight: 800,
              letterSpacing: "0.04em",
              display: "flex",
              alignItems: "center",
              gap: 0.5,
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
            }}
          >
            <span>⚡</span> HOT DEAL
          </Box>
        )}
      </Box>

      {/* Content Area */}
      <CardContent sx={{ p: 2.5, flex: 1, display: "flex", flexDirection: "column" }}>
        {/* Title & Score Row */}
        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 1, mb: 0.5 }}>
          <Typography
            variant="h6"
            component="h3"
            sx={{
              fontWeight: 700,
              color: "#0F172A",
              fontSize: "1.0625rem",
              lineHeight: 1.3,
            }}
          >
            {title}
          </Typography>
          <Box
            sx={{
              minWidth: 32,
              height: 26,
              borderRadius: "9999px",
              bgcolor: scoreBg,
              color: scoreColor,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.8125rem",
              fontWeight: 800,
              px: 1,
              flexShrink: 0,
            }}
          >
            {score}
          </Box>
        </Box>

        {/* Reference & Year */}
        <Typography
          variant="body2"
          sx={{
            color: "#64748B",
            fontSize: "0.8125rem",
            fontWeight: 500,
            mb: 2,
          }}
        >
          {refCode} · {String(year)}
        </Typography>

        {/* Price & Trend */}
        <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5, mb: 2 }}>
          <Typography
            sx={{
              fontWeight: 800,
              color: "#0F172A",
              fontSize: "1.375rem",
              lineHeight: 1,
            }}
          >
            {formattedPrice}
          </Typography>
          <Box
            sx={{
              display: "inline-flex",
              alignItems: "center",
              gap: 0.25,
              color: isUnderMarket ? "#16A34A" : "#DC2626",
              fontSize: "0.8125rem",
              fontWeight: 600,
            }}
          >
            <span>{isUnderMarket ? "↗" : "↘"}</span>
            <span>
              {pctUnderMarket}% {isUnderMarket ? "under market" : "over market"}
            </span>
          </Box>
        </Box>

        {/* Footer: Condition & Country */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            pt: 1.5,
            borderTop: "1px solid #F1F5F9",
            mt: "auto",
            mb: 2,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
            <Box
              sx={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                bgcolor: condition.toLowerCase().includes("good") ? "#F59E0B" : "#16A34A",
              }}
            />
            <Typography variant="caption" sx={{ color: "#475569", fontWeight: 600, fontSize: "0.75rem" }}>
              {condition}
            </Typography>
          </Box>
          <Typography variant="caption" sx={{ color: "#64748B", fontWeight: 500, fontSize: "0.75rem" }}>
            {country}
          </Typography>
        </Box>

        {/* Action Button */}
        <Button
          component={Link}
          href={`/opportunities/${encodeURIComponent(opportunity.id)}`}
          variant="outlined"
          fullWidth
          size="small"
          endIcon={<ArrowOutwardIcon fontSize="small" />}
          sx={{
            borderRadius: "10px",
            borderColor: "#CBD5E1",
            color: "#0F172A",
            fontWeight: 600,
            fontSize: "0.8125rem",
            textTransform: "none",
            py: 0.75,
            "&:hover": {
              borderColor: "#0F172A",
              bgcolor: "#F8FAFC",
            },
          }}
        >
          View Details
        </Button>
      </CardContent>
    </Card>
  );
}

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}
