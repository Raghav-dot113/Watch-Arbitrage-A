"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  LinearProgress,
  MenuItem,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../components/shell/PageHeader";
import { PageContainer } from "../../../components/ui/PageContainer";
import {
  useCreateOrganization,
  type OrganizationCreateRequest,
} from "../../../lib/hooks/useOnboarding";
import {
  useUpdateOrganizationSettings,
  type OrganizationSettingsPatchRequest,
} from "../../../lib/hooks/useSettings";
import {
  useOrganizationSettings,
  type OrganizationSettingsResponse,
} from "../../../lib/hooks/useSettings";

const CURRENCY_OPTIONS = ["USD", "EUR", "GBP", "CAD", "AUD"];
const TIMEZONE_OPTIONS = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Shanghai",
];

const slugify = (name: string) =>
  name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

interface OnboardingFormData {
  name: string;
  slug: string;
  currency: string;
  timezone: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = React.useState<number>(0);
  const [form, setForm] = React.useState<OnboardingFormData>({
    name: "",
    slug: "",
    currency: "USD",
    timezone: "UTC",
  });
  const [submitting, setSubmitting] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  const createOrganization = useCreateOrganization();
  const updateSettings = useUpdateOrganizationSettings();
  const { data: settings } = useOrganizationSettings();

  const orgSettings: OrganizationSettingsResponse | undefined = settings;

  const isComplete = Boolean(orgSettings?.currency && orgSettings?.timezone);

  const handleNext = async () => {
    if (step === 0) {
      if (!form.name || !form.slug) return;
      setSubmitting(true);
      setError(null);
      try {
        await createOrganization.mutateAsync({
          name: form.name,
          slug: form.slug,
        });
        setStep(1);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to create organization",
        );
      } finally {
        setSubmitting(false);
      }
    } else if (step === 1) {
      setSubmitting(true);
      setError(null);
      try {
        const body: OrganizationSettingsPatchRequest = {
          currency: form.currency,
          timezone: form.timezone,
        };
        await updateSettings.mutateAsync(body);
        setStep(2);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to save organization settings",
        );
      } finally {
        setSubmitting(false);
      }
    } else {
      router.push("/opportunities");
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
      setError(null);
    }
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setForm({ ...form, name: value, slug: slugify(value) });
    setError(null);
  };

  const handleSlugChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, slug: e.target.value });
    setError(null);
  };

  const handleCurrencyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, currency: e.target.value });
    setError(null);
  };

  const handleTimezoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, timezone: e.target.value });
    setError(null);
  };

  return (
    <PageContainer>
      <PageHeader
        title="Set up your organization"
        description="Get started with ChronoArb in a few quick steps."
      />
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Stepper activeStep={step} sx={{ width: "100%" }}>
          {[
            { label: "Create organization" },
            { label: "Configure settings" },
            { label: "Complete" },
          ].map((stepLabel) => (
            <Step key={stepLabel.label}>
              <StepLabel>{stepLabel.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        {step === 0 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Organization Details
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: "background.paper",
                border: `1px solid`,
                borderColor: "divider",
                borderRadius: "md",
                display: "flex",
                flexDirection: "column",
                gap: 2,
              }}
            >
              <TextField
                required
                label="Organization name"
                fullWidth
                value={form.name}
                onChange={handleNameChange}
                helperText="Your dealership or company name"
              />
              <TextField
                required
                label="Organization slug"
                fullWidth
                value={form.slug}
                onChange={handleSlugChange}
                helperText="URL-friendly identifier (lowercase, hyphens only)"
              />
              {error && (
                <Typography variant="caption" color="error.main">
                  {error}
                </Typography>
              )}
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button
                  variant="outlined"
                  onClick={handleBack}
                  disabled={submitting || createOrganization.isPending}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={
                    !form.name ||
                    !form.slug ||
                    submitting ||
                    createOrganization.isPending
                  }
                >
                  {submitting || createOrganization.isPending
                    ? "Creating..."
                    : "Create organization"}
                </Button>
              </Box>
            </Box>
          </Box>
        )}
        {step === 1 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Organization Settings
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: "background.paper",
                border: `1px solid`,
                borderColor: "divider",
                borderRadius: "md",
                display: "flex",
                flexDirection: "column",
                gap: 2,
              }}
            >
              <TextField
                select
                label="Default currency"
                fullWidth
                value={form.currency}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleCurrencyChange(e)}
                helperText="Default currency for profit calculations"
              >
                {CURRENCY_OPTIONS.map((c) => (
                  <MenuItem key={c} value={c}>
                    {c}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Timezone"
                fullWidth
                value={form.timezone}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleTimezoneChange(e)}
                helperText="IANA timezone for date display"
              >
                {TIMEZONE_OPTIONS.map((tz) => (
                  <MenuItem key={tz} value={tz}>
                    {tz}
                  </MenuItem>
                ))}
              </TextField>
              {error && (
                <Typography variant="caption" color="error.main">
                  {error}
                </Typography>
              )}
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button
                  variant="outlined"
                  onClick={handleBack}
                  disabled={submitting || updateSettings.isPending}
                >
                  Back
                </Button>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={submitting || updateSettings.isPending}
                >
                  {submitting || updateSettings.isPending
                    ? "Saving..."
                    : "Complete setup"}
                </Button>
              </Box>
            </Box>
          </Box>
        )}
        {step === 2 && (
          <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 3, alignItems: "center", justifyContent: "center", minHeight: 400 }}>
            <CircularProgress size={64} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Setup complete
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
              Your organization is ready. Redirecting to opportunities feed...
            </Typography>
            <LinearProgress />
          </Box>
        )}
      </Box>
    </PageContainer>
  );
}
