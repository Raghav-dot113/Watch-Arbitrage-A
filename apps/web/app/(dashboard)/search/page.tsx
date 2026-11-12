"use client";

import { useState, type FormEvent } from "react";
import { HttpError } from "@chronoarb/api-client";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  Search as SearchIcon,
  Launch as LaunchIcon,
  Favorite as FavoriteIcon,
} from "@mui/icons-material";
import { PageContainer } from "../../../components/ui/PageContainer";
import { PageHeader } from "../../../components/shell/PageHeader";
import { LoadingState } from "../../../components/ui/LoadingState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { EmptyState } from "../../../components/ui/EmptyState";
import {
  useChannel3Search,
  type Channel3Product,
  type Channel3Offer,
  type Channel3SearchRequest,
} from "../../../lib/hooks";
import { formatCurrency } from "../../../lib/formatters/currency";

const MIN_LIMIT = 1;
const MAX_LIMIT = 50;
const DEFAULT_LIMIT = 20;

interface SearchFormState {
  query: string;
  limit: number;
}

function clampLimit(value: number): number {
  return Math.min(MAX_LIMIT, Math.max(MIN_LIMIT, Math.trunc(value) || MIN_LIMIT));
}

function getNumericPrice(offer: Channel3Offer): number | null {
  const amount = offer.price?.amount.trim();
  if (!amount) return null;
  const numericPrice = Number(amount);
  return Number.isFinite(numericPrice) ? numericPrice : null;
}

function getBestOffer(product: Channel3Product): Channel3Offer | null {
  const pricedOffers = product.offers.flatMap((offer) => {
    const price = getNumericPrice(offer);
    return price === null ? [] : [{ offer, price }];
  });
  const inStockOffers = pricedOffers.filter(
    ({ offer }) => offer.availability === "InStock",
  );
  const candidates = inStockOffers.length > 0 ? inStockOffers : pricedOffers;
  if (candidates.length === 0) return null;

  return candidates.reduce((best, candidate) =>
    candidate.price < best.price ? candidate : best,
  ).offer;
}

function getSearchErrorMessage(error: unknown): string {
  if (error instanceof HttpError) {
    return `${error.error.message} (${error.error.code})`;
  }
  if (error instanceof Error) return error.message;
  return "Search failed. Please try again.";
}

export default function SearchPage() {
  const [formState, setFormState] = useState<SearchFormState>({
    query: "",
    limit: DEFAULT_LIMIT,
  });
  const [searchParams, setSearchParams] = useState<Channel3SearchRequest | null>(null);
  const [lastQuery, setLastQuery] = useState<string>("");
  const [queryError, setQueryError] = useState(false);

  const {
    data,
    isFetching,
    isError,
    error,
    refetch,
  } = useChannel3Search(searchParams);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = formState.query.trim();
    if (query.length < 2) {
      setQueryError(true);
      return;
    }

    setQueryError(false);
    const limit = clampLimit(formState.limit);
    const params: Channel3SearchRequest = {
      query,
      limit,
    };
    setFormState((current) => ({ ...current, limit }));
    setLastQuery(query);

    if (
      searchParams?.query === params.query &&
      searchParams.limit === params.limit &&
      searchParams.page_token === params.page_token
    ) {
      void refetch();
    } else {
      setSearchParams(params);
    }
  };

  const handleClear = () => {
    setFormState({ query: "", limit: DEFAULT_LIMIT });
    setSearchParams(null);
    setLastQuery("");
    setQueryError(false);
  };

  const getMainImage = (product: Channel3Product): string | null => {
    const mainImage = product.images.find((img) => img.is_main_image);
    return mainImage?.url ?? product.images[0]?.url ?? null;
  };

  const products = searchParams ? data?.products ?? [] : [];

  return (
    <PageContainer>
      <PageHeader
        title="Watch Search"
        description="Search the Channel3 catalog for watches across multiple retailers."
      />

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Box
              sx={{
                display: "flex",
                gap: 2,
                flexWrap: "wrap",
                alignItems: "flex-end",
              }}
            >
              <TextField
                label="Search watches"
                placeholder="e.g., Rolex Submariner, Omega Speedmaster"
                value={formState.query}
                onChange={(event) => {
                  setFormState((current) => ({
                    ...current,
                    query: event.target.value,
                  }));
                  setQueryError(false);
                }}
                fullWidth
                sx={{ flex: 1, minWidth: 300 }}
                error={queryError}
                helperText="Enter at least 2 characters."
              />
              <TextField
                type="number"
                label="Results limit"
                value={formState.limit}
                onChange={(event) =>
                  setFormState((current) => ({
                    ...current,
                    limit: Number(event.target.value),
                  }))
                }
                slotProps={{ htmlInput: { min: MIN_LIMIT, max: MAX_LIMIT } }}
                sx={{ minWidth: 160 }}
              />
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isFetching}
                startIcon={
                  isFetching ? (
                    <CircularProgress size={18} color="inherit" aria-label="Searching" />
                  ) : (
                    <SearchIcon />
                  )
                }
              >
                {isFetching ? "Searching..." : "Search"}
              </Button>
              {(lastQuery || formState.query) && (
                <Button
                  type="button"
                  variant="outlined"
                  onClick={handleClear}
                  startIcon={<SearchIcon fontSize="small" />}
                >
                  Clear
                </Button>
              )}
            </Box>
          </form>
        </CardContent>
      </Card>

      {isFetching && <LoadingState label="Searching watches" />}
      {isError && (
        <ErrorState
          title="Search failed"
          description={getSearchErrorMessage(error)}
          retryLabel="Try again"
          onRetry={() => void refetch()}
        />
      )}
      {!isFetching && !isError && products.length === 0 && searchParams ? (
        <EmptyState
          title="No watches found"
          description={`No results found for "${lastQuery}". Try a different search term.`}
        />
      ) : !isFetching && !isError && products.length > 0 ? (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, display: "block" }}>
            Found {products.length} watch{products.length !== 1 ? "es" : ""} for &quot;
            {lastQuery}&quot;
          </Typography>
          <Grid container spacing={3}>
            {products.map((product: Channel3Product) => (
              <Grid size={{ xs: 12, sm: 6, lg: 4, xl: 3 }} key={product.id}>
                <ProductCard product={product} getMainImage={getMainImage} />
              </Grid>
            ))}
          </Grid>
        </>
      ) : null}
    </PageContainer>
  );
}

