"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../AuthProvider";
import {
  Alert,
  Box,
  Button,
  Paper,
  TextField,
  Typography,
} from "@mui/material";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/opportunities";
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const formData = new FormData(event.currentTarget);
      const email = (formData.get("email") as string) ?? "";
      await login(email);
      router.push(callbackUrl);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box
      component="main"
      sx={{
        minHeight: "100dvh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
      }}
    >
      <Paper
        sx={{
          p: 4,
          maxWidth: 400,
          width: "100%",
          bgcolor: "background.paper",
          borderColor: "divider",
        }}
        elevation={0}
      >
        <Typography variant="h6" component="h2" sx={{ mb: 3, fontWeight: 700 }}>
          Sign in to ChronoArb
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <form onSubmit={handleSubmit}>
            <TextField
              label="Email"
              name="email"
              type="email"
              required
              autoComplete="email"
              fullWidth
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={isLoading || submitting}
            >
              {isLoading || submitting ? "Signing in..." : "Continue"}
            </Button>
          </form>
        </Box>
      </Paper>
    </Box>
  );
}
