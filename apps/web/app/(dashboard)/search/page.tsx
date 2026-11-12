"use client";

import { useState } from "react";
import { Box, Button, Card, CardContent, Grid, TextField, Typography, Chip, IconButton } from "@mui/material";
import { Search as SearchIcon, Launch as LaunchIcon, Favorite as FavoriteIcon } from "@mui/icons-material";
import { PageContainer } from "../../../components/ui/PageContainer";
import { PageHeader } from "../../../components/shell/PageHeader";
import { LoadingState } from "../../../components/ui/LoadingState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { EmptyState } from "../../../components/ui/EmptyState";
import { useChannel3Search, type Channel3Product, type Channel3Offer, type Channel3Price, type Channel3SearchRequest } from "../../../lib/hooks";

interface SearchFormState {
  query: string;
  limit: number;
}

export default function SearchPage() {
  const [formState, setFormState] = useState<SearchFormState>({ query: "", limit: 20 });
  const [searchParams, setSearchParams] = useState<Channel3SearchRequest | null>(null);
  const [lastQuery, setLastQuery] = useState<string>("");

  const { data, isLoading, isError, error, refetch } = useChannel3Search(searchParams);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (formState.query.trim().length < 2) return;
    const params: Channel3SearchRequest = {
      query: formState.query.trim(),
      limit: formState.limit,
    };
    setSearchParams(params);
    setLastQuery(formState.query.trim());
  };

  const handleClear = () => {
    setFormState({ query: "", limit: 20 });
    setSearchParams(null);
    setLastQuery("");
  };

  const formatPrice = (price: Channel3Price) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: price.currency,
    }).format(parseFloat(price.amount));
  };

  const getMainImage = (product: Channel3Product): string | null => {
    const mainImage = product.images.find((img) => img.is_main_image);
    return mainImage?.url ?? product.images[0]?.url ?? null;
  };

  const getBestOffer = (product: Channel3Product): Channel3Offer | null => {
    if (product.offers.length === 0) return null;
    return product.offers.reduce((best, offer) => {
      const bestPrice = parseFloat(best.price.amount);
      const offerPrice = parseFloat(offer.price.amount);
      return offerPrice < bestPrice ? offer : best;
    });
  };

  if (isLoading && !data) {
    return (
      <PageContainer>
        <LoadingState label="Searching watches" fullPage />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Search failed"
          description={error instanceof Error ? error.message : "An unexpected error occurred."}
          retryLabel="Try again"
          onRetry={() => refetch()}
        />
      </PageContainer>
    );
  }

  const products = data?.products ?? [];

  return (
    <PageContainer>
      <PageHeader
        title="Watch Search"
        description="Search the Channel3 catalog for watches across multiple retailers."
      />

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "flex-end" }}>
              <TextField
                label="Search watches"
                placeholder="e.g., Rolex Submariner, Omega Speedmaster"
                value={formState.query}
                onChange={(e) => setFormState({ ...formState, query: e.target.value })}
                fullWidth
                sx={{ flex: 1, minWidth: 300 }}
              />
              <TextField
                type="number"
                label="Results limit"
                value={formState.limit}
                onChange={(e) => setFormState({ ...formState, limit: parseInt(e.target.value) || 20 })}
                sx={{ minWidth: 160 }}
              />
              <Button type="submit" variant="contained" size="large" startIcon={<SearchIcon />}>
                Search
              </Button>
              {lastQuery && (
                <Button variant="outlined" onClick={handleClear} startIcon={<SearchIcon fontSize="small" />}>
                  Clear
                </Button>
              )}
            </Box>
          </form>
        </CardContent>
      </Card>

      {products.length === 0 && searchParams && !isLoading ? (
        <EmptyState
          title="No watches found"
          description={`No results found for "${lastQuery}". Try a different search term.`}
        />
      ) : products.length > 0 ? (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, display: "block" }}>
            Found {products.length} watch{products.length !== 1 ? "es" : ""} for "{lastQuery}"
          </Typography>
          <Grid container spacing={3}>
            {products.map((product: Channel3Product) => (
              <Grid size={{ xs: 12, sm: 6, lg: 4, xl: 3 }} key={product.id}>
                <ProductCard product={product} getMainImage={getMainImage} getBestOffer={getBestOffer} formatPrice={formatPrice} />
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
            <Typography variant="h6" color="primary" sx={{ fontWeight: 700 }}>
              {formatPrice(bestOffer.price)}
            </Typography>
            <Chip
              label={bestOffer.domain}
              size="small"
              variant="outlined"
              color="default"
            />
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
          <Button
            variant="outlined"
            size="small"
            fullWidth
            startIcon={<FavoriteIcon fontSize="small" />}
          >
            Watch
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}