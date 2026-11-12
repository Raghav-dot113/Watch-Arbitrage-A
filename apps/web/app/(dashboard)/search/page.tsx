"use client";

import { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Grid,
  IconButton,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import LaunchIcon from "@mui/icons-material/Launch";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import ClearIcon from "@mui/icons-material/Clear";
import Alert from "@mui/material/Alert";
import { PageContainer } from "../../../components/ui/PageContainer";
import { EmptyState } from "../../../components/ui/EmptyState";
import {
  useChannel3Search,
  type Channel3Product,
  type Channel3Offer,
  type Channel3Price,
  type Channel3SearchRequest,
} from "../../../lib/hooks";

interface SearchFormState {
  query: string;
  limit: number;
  condition: Channel3SearchRequest["condition"];
  in_stock_only: boolean;
}

const DEFAULT_CONDITION: Channel3SearchRequest["condition"] = "used";

function getConditionLabel(condition: string | null): string {
  if (condition === "used") return "Pre-owned";
  if (condition === "new") return "New";
  return "Unknown";
}

function getProductConditionLabel(product: Channel3Product): string {
  const conditions = new Set(product.offers.map((offer) => offer.condition));
  if (conditions.size === 0) return "Unknown";
  if (conditions.size > 1) return "Mixed";
  return getConditionLabel(conditions.values().next().value ?? null);
}

const PRESET_SEARCHES = [
  "Cartier Tank",
  "Rolex Submariner",
  "Omega Speedmaster",
  "Rolex Datejust",
  "Patek Philippe",
  "Audemars Piguet",
];

export default function SearchPage() {
  const [formState, setFormState] = useState<SearchFormState>({
    query: "",
    limit: 20,
    condition: DEFAULT_CONDITION,
    in_stock_only: false,
  });
  const [searchParams, setSearchParams] = useState<Channel3SearchRequest | null>(null);
  const [lastQuery, setLastQuery] = useState<string>("");

  const { data, isLoading, isError, error, refetch } = useChannel3Search(searchParams);

  const executeSearch = (queryText: string, limitNum = formState.limit) => {
    const trimmed = queryText.trim();
    if (trimmed.length < 2) return;
    setSearchParams({
      query: trimmed,
      limit: limitNum,
      condition: formState.condition,
      in_stock_only: formState.in_stock_only,
    });
    setLastQuery(trimmed);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    executeSearch(formState.query);
  };

  const handlePresetClick = (preset: string) => {
    setFormState((prev) => ({ ...prev, query: preset }));
    executeSearch(preset);
  };

  const handleClear = () => {
    setFormState({
      query: "",
      limit: 20,
      condition: DEFAULT_CONDITION,
      in_stock_only: false,
    });
    setSearchParams(null);
    setLastQuery("");
  };

  const formatPrice = (price: Channel3Price) => {
    const raw = price.amount ?? price.price;
    const num = typeof raw === "number" ? raw : parseFloat(String(raw || "0"));
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: price.currency || "USD",
      maximumFractionDigits: 0,
    }).format(isNaN(num) ? 0 : num);
  };

  const getMainImage = (product: Channel3Product): string | null => {
    const mainImage = product.images.find((img) => img.is_main_image);
    return mainImage?.url ?? product.images[0]?.url ?? null;
  };

  const getBestOffer = (product: Channel3Product): Channel3Offer | null => {
    if (!product.offers || product.offers.length === 0) return null;
    return product.offers.reduce((best, offer) => {
      const bestRaw = best.price.amount ?? best.price.price;
      const offerRaw = offer.price.amount ?? offer.price.price;
      const bestPrice = typeof bestRaw === "number" ? bestRaw : parseFloat(String(bestRaw || "0"));
      const offerPrice = typeof offerRaw === "number" ? offerRaw : parseFloat(String(offerRaw || "0"));
      return offerPrice < bestPrice ? offer : best;
    });
  };

  const products = data?.products ?? [];

  return (
    <PageContainer>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
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
          Watch Search
        </Typography>
        <Typography variant="body2" sx={{ color: "#64748B", fontSize: "0.9375rem" }}>
          Live multi-marketplace search across retailers with real-time pricing intelligence.
        </Typography>
      </Box>

      {/* Search Bar Card */}
      <Card
        variant="outlined"
        sx={{
          mb: 4,
          borderRadius: "16px",
          bgcolor: "#FFFFFF",
          borderColor: "#E2E8F0",
          boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
              <TextField
                placeholder="Search watches (e.g., Cartier Tank, Rolex Submariner)..."
                value={formState.query}
                onChange={(e) => setFormState({ ...formState, query: e.target.value })}
                fullWidth
                size="medium"
                slotProps={{
                  input: {
                    startAdornment: <SearchIcon sx={{ color: "#94A3B8", mr: 1 }} />,
                    endAdornment: formState.query ? (
                      <IconButton size="small" onClick={() => setFormState({ ...formState, query: "" })}>
                        <ClearIcon fontSize="small" />
                      </IconButton>
                    ) : null,
                  },
                }}
                sx={{
                  flex: 1,
                  minWidth: { xs: "100%", sm: 320 },
                  "& .MuiOutlinedInput-root": {
                    borderRadius: "12px",
                    bgcolor: "#F8FAFC",
                    "&:hover": { bgcolor: "#FFFFFF" },
                  },
                }}
              />

              <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                <ToggleButtonGroup
                  exclusive
                  size="small"
                  value={formState.condition}
                  aria-label="Condition"
                  onChange={(_, condition: SearchFormState["condition"] | null) => {
                    if (condition) {
                      setFormState((current) => ({ ...current, condition }));
                    }
                  }}
                >
                  <ToggleButton value="used">Pre-owned</ToggleButton>
                  <ToggleButton value="new">New</ToggleButton>
                  <ToggleButton value="all">All</ToggleButton>
                </ToggleButtonGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formState.in_stock_only}
                      onChange={(event) =>
                        setFormState((current) => ({
                          ...current,
                          in_stock_only: event.target.checked,
                        }))
                      }
                    />
                  }
                  label="In stock only"
                />
              </Box>

              <TextField
                type="number"
                label="Limit"
                value={formState.limit}
                onChange={(e) => setFormState({ ...formState, limit: parseInt(e.target.value) || 20 })}
                size="medium"
                sx={{
                  width: { xs: "100%", sm: 110 },
                  "& .MuiOutlinedInput-root": {
                    borderRadius: "12px",
                  },
                }}
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isLoading || formState.query.trim().length < 2}
                startIcon={isLoading ? <CircularProgress size={18} color="inherit" /> : <SearchIcon />}
                sx={{
                  bgcolor: "#0F172A",
                  color: "#FFFFFF",
                  fontWeight: 700,
                  px: 3,
                  py: 1.4,
                  borderRadius: "12px",
                  "&:hover": { bgcolor: "#1E293B" },
                }}
              >
                {isLoading ? "Searching..." : "Search"}
              </Button>

              {lastQuery && (
                <Button
                  variant="outlined"
                  size="large"
                  onClick={handleClear}
                  sx={{
                    borderRadius: "12px",
                    borderColor: "#CBD5E1",
                    color: "#475569",
                    py: 1.4,
                    "&:hover": { borderColor: "#0F172A", bgcolor: "#F8FAFC" },
                  }}
                >
                  Clear
                </Button>
              )}
            </Box>
          </form>

          {/* Quick preset chips */}
          <Box sx={{ mt: 2.5, display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
            <Typography variant="caption" sx={{ color: "#64748B", fontWeight: 600, mr: 0.5 }}>
              Trending:
            </Typography>
            {PRESET_SEARCHES.map((preset) => (
              <Chip
                key={preset}
                label={preset}
                size="small"
                onClick={() => handlePresetClick(preset)}
                sx={{
                  bgcolor: "#F1F5F9",
                  color: "#334155",
                  fontWeight: 600,
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  borderRadius: "8px",
                  "&:hover": {
                    bgcolor: "#E2E8F0",
                    color: "#0F172A",
                  },
                }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Error notification without removing search bar */}
      {isError && (
        <Alert
          severity="error"
          sx={{ mb: 3, borderRadius: "12px" }}
          action={
            <Button color="inherit" size="small" onClick={() => refetch()}>
              Retry
            </Button>
          }
        >
          {error instanceof Error ? error.message : "Search temporarily failed. Please try again."}
        </Alert>
      )}

      {/* Loading Skeleton Indicator */}
      {isLoading && (
        <Box sx={{ py: 6, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
          <CircularProgress size={40} sx={{ color: "#0F172A" }} />
          <Typography variant="body2" sx={{ color: "#64748B", fontWeight: 500 }}>
            Scanning retail marketplaces for "{lastQuery}"...
          </Typography>
        </Box>
      )}

      {!isLoading && !isError && searchParams && (data?.filtered_out_count ?? 0) > 0 && (
        <Typography variant="caption" sx={{ color: "#64748B", display: "block", mb: 1 }}>
          {data?.filtered_out_count} offer{data?.filtered_out_count !== 1 ? "s" : ""} hidden by the active filters.
        </Typography>
      )}

      {/* Empty State */}
      {!isLoading && !isError && products.length === 0 && searchParams && (
        <EmptyState
          title="No watches found"
          description={
            searchParams.condition === "all"
              ? `No results for "${lastQuery}" across all conditions. Try a different keyword like "Cartier Tank" or "Rolex".`
              : `No ${searchParams.condition === "used" ? "pre-owned" : "new"} results for "${lastQuery}". Try a different keyword like "Cartier Tank" or "Rolex".`
          }
        />
      )}

      {/* Products Grid */}
      {!isLoading && products.length > 0 && (
        <Box>
          <Box sx={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", mb: 2.5 }}>
            <Typography variant="h6" sx={{ fontWeight: 800, color: "#0F172A", fontSize: "1.125rem" }}>
              Search Results
            </Typography>
            <Typography variant="body2" sx={{ color: "#64748B" }}>
              Found {products.length} watch{products.length !== 1 ? "es" : ""} for "{lastQuery}"
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {products.map((product: Channel3Product) => (
              <Grid size={{ xs: 12, sm: 6, lg: 4, xl: 3 }} key={product.id}>
                <ProductCard
                  product={product}
                  getMainImage={getMainImage}
                  getBestOffer={getBestOffer}
                  formatPrice={formatPrice}
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </PageContainer>
  );
}

function ProductCard({
  product,
  getMainImage,
  getBestOffer,
  formatPrice,
}: {
  product: Channel3Product;
  getMainImage: (p: Channel3Product) => string | null;
  getBestOffer: (p: Channel3Product) => Channel3Offer | null;
  formatPrice: (price: Channel3Price) => string;
}) {
  const image = getMainImage(product);
  const bestOffer = getBestOffer(product);
  const brandName = product.brands[0]?.name ?? "Watch";

  const domain = bestOffer?.domain || "Retailer";
  const domainBadge = domain.replace(/^www\./, "").toUpperCase();

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
      {/* Watch Image Box with Overlays */}
      <Box
        sx={{
          position: "relative",
          width: "100%",
          height: 220,
          bgcolor: "#F8FAFC",
          overflow: "hidden",
        }}
      >
        {image ? (
          <Box
            component="img"
            src={image}
            alt={product.title}
            sx={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              p: 2,
              transition: "transform 0.3s ease",
              "&:hover": {
                transform: "scale(1.05)",
              },
            }}
          />
        ) : (
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
            <Typography variant="body2" sx={{ color: "#94A3B8" }}>
              No image available
            </Typography>
          </Box>
        )}

        {/* Top-Left: Retailer/Marketplace Badge */}
        <Box
          sx={{
            position: "absolute",
            top: 12,
            left: 12,
            px: 1.25,
            py: 0.4,
            borderRadius: "6px",
            bgcolor: "#0F172A",
            color: "#FFFFFF",
            fontSize: "0.6875rem",
            fontWeight: 800,
            letterSpacing: "0.06em",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
          }}
        >
          {domainBadge}
        </Box>

        {/* Top-Right: Brand Pill */}
        <Box
          sx={{
            position: "absolute",
            top: 12,
            right: 12,
            px: 1.25,
            py: 0.4,
            borderRadius: "6px",
            bgcolor: "rgba(255, 255, 255, 0.9)",
            color: "#0F172A",
            fontSize: "0.6875rem",
            fontWeight: 700,
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        >
          {brandName}
        </Box>
      </Box>

      {/* Content Area */}
      <CardContent sx={{ p: 2.5, flex: 1, display: "flex", flexDirection: "column" }}>
        {/* Title */}
        <Typography
          variant="h6"
          component="h3"
          sx={{
            fontWeight: 700,
            color: "#0F172A",
            fontSize: "1rem",
            lineHeight: 1.35,
            mb: 1,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {product.title}
        </Typography>

        <Chip
          label={getProductConditionLabel(product)}
          size="small"
          variant="outlined"
          aria-label={`Product condition: ${getProductConditionLabel(product)}`}
          sx={{ alignSelf: "flex-start", mb: 1.5 }}
        />

        {/* Description snippet */}
        {product.description && (
          <Typography
            variant="body2"
            sx={{
              color: "#64748B",
              fontSize: "0.8125rem",
              lineHeight: 1.4,
              mb: 2,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {product.description}
          </Typography>
        )}

        {product.offers.length > 0 && (
          <Box role="list" aria-label="Offers" sx={{ display: "grid", gap: 0.75, mb: 2 }}>
            {product.offers.map((offer) => (
              <Box
                role="listitem"
                key={offer.url}
                sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 0 }}
              >
                <Typography variant="caption" sx={{ color: "#64748B", flex: 1 }} noWrap>
                  {offer.domain}
                </Typography>
                <Chip
                  label={getConditionLabel(offer.condition)}
                  size="small"
                  variant="outlined"
                  aria-label={`${getConditionLabel(offer.condition)} offer condition`}
                />
              </Box>
            ))}
          </Box>
        )}

        {/* Price Row */}
        {bestOffer && (
          <Box sx={{ display: "flex", alignItems: "baseline", gap: 1, mb: 2, mt: "auto" }}>
            <Typography
              sx={{
                fontWeight: 800,
                color: "#0F172A",
                fontSize: "1.375rem",
                lineHeight: 1,
              }}
            >
              {formatPrice(bestOffer.price)}
            </Typography>
            <Typography variant="caption" sx={{ color: "#16A34A", fontWeight: 700 }}>
              Live Price
            </Typography>
          </Box>
        )}

        {/* Actions Row */}
        <Box sx={{ display: "flex", gap: 1, mt: bestOffer ? 0 : "auto" }}>
          {bestOffer && (
            <Button
              variant="contained"
              size="small"
              fullWidth
              href={bestOffer.url}
              target="_blank"
              rel="noopener noreferrer"
              endIcon={<LaunchIcon fontSize="small" />}
              sx={{
                bgcolor: "#0F172A",
                color: "#FFFFFF",
                fontWeight: 700,
                borderRadius: "10px",
                fontSize: "0.8125rem",
                py: 0.75,
                textTransform: "none",
                "&:hover": { bgcolor: "#1E293B" },
              }}
            >
              View Offer
            </Button>
          )}
          <Button
            variant="outlined"
            size="small"
            startIcon={<FavoriteBorderIcon fontSize="small" />}
            sx={{
              minWidth: 44,
              px: 1.5,
              borderRadius: "10px",
              borderColor: "#CBD5E1",
              color: "#475569",
              "&:hover": { borderColor: "#0F172A", bgcolor: "#F8FAFC" },
            }}
            aria-label="Add to watchlist"
          >
            Watch
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}