function ProductCard({
  product,
  getMainImage,
}: {
  product: Channel3Product;
  getMainImage: (p: Channel3Product) => string | null;
}) {
  const image = getMainImage(product);
  const bestOffer = getBestOffer(product);
  const brandName = product.brands[0]?.name ?? "Unknown Brand";

  return (
    <Card variant="outlined" sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box
        component="div"
        sx={{
          aspectRatio: "1 / 1",
          position: "relative",
          overflow: "hidden",
          bgcolor: "grey.100",
        }}
      >
        {image ? (
          <img
            src={image}
            alt={product.title}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transition: "transform 0.2s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
            onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
          />
        ) : (
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
            <Typography color="text.disabled">No image</Typography>
          </Box>
        )}
        {product.brands.length > 0 && (
          <Chip
            label={brandName}
            size="small"
            sx={{
              position: "absolute",
              top: 8,
              left: 8,
              bgcolor: "background.paper",
              boxShadow: 1,
            }}
          />
        )}
      </Box>
      <CardContent sx={{ flex: 1, display: "flex", flexDirection: "column", p: 2 }}>
        <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600, lineHeight: 1.3 }}>
          {product.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {brandName}
        </Typography>
        {product.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {product.description}
          </Typography>
        )}
        {bestOffer && (
          <Box sx={{ mb: 2, display: "flex", alignItems: "baseline", gap: 1 }}>
            {bestOffer.price && (
              <Typography variant="h6" color="primary" sx={{ fontWeight: 700 }}>
                {formatCurrency(bestOffer.price.amount, bestOffer.price.currency)}
              </Typography>
            )}
            <Chip
              label={bestOffer.domain}
              size="small"
              variant="outlined"
              color="default"
            />
            {bestOffer.condition && (
              <Chip
                label={bestOffer.condition}
                size="small"
                variant="outlined"
              />
            )}
          </Box>
        )}
        <Box sx={{ mt: "auto", display: "flex", gap: 1 }}>
          {bestOffer && (
            <Button
              variant="contained"
              size="small"
              fullWidth
              href={bestOffer.url}
              target="_blank"
              rel="noopener noreferrer"
              startIcon={<LaunchIcon fontSize="small" />}
            >
              View Offer
            </Button>
          )}
          <Tooltip title="Coming soon">
            <span>
              <Button
                variant="outlined"
                size="small"
                fullWidth
                disabled
                startIcon={<FavoriteIcon fontSize="small" />}
              >
                Watch
              </Button>
            </span>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
}